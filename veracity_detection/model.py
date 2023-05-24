from typing import List, Optional, Callable

import torch
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm


class MLP(torch.nn.Sequential):
    """
    Modified version of https://pytorch.org/vision/main/_modules/torchvision/ops/misc.html#MLP
    We removed the dropout applied to the output layer and added initializer to weights and biases.

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
        params = {} if inplace is None else {"inplace": inplace}

        layers = []
        in_dim = in_channels
        for hidden_dim in hidden_channels[:-1]:
            l1 = torch.nn.Linear(in_dim, hidden_dim, bias=bias)
            init_weights(l1.weight)
            init_bias(l1.bias)
            layers.append(l1)
            if norm_layer is not None:
                layers.append(norm_layer(hidden_dim))
            layers.append(activation_layer(**params))
            layers.append(torch.nn.Dropout(dropout, **params))
            in_dim = hidden_dim

        output_layer = torch.nn.Linear(in_dim, hidden_channels[-1], bias=bias)
        init_weights(output_layer.weight)
        init_bias(output_layer.bias)
        layers.append(output_layer)
        if activation_output:
            layers.append(activation_output())
        super().__init__(*layers)

    def train_model(self,
                    loss_function: Optional[Callable[..., torch.nn.Module]] = torch.nn.BCELoss,
                    optimizer: Optional[Callable[..., torch.optim.Optimizer]] = torch.optim.Adam,
                    epochs: int = 1,
                    lr: float = 0.001,
                    training_loader: torch.utils.data.DataLoader = None,
                    validation_loader: torch.utils.data.DataLoader = None):

        # turn gradient tracking on
        self.train(True)

        # instantiate chosen
        optimizer = optimizer(self.parameters(), lr=lr)
        loss_function = loss_function()
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")  # FIXME pass the decision to user

        train_losses = []
        val_losses = []
        for epoch in range(epochs):
            train_loss_sum = 0
            with tqdm(training_loader, unit="batch") as tepoch:  # show progress bar as we progress through batches
                for inputs, labels in tepoch:
                    tepoch.set_description(f"Epoch {epoch}")
                    inputs, labels = inputs.to(device), labels.to(device)  # pass to gpu (or not)
                    optimizer.zero_grad()  # set gradients to 0
                    outputs = self(inputs)  # predict labels
                    loss = loss_function(outputs, labels)  # compute loss between predictions and actual
                    loss.backward()  # backward pass
                    optimizer.step()  # optimize

                    # update progress bar with loss
                    train_loss_sum += loss.item()
                    tepoch.set_postfix(loss=loss.item())

                train_losses.append(train_loss_sum / len(training_loader))

                # evaluate on validation dataset if existing
                if validation_loader:
                    val_loss = 0
                    with torch.set_grad_enabled(False):
                        for x_val, y_val in validation_loader:
                            x_val, y_val = x_val.to(device), y_val.to(device)
                            val_pred = self(x_val)
                            v_loss = loss_function(val_pred, y_val)
                            val_loss += v_loss.item()
                        val_losses.append(val_loss / len(validation_loader))

        # turn gradient tracking off
        self.train(False)
        return train_losses, val_losses

    def test_model(self, x_test: torch.Tensor = None):
        self.eval()
        with torch.no_grad():
            return self(x_test)