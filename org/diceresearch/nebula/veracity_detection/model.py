import logging
from typing import List, Optional, Callable

import torch
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm


class MLP(torch.nn.Sequential):
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
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        super().__init__(*layers)

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
                    inputs = sample['scores']
                    labels = sample['labels']
                    inputs, labels = inputs.to(self.device), labels.to(self.device)  # pass to gpu (or not)
                    optimizer.zero_grad()  # set gradients to 0
                    outputs = self(inputs) #.reshape(-1)  # predict labels
                    loss = loss_function(outputs, labels)  # compute loss between predictions and actual
                    loss.backward()  # backward pass
                    optimizer.step()  # optimize

                    # update progress bar with loss
                    train_loss_sum += loss.item()
                    n_batches_processed += 1
                    tepoch.set_postfix(loss=train_loss_sum / n_batches_processed)

                epoch_loss = train_loss_sum / len(training_loader)
                train_losses.append(epoch_loss)
                if epoch%20==0:
                    logging.debug('Epoch {0} Training loss {1}'.format(epoch, epoch_loss))

                # evaluate on validation dataset if existing
                if validation_loader:
                    val_loss = 0
                    with torch.set_grad_enabled(False):
                        for x_val, y_val in validation_loader:
                            x_val, y_val = x_val.to(self.device), y_val.to(self.device)
                            val_pred = self(x_val)
                            v_loss = loss_function(val_pred, y_val)
                            val_loss += v_loss.item()
                        val_losses.append(val_loss / len(validation_loader))
        logging.debug('Last epoch training loss {0}'.format(epoch_loss))
        # turn gradient tracking off
        self.train(False)
        return train_losses, val_losses

    def test_model(self, x_test):
        self.eval()
        with torch.no_grad():
            return self(x_test)

    def predict(self, test_loader):
        results = list()
        for sample in tqdm(test_loader):
            scores = sample['scores']
            output = self(scores).reshape(-1).detach().numpy()
            sample['predicted_label'] = output
            results.append(sample)
        return results

class FocalLoss(torch.nn.Module):
    def __init__(self, gamma=2, alpha=None):
        super(FocalLoss, self).__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, inputs, targets):
        ce_loss = torch.nn.functional.binary_cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = (1 - pt) ** self.gamma * ce_loss

        if self.alpha is not None:
            focal_loss = self.alpha * focal_loss

        return focal_loss.mean()