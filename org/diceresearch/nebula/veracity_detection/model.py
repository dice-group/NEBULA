import logging
from typing import List, Optional, Callable

import torch
from tqdm import tqdm


class BaseWise:
    """
    Common behaviour between the NN used in NEBULA
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def train_model(self,
                    loss_function: Optional[Callable[..., torch.nn.Module]] = torch.nn.BCELoss,
                    optimizer: Optional[Callable[..., torch.optim.Optimizer]] = torch.optim.Adam,
                    epochs: int = 1,
                    lr: float = 0.001,
                    training_loader: torch.utils.data.DataLoader = None,
                    validation_loader: torch.utils.data.DataLoader = None):
        """
        Trains the model
        :param loss_function:       Loss function
        :param optimizer:           Optimizer
        :param epochs:              Number of epochs
        :param lr:                  Learning rate
        :param training_loader:     Training DataLoader
        :param validation_loader:   Validation DataLoader if we want to evaluate on the validation split at the end of
                                    each epoch.
        :return: Train and validation losses at the end of each epoch.
        """

        # turn gradient tracking on
        self.train(True)

        # instantiate chosen
        optimizer = optimizer(self.parameters(), lr=lr)
        loss_function = loss_function()
        logging.debug(loss_function)
        logging.debug(optimizer)

        train_losses = []
        val_losses = []
        for epoch in range(epochs):
            train_loss_sum = 0
            with tqdm(training_loader, unit="batch") as tepoch:  # show progress bar as we progress through batches
                n_batches_processed = 0
                for sample in tepoch:
                    tepoch.set_description(f"Epoch {epoch}")
                    inputs, labels = sample
                    inputs, labels = inputs.to(self.device), labels.to(self.device)  # pass to gpu (or not)

                    outputs = self(inputs)  # .reshape(-1)  # predict labels
                    loss = loss_function(outputs, labels.unsqueeze(-1))  # compute loss between predictions and actual
                    # loss = loss_function(outputs, labels) # classification
                    optimizer.zero_grad()  # set gradients to 0
                    loss.backward()  # backward pass
                    optimizer.step()  # optimize

                    # update progress bar with loss
                    train_loss_sum += loss.item()
                    n_batches_processed += 1
                    tepoch.set_postfix(loss=train_loss_sum / n_batches_processed)

                epoch_loss = train_loss_sum / len(training_loader)
                train_losses.append(epoch_loss)
                if epoch % 20 == 0:
                    logging.debug('Epoch {0} Training loss {1}'.format(epoch, epoch_loss))

                # evaluate on validation dataset if existing
                if validation_loader and epoch % 20 == 0:
                    self.train(False)
                    val_loss = 0
                    with torch.set_grad_enabled(False):
                        for x_val, y_val in tqdm(validation_loader):
                            x_val, y_val = x_val.to(self.device), y_val.to(self.device)
                            val_pred = self(x_val)
                            v_loss = loss_function(val_pred, y_val.unsqueeze(1))
                            val_loss += v_loss.item()
                        validation_loss = val_loss / len(validation_loader)
                        logging.debug('Epoch {0} Validation loss {1}'.format(epoch, validation_loss))

                        # early stopping
                        # if validation loss doesn't increase, stop
                        if len(val_losses) > 0 and validation_loss > val_losses[-1]:
                            logging.debug(f"Validation loss went up.")
                            # break
                        val_losses.append(validation_loss)

                    self.train(True)
        logging.debug('Last epoch training loss {0}'.format(epoch_loss))
        if validation_loader:
            logging.debug('Last epoch validation loss {0}'.format(validation_loss))
        # turn gradient tracking off
        self.train(False)
        return train_losses, val_losses

    def predict(self, test_loader):
        results = list()
        for sample in tqdm(test_loader):
            scores = sample[0]
            output = self(scores).reshape(-1).detach().numpy()
            sample.append(output)
            results.append(sample)
        return results


class MLP(torch.nn.Sequential, BaseWise):
    """
    Modified version of https://pytorch.org/vision/main/_modules/torchvision/ops/misc.html#MLP
    - Removed dropout from the output layer
    - Added initializer to weights and biases
    - Added different activation function to the output layer

    """

    def __init__(
            self,
            in_channels: int,
            hidden_channels: List[int],
            norm_layer: Optional[Callable[..., torch.nn.Module]] = None,
            init_weights: Callable[..., torch.tensor] = torch.nn.init.xavier_uniform_,
            init_bias: Callable[..., torch.tensor] = torch.nn.init.zeros_,
            activation_layer: Optional[Callable[..., torch.nn.Module]] = torch.nn.ReLU,
            activation_output: Optional[Callable[..., torch.nn.Module]] = None,
            inplace: Optional[bool] = None,
            bias: bool = True,
            dropout: float = 0.0,
    ):
        """
        Constructor.
        Creates a Multi-Layer Perceptron with repeating stacks of linear, normalization and dropout layers.
        :param in_channels:         Input layer size.
        :param hidden_channels:     List with sizes of hidden layers. The last index will be used as the output
                                    layer size.
        :param norm_layer:          Type of normalization needed
        :param init_weights:        Weight initializer
        :param init_bias:           Bias initializer
        :param activation_layer:    Activation function for the hidden layers
        :param activation_output:   Activation function for the output layer
        :param inplace:             Inplace operation
        :param bias:                True if bias in linear layers
        :param dropout:             Dropout probability
        """
        params = {} if inplace is None else {"inplace": inplace}

        layers = []
        in_dim = in_channels
        # stacks of linear - norm - activation - dropout
        for hidden_dim in hidden_channels[:-1]:
            l1 = torch.nn.Linear(in_dim, hidden_dim, bias=bias)
            init_weights(l1.weight)
            if bias:
                init_bias(l1.bias)
            layers.append(l1)
            if norm_layer is not None:
                layers.append(norm_layer(hidden_dim))
            layers.append(activation_layer(**params))
            layers.append(torch.nn.Dropout(dropout, **params))
            in_dim = hidden_dim

        # output layer setup
        output_layer = torch.nn.Linear(in_dim, hidden_channels[-1], bias=bias)
        init_weights(output_layer.weight)
        if bias:
            init_bias(output_layer.bias)
        layers.append(output_layer)
        if activation_output:
            layers.append(activation_output())
        super().__init__(*layers)
        BaseWise.__init__(self)

    def test_model(self, x_test):
        self.eval()
        with torch.no_grad():
            return self(x_test)


class WISE(torch.nn.Module, BaseWise):
    """
        Default RNN implementation followed by a linear and an output activation_output layer
    """

    def __init__(self, input_size, hidden_size, num_layers, nonlinearity, bias, batch_first, dropout, bidirectional,
                 output_size, activation_output: Optional[Callable[..., torch.nn.Module]] = None):
        """
        Constructor
        :param input_size: Input size
        :param hidden_size: Number of hidden features
        :param num_layers: Number of recurrent layers
        :param nonlinearity: Non-linearity function
        :param bias: Bias
        :param batch_first: if (batch, seq, feature) or (seq, batch, feature)
        :param dropout: Dropout rate
        :param bidirectional: Bidirectional
        :param output_size: Output neurons
        :param activation_output: Output activation function
        """
        super(WISE, self).__init__()
        BaseWise.__init__(self)  # Explicitly call the Base class initializer
        self.rnn = torch.nn.RNN(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers,
                                nonlinearity=nonlinearity, bias=bias, batch_first=batch_first, dropout=dropout,
                                bidirectional=bidirectional)
        self.fc = torch.nn.Linear(hidden_size, output_size)
        self.activation_output = activation_output

    def forward(self, x):
        """

        :param x: Network input
        :return: Network output
        """
        output, _ = self.rnn(x)
        output = self.fc(output[:, -1, :])  # on last step
        output = self.activation_output(output)
        return output

    def test_model(self, x_test):
        """
        Deactivates gradient tracking to predict

        :param x_test: Data to predict on
        :return: Prediction
        """
        self.eval()
        with torch.no_grad():
            return self(x_test)


class FocalLoss(torch.nn.Module):
    """
    Focal Loss implementation
    FL(p_t)=−(1−p_t)^γ⋅ \times log(p_t)
    """

    def __init__(self, gamma=2, alpha=None):
        super(FocalLoss, self).__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, inputs, targets):
        ce_loss = torch.nn.functional.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = (1 - pt) ** self.gamma * ce_loss

        if self.alpha is not None:
            focal_loss = self.alpha * focal_loss

        return focal_loss.mean()
