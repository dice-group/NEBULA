import argparse
import logging
import random
from collections import Counter
from logging.config import fileConfig

import numpy as np
import torch
from imblearn.over_sampling import SMOTE
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

import settings
from data.dataset import StanceDataset
from sklearn.preprocessing import MinMaxScaler
from utils.util import read_jsonl_from_file, get_optimal_thresholds, translate_to_classes
from veracity_detection.model import MLP
from sklearn.metrics import confusion_matrix, classification_report

"""
    Training script for the first step of a JSON Lines file.
"""


def parse_args():
    """
    Parse program arguments
    :return:
    """
    parser = argparse.ArgumentParser(prog='Train WISE\'s First Step')
    parser.add_argument('--train-file', required=True, help='Path to JSONL file to train with')
    parser.add_argument('--val-file', help='Path to JSONL file to validate with')
    parser.add_argument('--test-file', help='Path to JSONL file to test with')
    parser.add_argument('--save', default='resources/model_tanh_mse.pt', help='Path where to save the trained model')
    parser.add_argument('--top-k', default=10, type=int, help='Top k evidence')
    parser.add_argument('--dropout', default=0.5, type=float, help='Dropout rate')
    parser.add_argument('--epochs', default=150, type=int, help='Number of epochs')
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

    # Use this to oversample from the minority classes
    seed = random.randint(0, 1e6)
    logging.debug('Seed for over sampler: {0}'.format(seed))
    oversampler = None
    # oversampler = SMOTE(sampling_strategy='auto', random_state=seed)

    # FEVER labels to int
    label_dict = {"SUPPORTS": 1, "NOT ENOUGH INFO": 0, "REFUTES": -1}

    # convert to Dataset and to DataLoader
    scaler = MinMaxScaler()
    train_dataset = StanceDataset(jsonl=training_data, k=args.top_k, resample=oversampler, is_train=True, scaler=scaler, label_dict=label_dict)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=args.batch_size, drop_last=True, shuffle=True)

    val_loader = None
    if args.val_file:
        val_data = read_jsonl_from_file(args.val_file)
        val_dataset = StanceDataset(jsonl=val_data, k=args.top_k, resample=None, is_train=False, scaler=scaler, label_dict=label_dict)
        val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=1, shuffle=False)

    # create model
    model = MLP(in_channels=args.top_k, hidden_channels=[5, 1],
                init_weights=torch.nn.init.xavier_uniform_,
                init_bias=torch.nn.init.zeros_,
                norm_layer=torch.nn.BatchNorm1d,
                activation_layer=torch.nn.GELU,
                activation_output=torch.nn.Tanh,
                bias=True, dropout=args.dropout)
    logging.info(model)

    # train
    model.train_model(loss_function=torch.nn.MSELoss,
                                        optimizer=torch.optim.Adam,
                                        training_loader=train_loader,
                                        validation_loader=val_loader,
                                        epochs=args.epochs, lr=args.learning_rate)

    # save trained model to file
    logging.info('Saved model to {0}'.format(args.save))
    # torch.save(model.state_dict(), args.save)
    torch.save(model, args.save)

    # read and predict
    logging.info('Reading test file from {0}'.format(args.test_file))
    test_data = read_jsonl_from_file(args.test_file)
    test_dataset = StanceDataset(jsonl=test_data, k=args.top_k, label_dict=label_dict, scaler=scaler, is_train=False)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=1, shuffle=False)
    results = model.predict(test_loader)

    # Load true labels and predicted scores from predictions
    true_labels, predicted_scores = load_scores(results)

    # classification
    # class_labels = [0, 1, 2]
    # predicted_labels = [get_highest_index(score) for score in predicted_scores]
    # true_labels = [score.item() for score in true_labels]

    # regression
    class_labels = ['REFUTES', 'NOT ENOUGH INFO', 'SUPPORTS']
    true_labels, predicted_labels, best_thresholds = get_regression_metrics(true_labels, predicted_scores, class_labels, (-1, 1))

    # calculate metrics for best thresholds
    calculate_metrics(true_labels, predicted_labels, class_labels)


def get_regression_metrics(true_labels, predicted_scores, class_labels, regression_range):
    # Perform a grid search to find optimal thresholds
    # This is only needed for regression

    # cannot use list(train_dataset.class_counts) as we need the class labels ordered
    # class_labels = ['REFUTES', 'NOT ENOUGH INFO', 'SUPPORTS']
    true_labels = [translate(label) for label in true_labels]

    # Adjust the range based on the output activation function
    best_thresholds = get_optimal_thresholds(thresholds_range=np.arange(regression_range[0], regression_range[1], 0.01),
                                             classes=class_labels, scores=predicted_scores, true_labels=true_labels)

    # Print the best thresholds and F1 score
    predicted_labels = [translate_to_classes(score, best_thresholds, class_labels)
                        for score in predicted_scores]

    frequency_count = Counter(predicted_labels)
    logging.info(f"Label frequency count in the test predictions: {frequency_count}")

    return true_labels, predicted_labels, best_thresholds


def calculate_metrics(true_labels, predicted_labels, class_labels):

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

    # Compute micro metrics
    f1_mi = f1_score(true_labels, predicted_labels, average='micro', labels=class_labels)
    precision_mi = precision_score(true_labels, predicted_labels, average='micro', labels=class_labels)
    recall_mi = recall_score(true_labels, predicted_labels, average='micro', labels=class_labels)
    logging.info('Micro Precision Score: {}'.format(precision_mi))
    logging.info('Micro Recall Score: {}'.format(recall_mi))
    logging.info('Micro F1 Score: {}'.format(f1_mi))

    # Compute metrics per label
    f1_n = f1_score(true_labels, predicted_labels, average=None, labels=class_labels)
    precision_n = precision_score(true_labels, predicted_labels, average=None, labels=class_labels)
    recall_n = recall_score(true_labels, predicted_labels, average=None, labels=class_labels)
    logging.info('Precision Score: {}'.format(precision_n))
    logging.info('Recall Score: {}'.format(recall_n))
    logging.info('F1 Score: {}'.format(f1_n))

    logging.info(classification_report(true_labels, predicted_labels))
    logging.info(confusion_matrix(true_labels, predicted_labels))


def translate(label):
    # FIXME
    if label == -1:
        return 'REFUTES'
    elif label == 0:
        return 'NOT ENOUGH INFO'
    else:
        return 'SUPPORTS'


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