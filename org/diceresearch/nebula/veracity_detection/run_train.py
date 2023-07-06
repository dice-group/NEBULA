import argparse
import json
import logging
from itertools import product
from logging.config import fileConfig

import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_curve, auc
from tqdm import tqdm

from org.diceresearch.nebula.data.dataset import StanceDataset
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
    parser.add_argument('--file', required=True, help='Path to JSONL file to read from')
    parser.add_argument('--save', default='resources/model.pt', help='Path where to save the trained model')
    parser.add_argument('--top-k', default=10, type=int, help='Top k evidence')
    parser.add_argument('--dropout', default=0.5, type=float, help='Dropout rate')
    parser.add_argument('--epochs', default=100, type=int, help='Number of epochs')
    parser.add_argument('--batch-size', default=512, type=int, help='Batch size')
    parser.add_argument('--learning-rate', default=1e-4, type=float, help='Learning rate')
    parser.add_argument('--save-predictions', default='resources/predictions.txt', type=str,
                        help='Path where to save the predictions')
    return parser.parse_args()


def translate_to_classes(score, threshold_low, threshold_high):
    if score < threshold_low:
        return 'refutes'
    elif score < threshold_high:
        return 'nei'
    else:
        return 'supports'


def load_data_from_jsonl(file):
    true_labels = []
    predicted_scores = []
    for data in file:
        true_label = data['labels']
        predicted_score = data['predicted_label']
        true_labels.append(true_label)
        predicted_scores.append(predicted_score)
    return true_labels, predicted_scores


def translate(label):
    if label == 0.0:
        return 'REFUTES'
    elif label == 0.5:
        return 'NOT ENOUGH INFO'
    else:
        return 'SUPPORTS'

def main():
    fileConfig('./resources/logging_config.ini')
    args = parse_args()

    # read data from file
    logging.info('Reading JSONL file from {}'.format(args.file))
    with open(args.file, 'r') as json_file:
        data = [json.loads(line) for line in json_file]

    # convert to Dataset and to DataLoader
    train_dataset = StanceDataset(jsonl=data, k=args.top_k)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, drop_last=True)

    # model = MLP(in_channels=args.top_k, hidden_channels=[5, 3],
    #             init_weights=torch.nn.init.xavier_uniform_,
    #             init_bias=torch.nn.init.zeros_,
    #             norm_layer=torch.nn.BatchNorm1d,
    #             activation_layer=torch.nn.ReLU,
    #             activation_output=torch.nn.Softmax,
    #             bias=True, dropout=args.dropout)


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
    train_losses, _ = model.train_model(loss_function=torch.nn.L1Loss,
                                        optimizer=torch.optim.Adam,
                                        training_loader=train_loader,
                                        epochs=args.epochs, lr=args.learning_rate)

    # save model to file TODO uncomment when needed again
    # logging.info('Saved model to {0}'.format(args.save))
    # torch.save(model.state_dict(), args.save)

    # save predictions on training data
    test_loader = torch.utils.data.DataLoader(train_dataset, batch_size=1, shuffle=False)
    predictions = model.predict(test_loader)

    # Load true labels and predicted scores from JSONL file
    true_labels, predicted_scores = load_data_from_jsonl(predictions)

    # Define the labels for the classes
    class_labels = ['REFUTES', 'NOT ENOUGH INFO', 'SUPPORTS']

    # Perform a grid search to find optimal thresholds
    best_thresholds = None
    best_f1 = -1

    thresholds_range = np.arange(0.1, 1.0, 0.1)  # Adjust the range based on your needs
    true_labels = [translate(label) for label in true_labels]

    logging.info('Finding best thresholds')
    for threshold1, threshold2 in tqdm(product(thresholds_range, repeat=2)):
        if threshold1 < threshold2:
            translated_labels = [translate_to_classes(score, threshold1, threshold2) for score in predicted_scores]

            f1 = f1_score(true_labels, translated_labels, average='macro')
            if f1 > best_f1:
                best_f1 = f1
                best_thresholds = (threshold1, threshold2)
                logging.debug('Current best macro F1-score {0} with thresholds {1}'.format(best_f1, best_thresholds))

    # Print the best thresholds and F1 score
    predicted_labels = [translate_to_classes(score, best_thresholds[0], best_thresholds[1]) for score in
                        predicted_scores]

    f1 = f1_score(true_labels, predicted_labels, average='weighted', labels=class_labels)
    accuracy = accuracy_score(true_labels, predicted_labels)
    precision = precision_score(true_labels, predicted_labels, average='weighted', labels=class_labels)
    recall = recall_score(true_labels, predicted_labels, average='weighted', labels=class_labels)
    logging.info('Accuracy Score: {}'.format(accuracy))
    logging.info('Weighted Precision Score: {}'.format(precision))
    logging.info('Weighted Recall Score: {}'.format(recall))
    logging.info('Weighted F1 Score: {}'.format(f1))

    f1_m = f1_score(true_labels, predicted_labels, average='macro', labels=class_labels)
    precision_m = precision_score(true_labels, predicted_labels, average='macro', labels=class_labels)
    recall_m = recall_score(true_labels, predicted_labels, average='macro', labels=class_labels)
    logging.info('Macro Precision Score: {}'.format(precision_m))
    logging.info('Macro Recall Score: {}'.format(recall_m))
    logging.info('Macro F1 Score: {}'.format(f1_m))

    f1_n = f1_score(true_labels, predicted_labels, average=None, labels=class_labels)
    precision_n = precision_score(true_labels, predicted_labels, average=None, labels=class_labels)
    recall_n = recall_score(true_labels, predicted_labels, average=None, labels=class_labels)
    logging.info('Precision Score: {}'.format(precision_n))
    logging.info('Recall Score: {}'.format(recall_n))
    logging.info('F1 Score: {}'.format(f1_n))


if __name__ == '__main__':
    main()