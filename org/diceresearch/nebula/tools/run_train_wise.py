import argparse
import logging
from logging.config import fileConfig

import numpy as np
import torch

import settings
from tools.run_train import calculate_metrics
from utils.util import read_jsonl_from_file, get_optimal_thresholds, translate_to_classes

from data.dataset import WiseDataset, zero_pad_batch
from veracity_detection.model import WISE

"""
    Training script for WISE's final step of a JSON-Lines file.
"""


def parse_args():
    """
    Parse program arguments
    :return:
    """
    parser = argparse.ArgumentParser(prog='Train WISE\'s final step')
    parser.add_argument('--train-file', required=True, help='Path to JSONL file to train with')
    parser.add_argument('--test-file', help='Path to JSONL file to test with')
    parser.add_argument('--save', default='resources/model_rnn.pt',
                        help='Path where to save the trained model')
    parser.add_argument('--dropout', default=0.0, type=float, help='Dropout rate')
    parser.add_argument('--epochs', default=100, type=int, help='Number of epochs')
    parser.add_argument('--batch-size', default=512, type=int, help='Batch size')
    parser.add_argument('--learning-rate', default=1e-4, type=float, help='Learning rate')
    parser.add_argument('--save-predictions', default='resources/predictions.txt', type=str,
                        help='Path where to save the predictions')
    return parser.parse_args()


def main():
    fileConfig(settings.logging_config)
    args = parse_args()

    # read data from file
    logging.info('Reading JSONL file from {}'.format(args.train_file))
    training_data = read_jsonl_from_file(args.train_file)

    # convert to Dataset and to DataLoader
    labels = {0: 1, 1: 0, 2: 0.5}  # NELA labels
    train_dataset = WiseDataset(jsonl=training_data, label_dict=labels)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=args.batch_size, drop_last=True, shuffle=True,
                                               collate_fn=zero_pad_batch)

    # create model
    model = WISE(input_size=1, hidden_size=64, num_layers=5, nonlinearity='relu', bias=True,
                 batch_first=True, dropout=args.dropout, bidirectional=False, output_size=1,
                 activation_output=torch.nn.Sigmoid())
    logging.info(model)

    # train
    train_losses, _ = model.train_model(loss_function=torch.nn.HuberLoss,
                                        optimizer=torch.optim.Adam,
                                        training_loader=train_loader,
                                        epochs=args.epochs, lr=args.learning_rate)

    # save trained model to file
    logging.info('Saved model to {0}'.format(args.save))
    # torch.save(model.state_dict(), args.save)
    torch.save(model, args.save)

    # read and predict
    logging.info('Reading test file from {0}'.format(args.test_file))
    test_data = read_jsonl_from_file(args.test_file)
    test_dataset = WiseDataset(jsonl=test_data, label_dict=labels)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=1, shuffle=False)
    results = model.predict(test_loader)

    # Load true labels and predicted scores from predictions
    true_labels, predicted_scores = load_scores(results)

    # Perform a grid search to find optimal thresholds
    # This is only needed for regression
    # cannot use list(train_dataset.class_counts) as we need the class labels ordered
    class_labels = ['1', '2', '0']
    true_labels = [translate(label) for label in true_labels]

    # Adjust the range based on the output activation function
    best_thresholds = get_optimal_thresholds(thresholds_range=np.arange(0.01, 1.0, 0.01),
                                             classes=class_labels, scores=predicted_scores, true_labels=true_labels)

    # Print the best thresholds and F1 score
    predicted_labels = [translate_to_classes(score, best_thresholds[0], best_thresholds[1], class_labels)
                        for score in predicted_scores]

    # calculate metrics for best thresholds
    calculate_metrics(true_labels, predicted_labels, class_labels)


def translate(label):
    # FIXME
    if label == 0.0:
        return '1'
    elif label == 0.5:
        return '2'
    else:
        return '0'


def load_scores(file):
    true_labels = []
    predicted_scores = []
    for data in file:
        true_label = data[1]
        predicted_score = data[2]
        true_labels.append(true_label)
        predicted_scores.append(predicted_score)
    return true_labels, predicted_scores


if __name__ == '__main__':
    main()