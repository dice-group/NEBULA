import argparse
import json
import logging
from itertools import product
from logging.config import fileConfig

import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm

from org.diceresearch.nebula.data.dataset import StanceDataset
from org.diceresearch.nebula.utils.util import read_jsonl_from_file, get_optimal_thresholds, translate_to_classes
from org.diceresearch.nebula.veracity_detection.model import MLP

"""
    Temporary training script for the first step of a JSON Lines file.
"""


def parse_args():
    """
    Parse program arguments
    :return:
    """
    parser = argparse.ArgumentParser(prog='Train WISE\'s First Step')
    parser.add_argument('--train-file', required=True, help='Path to JSONL file to train with')
    parser.add_argument('--test-file', help='Path to JSONL file to test with')
    parser.add_argument('--save', default='resources/model.pt', help='Path where to save the trained model')
    parser.add_argument('--top-k', default=10, type=int, help='Top k evidence')
    parser.add_argument('--dropout', default=0.5, type=float, help='Dropout rate')
    parser.add_argument('--epochs', default=100, type=int, help='Number of epochs')
    parser.add_argument('--batch-size', default=512, type=int, help='Batch size')
    parser.add_argument('--learning-rate', default=1e-4, type=float, help='Learning rate')
    parser.add_argument('--save-predictions', default='resources/predictions.txt', type=str,
                        help='Path where to save the predictions')
    return parser.parse_args()


def main():
    fileConfig('./resources/logging_config.ini')
    args = parse_args()

    # read data from file
    logging.info('Reading JSONL file from {}'.format(args.train_file))
    training_data = read_jsonl_from_file(args.train_file)

    # convert to Dataset and to DataLoader
    train_dataset = StanceDataset(jsonl=training_data, k=args.top_k)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=args.batch_size, drop_last=True, shuffle=True)

    # create model
    model = MLP(in_channels=args.top_k, hidden_channels=[5, 1],
                init_weights=torch.nn.init.xavier_uniform_,
                init_bias=torch.nn.init.zeros_,
                norm_layer=torch.nn.BatchNorm1d,
                activation_layer=torch.nn.ReLU,
                activation_output=torch.nn.Sigmoid,
                bias=True, dropout=args.dropout)
    logging.info(model)

    # train
    train_losses, _ = model.train_model(loss_function=torch.nn.SmoothL1Loss,
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
    test_dataset = StanceDataset(jsonl=test_data, k=args.top_k)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=1, shuffle=False)
    results = model.predict(test_loader)

    # Load true labels and predicted scores from predictions
    true_labels, predicted_scores = load_scores(results)

    # Perform a grid search to find optimal thresholds
    # This is only needed for regression
    # cannot use list(train_dataset.class_counts) as we need the class labels ordered
    class_labels = ['REFUTES', 'NOT ENOUGH INFO', 'SUPPORTS']
    true_labels = [translate(label) for label in true_labels]

    # Adjust the range based on the output activation function
    best_thresholds = get_optimal_thresholds(thresholds_range=np.arange(0.1, 1.0, 0.1),
                                             classes=class_labels, scores=predicted_scores, true_labels=true_labels)

    # Print the best thresholds and F1 score
    predicted_labels = [translate_to_classes(score, best_thresholds[0], best_thresholds[1], class_labels)
                        for score in predicted_scores]

    # Compute accuracy
    accuracy = accuracy_score(true_labels, predicted_labels)
    logging.info('Accuracy Score: {}'.format(accuracy))

    # Compute weighted metrics
    f1 = f1_score(true_labels, predicted_labels, average='weighted', labels=class_labels)
    precision = precision_score(true_labels, predicted_labels, average='weighted', labels=class_labels)
    recall = recall_score(true_labels, predicted_labels, average='weighted', labels=class_labels)
    logging.info('Weighted Precision Score: {}'.format(precision))
    logging.info('Weighted Recall Score: {}'.format(recall))
    logging.info('Weighted F1 Score: {}'.format(f1))

    # Compute macro metrics
    f1_m = f1_score(true_labels, predicted_labels, average='macro', labels=class_labels)
    precision_m = precision_score(true_labels, predicted_labels, average='macro', labels=class_labels)
    recall_m = recall_score(true_labels, predicted_labels, average='macro', labels=class_labels)
    logging.info('Macro Precision Score: {}'.format(precision_m))
    logging.info('Macro Recall Score: {}'.format(recall_m))
    logging.info('Macro F1 Score: {}'.format(f1_m))

    # Compute metrics per label
    f1_n = f1_score(true_labels, predicted_labels, average=None, labels=class_labels)
    precision_n = precision_score(true_labels, predicted_labels, average=None, labels=class_labels)
    recall_n = recall_score(true_labels, predicted_labels, average=None, labels=class_labels)
    logging.info('Precision Score: {}'.format(precision_n))
    logging.info('Recall Score: {}'.format(recall_n))
    logging.info('F1 Score: {}'.format(f1_n))


def translate(label):
    # FIXME
    if label == 0.0:
        return 'REFUTES'
    elif label == 0.5:
        return 'NOT ENOUGH INFO'
    else:
        return 'SUPPORTS'

def load_scores(file):
    true_labels = []
    predicted_scores = []
    for data in file:
        true_label = data['labels']
        predicted_score = data['predicted_label']
        true_labels.append(true_label)
        predicted_scores.append(predicted_score)
    return true_labels, predicted_scores


if __name__ == '__main__':
    main()