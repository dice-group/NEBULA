import argparse
import logging
import random
from logging.config import fileConfig

import torch
from imblearn.over_sampling import RandomOverSampler
from sklearn.model_selection import KFold
from torch.utils.data import SubsetRandomSampler

import settings
from data.dataset import StanceDataset
from utils.util import read_jsonl_from_file, translate_to_classes
from veracity_detection.model import MLP
from tools.run_train import load_scores, get_regression_metrics, calculate_metrics, translate


def parse_args():
    """
    Parse program arguments
    :return:
    """
    parser = argparse.ArgumentParser(prog='K-Fold Cross Validation')
    parser.add_argument('--train-file', required=True, help='Path to JSONL file to train with')
    parser.add_argument('--test-file', help='Path to JSONL file to test with')
    parser.add_argument('--k-folds', default=5, help='Number of folds')
    parser.add_argument('--seed', help='Seed for RNG')
    return parser.parse_args()


def main():
    fileConfig(settings.logging_config)
    args = parse_args()

    # read data from file
    logging.info('Reading JSONL file from {}'.format(args.train_file))
    training_data = read_jsonl_from_file(args.train_file)

    if args.seed:
        seed = args.seed
    else:
        seed = random.randint(0, 1e6)

    oversampler = RandomOverSampler(sampling_strategy='auto', random_state=seed)
    train_dataset = StanceDataset(jsonl=training_data, k=10, resample=oversampler)

    logging.debug('Seed: {}'.format(seed))
    torch.manual_seed(seed)

    # Grid search
    learning_rate = [1e-7, 1e-4, 1e-2]
    batch_size = [16, 128, 512]
    num_epochs = [20, 50, 100]
    dropout = [0.0, 0.5]
    act_fn = [torch.nn.Sigmoid, torch.nn.Tanh]
    loss_fn = [torch.nn.L1Loss, torch.nn.SmoothL1Loss, torch.nn.MSELoss]

    # only keep track of best macro f1
    best_score = 0
    best_params = None
    kfold = KFold(n_splits=args.k_folds, shuffle=True, random_state=seed)

    for af in act_fn:
        for dr in dropout:
            for lf in loss_fn:

                # not interested
                if af == torch.nn.Sigmoid and lf == torch.nn.MSELoss:
                    continue

                for lr in learning_rate:
                    for bs in batch_size:
                        for ne in num_epochs:
                            cur_params = {'learning_rate': lr, 'batch_size': bs, 'num_epochs': ne, 'dropout': dr,
                                          'loss_function': lf, 'activation_fn': af}
                            fold_results = list()
                            for fold, (tr_idx, val_idx) in enumerate(kfold.split(train_dataset)):

                                train_loader = torch.utils.data.DataLoader(dataset=train_dataset,
                                                                           batch_size=bs,
                                                                           sampler=SubsetRandomSampler(tr_idx),
                                                                           drop_last=True)

                                # create model
                                model = MLP(in_channels=10, hidden_channels=[5, 1],
                                            init_weights=torch.nn.init.xavier_uniform_,
                                            init_bias=torch.nn.init.zeros_,
                                            norm_layer=torch.nn.BatchNorm1d,
                                            activation_layer=torch.nn.ReLU,
                                            activation_output=af,
                                            bias=True, dropout=dr)

                                # train
                                train_losses, _ = model.train_model(loss_function=lf,
                                                                    optimizer=torch.optim.Adam,
                                                                    training_loader=train_loader,
                                                                    epochs=ne, lr=lr)

                                val_loader = torch.utils.data.DataLoader(dataset=train_dataset,
                                                                         sampler=SubsetRandomSampler(val_idx),
                                                                         batch_size=1, shuffle=False)

                                # usual shenanigans from run_train
                                results = model.predict(val_loader)
                                true_labels, predicted_scores = load_scores(results)
                                class_labels = ['REFUTES', 'NOT ENOUGH INFO', 'SUPPORTS']

                                if af == torch.nn.Sigmoid:
                                    range = (0.1, 1)
                                else:
                                    range = (-0.9, 1)

                                true_labels, predicted_labels, thresholds = get_regression_metrics(true_labels,
                                                                                                   predicted_scores,
                                                                                                   class_labels, range)

                                current_scores = calculate_metrics(true_labels, predicted_labels, class_labels)

                                fold_results.append((thresholds, current_scores))

                            average_macro_f1 = sum(result[1][3] for result in fold_results) / len(fold_results)
                            # check if macro f1 is better than before
                            if average_macro_f1 > best_score:
                                best_score = average_macro_f1
                                best_params = cur_params
                                logging.info(
                                    'Found better macro F1 {0} with params {1}'.format(best_score, best_params))

    logging.info('Best avg score: {0}'.format(best_score))
    logging.info('Best cross params: {0}'.format(best_params))

    # convert to DataLoader
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=best_params['batch_size'], drop_last=True,
                                               shuffle=True)

    # create model
    best_model = MLP(in_channels=10, hidden_channels=[5, 1],
                     init_weights=torch.nn.init.xavier_uniform_,
                     init_bias=torch.nn.init.zeros_,
                     norm_layer=torch.nn.BatchNorm1d,
                     activation_layer=torch.nn.ReLU,
                     activation_output=best_params['activation_fn'],
                     bias=True, dropout=best_params['dropout'])

    # train
    train_losses, _ = best_model.train_model(loss_function=best_params['loss_function'],
                                             optimizer=torch.optim.Adam,
                                             training_loader=train_loader,
                                             epochs=best_params['num_epochs'], lr=best_params['learning_rate'])

    torch.save(best_model, args.save)

    # use best params to predict on test
    # read and predict
    logging.info('Reading test file from {0}'.format(args.test_file))
    test_data = read_jsonl_from_file(args.test_file)
    test_dataset = StanceDataset(jsonl=test_data, k=args.top_k)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=1, shuffle=False)
    results = best_model.predict(test_loader)

    # Load true labels and predicted scores from predictions
    true_labels, predicted_scores = load_scores(results)

    # regression
    class_labels = ['REFUTES', 'NOT ENOUGH INFO', 'SUPPORTS']
    true_labels = [translate(label) for label in true_labels]

    # Adjust the range based on the output activation function
    if best_params['activation_fn'] == torch.nn.Sigmoid:
        regression_range = (0.1, 1)
    else:
        regression_range = (-0.9, 1)

    true_labels, predicted_labels, best_thresholds = get_regression_metrics(true_labels, predicted_scores,
                                                                            regression_range,
                                                                            class_labels)
    predicted_labels = [translate_to_classes(score, best_thresholds[0], best_thresholds[1], class_labels)
                        for score in predicted_scores]
    metrics = calculate_metrics(true_labels, predicted_labels, class_labels)
    logging.info('Best thresholds {0} from test data {1}'.format(best_thresholds, metrics))


if __name__ == '__main__':
    main()
