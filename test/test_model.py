import logging
import random
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
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed(seed)
torch.backends.cudnn.deterministic = True


class TestMLP(unittest.TestCase):
    """
        Sanity Check of the MLP
    """

    def test(self):
        """
        Test if MLP object is created right
        :return:
        """
        model = MLP(in_channels=4, hidden_channels=[2, 1],
                    init_weights=torch.nn.init.xavier_uniform_,
                    init_bias=torch.nn.init.zeros_,
                    norm_layer=torch.nn.BatchNorm1d,
                    activation_layer=torch.nn.ReLU,
                    activation_output=torch.nn.Sigmoid,
                    inplace=False, bias=True, dropout=0.5)
        logging.info(model)
        # Expected
        # Linear (Input) - BatchNorm - ReLU - Dropout - Linear - Sigmoid (Output)
        self.assertEqual(sum(1 for _ in model.children()), 6)

    def test_train(self):
        """
        Sample train run for 1 epoch
        :return:
        """
        x_scl = np.random.randint(-1, 1, size=(5, 5)).astype(np.float32)  # input from stance classification
        x_kgcl = np.random.randint(-1, 1, size=(5, 5)).astype(np.float32)  # input from kg based classification
        y_train = np.random.randint(-1, 1, size=(5, 1)).astype(np.float32)  # dummy labels
        x_train = np.hstack((x_scl, x_kgcl))  # concatenate inputs

        # convert to data loader
        train_dataset = torch.utils.data.TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train))
        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=5, shuffle=True)

        input_size = np.shape(x_train)[1]  # input size will serve as input neurons size

        # create network with 1 input, 1 hidden and 1 output layer
        model = MLP(in_channels=input_size, hidden_channels=[2, 1],
                    init_weights=torch.nn.init.xavier_uniform_,
                    init_bias=torch.nn.init.zeros_,
                    norm_layer=torch.nn.BatchNorm1d,
                    activation_layer=torch.nn.ReLU,
                    activation_output=torch.nn.Sigmoid,
                    inplace=False, bias=True, dropout=0.5)

        # train
        model.train_model(loss_function=torch.nn.BCELoss,
                          optimizer=torch.optim.Adam,
                          training_loader=train_loader,
                          epochs=1)

        # predict
        x_test = np.random.randint(-1, 1, size=(1, 10)).astype(np.float32)
        model.test_model(torch.from_numpy(x_test))


if __name__ == '__main__':
    unittest.main()