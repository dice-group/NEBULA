import logging
import unittest

import numpy as np
import torch

from veracity_detection.model import MLP

# FIXME create logging config file
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%d-%m-%Y %H:%M:%S')

# to ensure deterministic behaviour
seed = 1
np.random.seed(seed)
torch.manual_seed(seed)


class TestModel(unittest.TestCase):
    """
        Sanity Check of the models
    """

    def test_mlp(self):
        """
        Sample train run of the MLP
        :return:
        """
        x_train = np.random.randint(-1, 2, size=(5, 10)).astype(np.float32)  # dummy input
        y_train = np.random.randint(0, 2, size=(5, 1)).astype(np.float32)  # dummy labels

        # convert to data loader
        train_dataset = torch.utils.data.TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train))
        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=3, shuffle=True)

        input_size = np.shape(x_train)[1]  # input size will serve as input neurons size

        # create network with 1 input, 1 hidden and 1 output layer
        model = MLP(in_channels=input_size, hidden_channels=[2, 1],
                    init_weights=torch.nn.init.xavier_uniform_,
                    init_bias=torch.nn.init.zeros_,
                    norm_layer=torch.nn.BatchNorm1d,
                    activation_layer=torch.nn.ReLU,
                    activation_output=torch.nn.Sigmoid,
                    inplace=False, bias=True, dropout=0.5)
        logging.info(model)
        # Expect 6 layers
        # Linear(input) - BatchNorm - ReLu - Dropout - Linear - Sigmoid (output)
        self.assertEqual(sum(1 for _ in model.children()), 6)

        # train
        epochs = 1
        train_losses, val_losses = model.train_model(loss_function=torch.nn.BCELoss,
                                                     optimizer=torch.optim.Adam,
                                                     training_loader=train_loader,
                                                     epochs=epochs)
        self.assertEqual(len(train_losses), epochs)
        self.assertEqual(len(val_losses), 0)

        # predict
        x_test = np.random.randint(0, 2, size=(1, 10)).astype(np.float32)
        model.test_model(torch.from_numpy(x_test))

    def test_rnn(self):
        x_train = np.random.randint(0, 2, size=(5, 10)).astype(np.float32)  # dummy input
        y_train = np.random.randint(0, 2, size=(5, 1)).astype(np.float32)  # dummy labels

        input_size = np.shape(x_train)[1]
        rnn = torch.nn.RNN(input_size=input_size,
                           hidden_size=2, num_layers=1, nonlinearity='relu', bias=True,
                           batch_first=False, dropout=0.0, bidirectional=False)


if __name__ == '__main__':
    unittest.main()
