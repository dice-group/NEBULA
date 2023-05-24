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
        train_loss = 0.0

        # iterate epochs
        for epoch in range(epochs):
            with tqdm(training_loader, unit="batch") as tepoch:  # show progress bar
                for inputs, labels in tepoch:
                    tepoch.set_description(f"Epoch {epoch}")
                    optimizer.zero_grad()  # set gradients to 0
                    outputs = self(inputs)  # predict labels
                    loss = loss_function(outputs, labels)  # compute loss between predictions and actual
                    loss.backward()  # backward pass
                    optimizer.step()  # optimize

                    # Add loss
                    train_loss = loss.item()/len(training_loader.sampler)
                    tepoch.set_postfix(loss=train_loss)
                    # sleep(0.1)

                if validation_loader:
                    # TODO evaluate on validation split
                    pass

        # turn gradient tracking off
        self.train(False)
        return loss

    def test_model(self, x_test: torch.Tensor = None):
        self.eval()
        with torch.no_grad():
            return self(x_test)