import argparse
import json
import logging
from logging.config import fileConfig
import torch
from os import path

from org.diceresearch.nebula.data.dataset import StanceDataset
from org.diceresearch.nebula.veracity_detection.model import MLP

"""
    Temporary training script for the first step
"""


def parse_args():
    """
    Parse program arguments
    :return:
    """
    parser = argparse.ArgumentParser(prog='Train WISE\'s First Step')
    parser.add_argument('--file', required=True, help='Path to JSONL file to read from')
    parser.add_argument('--save', default='resources/model.pt', help='Path where to save the trained model')
    parser.add_argument('--top-k', default=10, type=int, help='Top k evidence')
    return parser.parse_args()


def main():
    fileConfig('./resources/logging_config.ini')
    args = parse_args()

    # read data from file
    logging.info('Reading JSONL file from {}'.format(args.file))
    with open(args.file, 'r') as json_file:
        data = [json.loads(line) for line in json_file]

    # convert to Dataset and to DataLoader
    train_dataset = StanceDataset(data, args.top_k)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=512, shuffle=True, drop_last=True)

    # create model
    model = MLP(in_channels=args.top_k, hidden_channels=[5, 1],
                init_weights=torch.nn.init.xavier_uniform_,
                init_bias=torch.nn.init.zeros_,
                norm_layer=torch.nn.BatchNorm1d,
                activation_layer=torch.nn.ReLU,
                activation_output=torch.nn.Tanh,
                bias=True, dropout=0.5)
    logging.info(model)

    # train
    train_losses, _ = model.train_model(loss_function=torch.nn.HingeEmbeddingLoss,
                                                 optimizer=torch.optim.Adam,
                                                 training_loader=train_loader,
                                                 epochs=10, lr=1e-4)

    # save model to file
    logging.info('Saved model to {0}'.format(args.save))
    torch.save(model.state_dict(), args.save)


if __name__ == '__main__':
    main()