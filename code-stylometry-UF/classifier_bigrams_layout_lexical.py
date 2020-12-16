#!/usr/bin/env python

# Author: Guillermo Suarez-Tangil

import os, sys
from optparse import OptionParser
import settings
import numpy as np
from timeit import default_timer
import traceback


from sklearn import preprocessing
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold, train_test_split, cross_val_score, cross_val_predict, PredefinedSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss, classification_report, confusion_matrix

#from samples_bigrams_layout_lexical import fetch_samples, get_index_relevant_class
from samples_bigrams_layout_lexical import fetch_samples, get_index_relevant_class
#from samples_ensambled_probs import fetch_samples, get_index_relevant_class

option_1 = { 'name' : ('-i', '--input'), 'help' : 'path : path to folder containing input files', 'nargs' : 1 }
option_2 = { 'name' : ('-d', '--debug'), 'help' : 'debug', 'action': 'store_true', 'default': False }
option_3 = { 'name' : ('-s', '--given_split'), 'help' : 'Uses holdout validation with a given split', 'action': 'store_true', 'default': False }
options = [option_1, option_2, option_3]

ids = []
ids_and_authors_dict = {}

def spawn_classifier(classifier_name=settings.classifier_name, processors=settings.processors):
    print('Baseline classifier:', classifier_name)
    if classifier_name == 'SVM':
        global SVC
        from sklearn.svm import SVC
        classifier = SVC(probability=True,
kernel='linear'
                        )
    elif classifier_name == 'RF':
        global RandomForestClassifier
        from sklearn.ensemble import RandomForestClassifier
        max_features = 'sqrt'
        classifier = RandomForestClassifier(n_estimators=1250,
                                            bootstrap=False, min_samples_leaf=3, min_samples_split=3, criterion='entropy', max_depth=None,
                                            max_features=max_features, n_jobs=processors)
    elif classifier_name == 'XGB':
        global XGBClassifier
        from xgboost import XGBClassifier
        max_features = 'sqrt'
        classifier = XGBClassifier(learning_rate=0.4, n_estimators=55, max_depth=6, max_features=max_features, nthread=processors)
    elif classifier_name == 'LSVM':
        global LinearSVC
        from sklearn.svm import LinearSVC
        classifier = LinearSVC(max_iter=350, tol=0.002)
    elif classifier_name == 'XTREE':
        global ExtraTreesClassifier
        from sklearn.ensemble import ExtraTreesClassifier
        classifier = ExtraTreesClassifier(n_estimators=1250,
                                          warm_start=True, bootstrap=True, min_samples_leaf=10, min_samples_split=5, criterion='gini', max_features=None, max_depth=None,
                                          n_jobs=processors)
    elif classifier_name == 'LSVR':
        global LinearSVR
        from sklearn.svm import LinearSVR
        classifier = LinearSVR(max_iter=350, tol=0.002)
    else:
        raise Exception('Baseline classifer "{}" not supported. Supported classifiers are: {}'.format(classifier_name, str(settings.classifiers.keys())))
    return classifier
    #TODO
    #from sklearn.tree import DecisionTreeClassifier
    #from sklearn.linear_model import LogisticRegression
    #from sklearn.linear_model import RidgeClassifier
    #from sklearn.linear_model import SGDClassifier
    #from sklearn.naive_bayes import BernoulliNB
    #from sklearn.naive_bayes import GaussianNB
    #from sklearn.naive_bayes import MultinomialNB
    #from sklearn.multiclass import OneVsRestClassifier


def spawn_classifiers(classifiers=settings.classifiers, processors=settings.processors):

    params = []
    estimators = []
    for classifier_id in classifiers:
        classifier_name = classifiers[classifier_id]
        clf = spawn_classifier(classifier_name=classifier_name, processors=processors)
        estimators.append((classifier_name, clf))
    return estimators


def spawn_parameters(classifier_name=settings.classifier_name, prefix=True):

    if not prefix:
        classifier_prefix = ''
    else:
        classifier_prefix = classifier_name + '__'

    if classifier_name == 'SVM' or classifier_name == 'LSVM':

        parameters = { classifier_prefix + 'kernel': ('linear', 'rbf'), #'linear', 'poly', 'rbf', 'sigmoid', 'precomputed'
                    classifier_prefix + 'C': [1, 10],
                    classifier_prefix + 'max_iter': [-1, 150, 250, 350],
                    classifier_prefix + 'tol': [0.001, 0.002, 0.005, 0.01],
                    }

    elif classifier_name == 'RF' or classifier_name == 'XGB' or classifier_name == 'XTREE':

        parameters = {classifier_prefix + 'max_depth': [3, None],
              classifier_prefix + 'max_features': ['sqrt', 'log2', None],
              classifier_prefix + 'min_samples_split': [2, 3, 5, 10],
              classifier_prefix + 'min_samples_leaf': [1, 3, 10],
              classifier_prefix + 'bootstrap': [True, False],
              classifier_prefix + 'criterion': ["gini", "entropy"],
              classifier_prefix + 'n_estimators': [10, 16, 32, 50, 100, 500, 1000, 1500]}

    else:

        raise Exception('Baseline parameters {} not supported. Supported classifiers are: {}'.format(classifier_name, str(settings.classifiers.keys())))

    if classifier_name == 'XGB':
        # Boosting Parameters
        parameters[classifier_prefix + 'learning_rate'] = [0.8, 1.0]

    if classifier_name == 'XTREE':
        # Boosting Parameters
        parameters[classifier_prefix + 'warm_start'] = [True, False]
        #parameters[classifier_prefix + 'oob_score'] = [True, False]

    return parameters


def feature_selection(classifier_name, processors=4):
    if not classifier_name:
        print('Feature selection: deactivated')
        return None
    else:
        from sklearn.feature_selection import SelectFromModel

    if classifier_name == 'SVM':
        fselection_model = SelectFromModel(SVC(C=0.10), prefit=False)
    elif classifier_name == 'RF' or classifier_name == 'XTREE' or classifier_name == 'XBG':
        from sklearn.ensemble import RandomForestClassifier
        if classifier_name != 'RF':
            print('Warning: RandomForest has been forced as baseline feature selection method')
        fselection_model = SelectFromModel(RandomForestClassifier(n_estimators=1250, n_jobs=processors), prefit=False)
    elif classifier_name == 'LSVM':
        fselection_model = SelectFromModel(LinearSVC(C=C, penalty="l1", dual=False), prefit=False)
    else:
        raise Exception('Baseline feature selection method "{}" not supported. Supported classifiers are: {}'.format(classifier_name, str(settings.classifiers.keys())))
    print('Feature selection: activated (baseline feature selection method: {})'.format(classifier_name))
    return fselection_model
    #TODO
    #from sklearn.feature_selection import SelectKBest
    #from sklearn.feature_selection import chi2
    #from sklearn.feature_selection import f_classif

def split_dataset(X, Y):
    return train_test_split(X, Y, test_size=0.33, random_state=42, stratify = Y)

def create_fvector(samples):
    X = []
    Y = []
    FILENAMES = []

    D = []
    fvector_labels = []

    for sample in samples:
        D.append(sample['features'])
        Y.append(sample['class'])
        FILENAMES.append(sample['filename'])

    v = DictVectorizer(sparse=False)
    X = v.fit_transform(D)

    fvector_labels = v.feature_names_
    class_names = np.array(list(set(Y)))

    print('features =', fvector_labels)
    print('#features =', len(fvector_labels))
    print('classes =', class_names)

    return X, Y, class_names, fvector_labels, FILENAMES

def create_fvector_train_test(samples_train, samples_test):

    # ------ Processing training set
    X_train = []
    Y_train = []

    D_train = []
    fvector_labels = []

    for sample in samples_train:
        D_train.append(sample['features'])
        Y_train.append(sample['class'])

    v_train = DictVectorizer(sparse=False)
    X_train = v_train.fit_transform(D_train)

    fvector_labels = v_train.feature_names_
    class_names = np.array(list(set(Y_train)))

    print('features =', fvector_labels)
    print('#features =', len(fvector_labels))
    print('classes =', class_names)

    # ------ Processing testing set
    X_test = []
    Y_test = []

    D_test = []

    for sample in samples_test:
        D_test.append(sample['features'])
        Y_test.append(sample['class'])

    X_test = v_train.transform(D_test)

    return X_train, X_test, Y_train, Y_test, class_names, fvector_labels


def print_metrics(Y_test, predicted, class_names, labels=None):

    average = 'micro'
    #average = None
    #if len(class_names) > 2:
    #    average = 'micro'

    cmatrix = confusion_matrix(Y_test, predicted, labels=class_names)
    report = classification_report(Y_test, predicted, labels=class_names)
    precision = precision_score(Y_test, predicted, average=average, labels=labels)
    recall = recall_score(Y_test, predicted, average=average, labels=labels)
    f1 = f1_score(Y_test, predicted, average=average, labels=labels)
    accuracy = accuracy_score(Y_test, predicted)
    #logloss = log_loss(Y_test, predicted)

    #print("PREDICTED:")
    #print(predicted)
    #print(len(predicted))
    #print("Y_TEST:")
    #print(Y_test)
    #print(len(Y_test))

    if type(precision) is np.ndarray:
        precision = precision.mean()

    if type(recall) is np.ndarray:
        recall = precision.mean()

    if type(f1) is np.ndarray:
        f1 = precision.mean()

    np.savetxt('/home/k1462425/Documents/Research/ast_bigram_approach/data/cmatrix.txt', cmatrix)
    with open('/home/k1462425/Documents/Research/ast_bigram_approach/data/classnames.txt', 'w') as f:
        for item in class_names:
            f.write("%s\n" % item)

    print('Confusion Matrix: (*)')
    #print(class_names)
    print(cmatrix)
    print('\t (*) Note that confusion matrix C is such that C_{i, j} is equal to the number of observations known to be in group i but predicted to be in group j.')
    print('Report:')
    print(report)
    print('Metrics reported for', labels)
    print('Precision: {0:.4f}'.format(precision))
    print('Recall: {0:.4f}'.format(recall))
    print('F1-score: {0:.4f}'.format(f1))
    print('Accuracy: {0:.4f}'.format(accuracy))
    #print 'Log-loss crossvalidation: {0:.2f}'.format(logloss)


def holdout(classifier, X_test, Y_test):
    print('Accuracy holdout:', classifier.score(X_test, Y_test))


def crossvalidation(classifier, X, Y, filenames, parentsamples_and_functionsamples, class_names, cv=5, labels = None):
    scores = cross_val_score(classifier, X, Y, cv=cv)
    #print("SCORES")
    #print(scores)
    #print(predicted)
    predicted = cross_val_predict(classifier, X, Y, cv=cv)
    #predicted_majorvoted = majority_voting(Y,predicted,filenames,parentsamples_and_functionsamples)

    print("PREDICTED")
    print(predicted)
    #print("PREDICTED_MAJORVOTED")
    #print(predicted_majorvoted)
    #print("PREDICTED")
    #print("Y")
    #print(Y)
    howmanywrong = calc_wrongs(Y,predicted)
    global ids
    pairs = get_wrong_id_pairs(Y,predicted)
    #print("WRONGLY ATTRIBUTED SAMPLES:")
    actual_ids = []
    for pair in pairs:
        actual_ids.append(str(pair[0])+"\n")

    if os.path.exists("/home/k1462425/Documents/Research/ast_bigram_approach/data/misclassified_ids.txt"):
        os.remove("/home/k1462425/Documents/Research/ast_bigram_approach/data/misclassified_ids.txt")
    with open("/home/k1462425/Documents/Research/ast_bigram_approach/data/misclassified_ids.txt",'a+') as fp:
        fp.writelines(actual_ids)

    fp.close()

    if os.path.exists("/home/k1462425/Documents/Research/ast_bigram_approach/data/misclassified_pairs.txt"):
        os.remove("/home/k1462425/Documents/Research/ast_bigram_approach/data/misclassified_pairs.txt")
    #with open("/home/k1462425/Documents/Research/ast_bigram_approach/data/misclassified_pairs.txt",'a+') as fp:
    #    for pair in pairs:
    #        fp.write(pair[0]+","+pair[1]+","+pair[2]+"\n")

    fp.close()

    for pair in pairs:
        #if pair[1] == "327316_4" and pair[2] == "601720_4":
        print(pair)

    #print(pairs)
    #print("NUMBER OF MISTAKES")
    #print(howmanywrong)
    #print("OUT OF")
    #print(len(predicted))
    print("---------")
    print("Ground truth (Y)")
    print(Y)
    print("----------")
    print("X")
    print(X)

    print('Accuracy crossvalidation: {0:.2f} (+/- {0:.2f})'.format(scores.mean(), scores.std()))
    print_metrics(Y, predicted, class_names, labels)

def get_wrong_id_pairs(ground_truth,predicted):
    global ids
    global ids_and_authors_dict
    pairs = []
    x = 0
    while x < len(ground_truth):
        if ground_truth[x] != predicted[x]:
            pair = (ids[x],ground_truth[x],predicted[x])
            pairs.append(pair)
        x = x + 1

    return pairs


def plot_coefficients(classifier, feature_names, top_features=20):
    import matplotlib.pyplot as plt
    coef = classifier.coef_.ravel()
    top_positive_coefficients = np.argsort(coef)[-top_features:]
    top_negative_coefficients = np.argsort(coef)[:top_features]
    top_coefficients = np.hstack([top_negative_coefficients, top_positive_coefficients])

    feature_names = np.array(feature_names)

    for feature in top_coefficients:
        print(feature_names[feature], coef[feature])

    plt.figure(figsize=(15, 5))
    colors = ['red' if c < 0 else 'blue' for c in coef[top_coefficients]]
    plt.bar(np.arange(2 * top_features), coef[top_coefficients], color=colors)
    plt.xticks(np.arange(0, 0 + 2 * top_features), feature_names[top_coefficients], rotation=60, ha='right')
    plt.show()

def plot_importance(classifier, feature_names, top_features=20):
    import matplotlib.pyplot as plt
    coef = classifier.feature_importances_
    top_positive_coefficients = np.argsort(coef)[-top_features:]
    top_negative_coefficients = np.argsort(coef)[:top_features]
    top_coefficients = np.hstack([top_negative_coefficients, top_positive_coefficients])

    plt.figure(figsize=(15, 5))
    colors = ['red' if c < 0 else 'blue' for c in coef[top_coefficients]]
    plt.bar(np.arange(2 * top_features), coef[top_coefficients], color=colors)
    feature_names = np.array(feature_names)
    plt.xticks(np.arange(1, 1 + 2 * top_features), feature_names[top_coefficients], rotation=60, ha='right')
    plt.show()

def print_feature_ranking(classifier, classifier_name, fvector_labels):

    print(' ----- Feature Importance ----- ')
    print('features =', fvector_labels)
    if classifier_name == 'SVM' or classifier_name == 'LSVM':

        print(classifier.coef_)
        plot_coefficients(classifier, fvector_labels)

    elif classifier_name == 'RF' or classifier_name == 'XGB' or classifier_name == 'XTREE':

        print(classifier.feature_importances_)
        plot_importance(classifier, fvector_labels)

    else: raise Exception('Feature ranking for {} not supported.'.format(classifier_name))

    print(' ------------------------------ ')

def print_summary(classifier, X_train, X_test, fvector_labels):
    print(' ------  Summary  ------ ')
    if settings.feature_selection:
        features = classifier.named_steps['feature_selection']
        print(str(features))
        features_names =  []#features.transform(X)
        #features_names = X[features.transform(np.arange(X.shape[1]))]
        #features_names = X.columns[features.transform(np.arange(len(X.columns)))]
    else:
        features_names = fvector_labels
    print('#samples:', X_train.shape[0] + X_test.shape[0])
    print('#samples_train:', X_train.shape[0])
    print('#samples_test:', X_test.shape[0])
    print('#features: {} (out of {})'.format(len(features_names), len(fvector_labels)))
    print('#features_train:', X_train.shape[1])
    print('#features_test:', X_test.shape[1])
    #print 'features', features_names
    print(' --------------------- ')


def prepare_data_crossvalidation(path_samples):

    # ------ Fetch samples
    samples = fetch_samples(path_samples)

    # ------ Create feature vector
    X, Y, class_names, fvector_labels, filenames = create_fvector(samples)

    print("X")
    print(X)
    print("X len")
    print(len(X))
    print("X len elem")
    print(len(X[0]))
    print("Y")
    print(Y)
    #print("FVECTOR LABELS")
    #print(fvector_labels)
    #print("SAMPLES")
    #print(samples)

    print("SAMPLES 0")
    print(samples[0])
    print("SAMPLES TYPE")
    print(type(samples))

    global ids
    global ids_and_authors_dict

    x = 0
    while x < len(samples):
        ids_and_authors_dict[samples[x]['id']] = samples[x]['class']
        x = x + 1
    x = 0
    while x < len(samples):
        ids.append(samples[x]['id'])
        x = x + 1

    parentsamples_and_functionsamples = {}
    for sample in samples:
        function_sample = sample['filename']
        function_sample_split = function_sample.split(".")[0]
        parentsample2 = ""
        parentsample = function_sample_split.split("_")[:-1]
        print(parentsample)
        for elem in parentsample:
            parentsample2 = parentsample2 + elem
            parentsample2 = parentsample2 + "_"
        parentsample2 = parentsample2[:-1]
        print(parentsample2)
        parentsamples_and_functionsamples[parentsample2] = []

    for sample in samples:
        function_sample = sample['filename']
        function_sample_split = function_sample.split(".")[0]
        parentsample2 = ""
        parentsample = function_sample_split.split("_")[:-1]
        #print(parentsample)
        for elem in parentsample:
            parentsample2 = parentsample2 + elem
            parentsample2 = parentsample2 + "_"
        parentsample2 = parentsample2[:-1]
        #print(parentsample2)
        parentsamples_and_functionsamples[parentsample2].append(function_sample)

    print(parentsamples_and_functionsamples)
    print(filenames)

    return X, Y, class_names, fvector_labels, samples, parentsamples_and_functionsamples, filenames

def getXYFolds(X, Y, folds):
    XY_folds = []
    for train_index, test_index in folds.split():
        X_train, X_test = X[train_index], X[test_index]
        Y_train, Y_test = Y[train_index], Y[test_index]
        fold = (X_train, X_test, Y_train, Y_test)
        XY_folds.append(fold)
    return XY_folds

def prepare_data_crossvalidation_given_split(path_samples):

    # ------ Fetch samples
    samples = fetch_samples(path_samples)

    test_fold = []
    for sample in samples:
        test_fold.append(sample['fold'])

    # ------ Create feature vector
    X, Y, class_names, fvector_labels = create_fvector(samples)

    folds = PredefinedSplit(test_fold)

    return X, Y, class_names, fvector_labels, folds, samples


def prepare_data_gridCrossvalidation(path_samples):

    # ------ Fetch samples
    samples_train = fetch_samples(os.path.join(path_samples, 'train'))
    samples_test = fetch_samples(os.path.join(path_samples, 'test'))

    test_fold = []
    for sample in samples_train:
        test_fold.append(sample['fold'])

    # ------ Create feature vector
    X_train, X_test, Y_train, Y_test, class_names, fvector_labels = create_fvector_train_test(samples_train, samples_test)

    folds = PredefinedSplit(test_fold)

    return X_train, X_test, Y_train, Y_test, class_names, fvector_labels, folds, samples_train, samples_test

def prepare_data_holdout_given_split(path_samples):

    # ------ Fetch samples
    samples_train = fetch_samples(os.path.join(path_samples, 'train'))
    samples_test = fetch_samples(os.path.join(path_samples, 'test'))
    #samples_test = fetch_samples(os.path.join(path_samples, 'validation'))

    # ------ Create feature vector from already splitted dataset
    X_train, X_test, Y_train, Y_test, class_names, fvector_labels = create_fvector_train_test(samples_train, samples_test)

    return X_train, X_test, Y_train, Y_test, class_names, fvector_labels, samples_train, samples_test


def prepare_data_holdout_random_split(path_samples):

    # ------ Fetch samples
    samples = fetch_samples(path_samples)

    # ------ Create feature vector
    X, Y, class_names, fvector_labels, filenames = create_fvector(samples)

    # ------ Split Dataset
    X_train, X_test, Y_train, Y_test = split_dataset(X, Y)


    return X_train, X_test, Y_train, Y_test, class_names, fvector_labels, samples


def main_holdout(options, arguments):

    # ------ Read input options and overwrite settings when redundant
    path_samples = options.input
    if not path_samples:
        raise AttributeError('Invalid --input (-i)')

    # ------ init
    if options.given_split:
        X_train, X_test, Y_train, Y_test, class_names, fvector_labels, samples_train, samples_test = prepare_data_holdout_given_split(path_samples)
    else:
        X_train, X_test, Y_train, Y_test, class_names, fvector_labels, samples = prepare_data_holdout_random_split(path_samples)


    def zero_rule_algorithm_classification(train, test):
        #print("TRAIN")
        #print(train)
        #print("TEST")
        #print(test)
        values_and_amounts_dict = {}
        for elem in train:
            values_and_amounts_dict[elem] = 0
        for elem in train:
            values_and_amounts_dict[elem] = values_and_amounts_dict[elem] + 1

        max_class = ''
        max_amount = 0
        for elem in values_and_amounts_dict:
            if values_and_amounts_dict[elem] > max_amount:
                max_class = elem
                max_amount = values_and_amounts_dict[elem]

        predicted = [None]*len(test)

        x = 0
        while x < len(test):
            predicted[x] = max_class
            x = x + 1

        return predicted


    # ------ Preprocess data
    X_train = np.asarray(X_train)
    Y_train = np.asarray(Y_train)
    X_test = np.asarray(X_test)
    Y_test = np.asarray(Y_test)
    std_scale = preprocessing.RobustScaler().fit(X_train) # StandardScaler --- RobustScaler
    X_train = std_scale.transform(X_train)
    X_test = std_scale.transform(X_test)

    # ------ Build classifier
    classifier = spawn_classifier()

    #  ------ Feature selection
    fselection_model = feature_selection(settings.feature_selection, settings.processors)
    if fselection_model:
        classifier = Pipeline([('feature_selection', fselection_model), ('classification', classifier)])

    print_summary(classifier, X_train, X_test, fvector_labels)

    # ------ Train and Test holdout
    classifier.fit(X_train, Y_train)
    predicted = classifier.predict(X_test)
    #print("X_TEST:")
    #print(X_test)
    #print("PREDICTED:")
    #print(predicted)
    #predicted = zero_rule_algorithm_classification(Y_train,Y_test) #uncomment this line to instead obrain the ZeroR classifier accuracy
    #print("PREDICTED2:")
    #print(predicted)
    #holdout(classifier, X_test, Y_test)

    #------- Feature Ranking and Metrics
    #print_feature_ranking(classifier, settings.classifier_name, ['action' if l == 'are' else l for l in fvector_labels]) COMMENTING THIS OUT: MTK
    print_metrics(Y_test, predicted, class_names, [class_names[get_index_relevant_class()]])

    # ------ Other stuff
    probabilities = classifier.predict_proba(X_test)
    decision_function = []
    #if settings.classifier_name == 'SVM':
    #    decision_function = classifier.decision_function(X_test)
    if options.given_split:
        from samples import ___store_individual_predictions
        ___store_individual_predictions(samples_test, predicted, probabilities, np.where(class_names=='scam'), decision_function)


def main_crossvalidation(options, arguments):

    # ------ Read input options and overwrite settings when redundant
    path_samples = options.input
    if not path_samples:
        raise AttributeError('Invalid --input (-i)')

    # ------ init
    if options.given_split:
        X, Y, class_names, fvector_labels, folds, samples = prepare_data_crossvalidation_given_split(path_samples)
    else:
        X, Y, class_names, fvector_labels, samples, parentsamples_and_functionsamples, filenames = prepare_data_crossvalidation(path_samples)
        folds = 5

    pipe = []

    scaler = preprocessing.RobustScaler()
    pipe.append(('scaler', scaler))

    fselection_model = feature_selection(settings.feature_selection, settings.processors)
    if fselection_model:
        pipe.append(('feature_selection', fselection_model))

    # ------ Build classifier
    classifier = spawn_classifier()
    pipe.append(('classification', classifier))

    classifier = Pipeline(pipe)

    #print("SAMPLES")
    #print(samples)

    # ------ Train and Test crossvalidation
    predicted = crossvalidation(classifier, X, Y, filenames, parentsamples_and_functionsamples, class_names, folds, [class_names[get_index_relevant_class()]])


    #print("PREDICTED")
    #print(predicted)
    #print("PREDICTED MAJORVOTED")
    #print(predicted_majorvoted)

    # ------ Other stuff
    if options.given_split:
        from samples import ___store_individual_predictions
        ___store_individual_predictions(samples, predicted)


def majority_voting(groundtruth_functions,predicted_functions,function_filenames,parentsamples_and_functionsamples):
    parents = set([])
    for function in function_filenames:
        parentName1 = function.split(".")[0]
        parentName2 = parentName1.split("_")[0]+"_"+parentName1.split("_")[1]+"_"+parentName1.split("_")[2]
        parents.add(parentName2)

    parents_predicted = {}

    for parent in parents:
        parents_predicted[parent] = ""

    for parent in parents:
        parent_functions = parentsamples_and_functionsamples[parent]
        predicted_votes = []
        for function in parent_functions:
            index = function_filenames.index(function)
            predicted_function_class = predicted_functions[index]
            predicted_votes.append(predicted_function_class)
            majority_vote = find_majority_vote(predicted_votes)

        parents_predicted[parent] = majority_vote

    new_predicted_functions = [None]*len(predicted_functions)

    #print("Length of function filenames: "+str(len(function_filenames)))
    #print("Length of predicted vector: "+str(len(predicted_functions)))
    #print(len(new_predicted_functions))

    for parent in parentsamples_and_functionsamples:
        parent_predicted = parents_predicted[parent]
        function_samples = parentsamples_and_functionsamples[parent]
        for function_sample in function_samples:
            index = function_filenames.index(function_sample)
            #print(index)
            if len(parents_predicted[parent]) > 0:
                new_predicted_functions[index] = parents_predicted[parent]
            else:
                new_predicted_functions[index] = predicted_functions[index]

    return new_predicted_functions


def find_majority_vote(predicted_votes):
    votes_amounts = {}
    for vote in predicted_votes:
        votes_amounts[vote] = 0

    for vote in predicted_votes:
        votes_amounts[vote] = votes_amounts[vote] + 1

    all_values = votes_amounts.values()
    max_value = max(all_values)

    maximum_valued_votes = []
    for vote in votes_amounts:
        if votes_amounts[vote] == max_value:
            maximum_valued_votes.append(vote)

    majority_voted_class = ""
    if len(maximum_valued_votes) == 1:
        majority_voted_class = maximum_valued_votes[0]

    return majority_voted_class


def calc_wrongs(ground_truth,predicted):
    sum = 0
    x = 0
    while x < len(ground_truth):
        if ground_truth[x] != predicted[x]:
            sum += 1
        x = x + 1
    return sum

def main_gridCrossvalidation(options, arguments):

    # ------ Read input options and overwrite settings when redundant
    path_samples = options.input
    if not path_samples:
        raise AttributeError('Invalid --input (-i)')

    # ------ init
    #X, Y, class_names, fvector_labels, folds, samples = prepare_data_crossvalidation_given_split(path_samples)
    X_train, X_test, Y_train, Y_test, class_names, fvector_labels, folds, samples_train, samples_test = prepare_data_gridCrossvalidation(path_samples)

    pipe = []

    scaler = preprocessing.RobustScaler()
    pipe.append(('scaler', scaler))

    fselection_model = feature_selection(settings.feature_selection, settings.processors)
    if fselection_model:
        pipe.append(('feature_selection', fselection_model))

    from sklearn.model_selection import GridSearchCV

    classifiers = spawn_classifiers()

    for classfier_name, classifier in classifiers:

        params = spawn_parameters(classfier_name, False)

        print('-----------------------')
        print('Name:', classfier_name)
        print('Params', params)

        try:
            grid = GridSearchCV(estimator=classifier, param_grid=params, cv=folds) #TODO: score
            pipe.append(('grid_' + classfier_name, grid))

            classifier = Pipeline(pipe)
            clf = classifier.fit(X_train, Y_train)

            print("Best-Stimator", classifier.named_steps['grid_' + classfier_name].best_estimator_)
            print("Best-Params", classifier.named_steps['grid_' + classfier_name].best_params_)
            print("Best-Score", classifier.named_steps['grid_' + classfier_name].best_score_)
            #print "CV-Result", classifier.named_steps['grid_' + classfier_name].cv_results_

            best_classifier = classifier.named_steps['grid_' + classfier_name].best_estimator_
            #Pass parameters and fit?: best_classifier.fit(X_train, Y_train)

            predicted = best_classifier.predict(X_test)

            print(classification_report(Y_test, predicted))
            print("Overall Accuracy:", round(accuracy_score(Y_test, predicted), 2))
            print
        except Exception as details:
            print(" *** Error running GridSearchCV: ", details)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)


def main_votingCrossvalidation(options, arguments):

    # ------ Read input options and overwrite settings when redundant
    path_samples = options.input
    if not path_samples:
        raise AttributeError('Invalid --input (-i)')

    # ------ init
    X, Y, class_names, fvector_labels, folds, samples = prepare_data_crossvalidation_given_split(path_samples)
    #X_train, X_test, Y_train, Y_test, class_names, fvector_labels, folds, samples_train, samples_test = prepare_data_gridCrossvalidation

    pipe = []

    scaler = preprocessing.RobustScaler()
    pipe.append(('scaler', scaler))

    fselection_model = feature_selection(settings.feature_selection, settings.processors)
    if fselection_model:
        pipe.append(('feature_selection', fselection_model))

    from sklearn.model_selection import GridSearchCV
    from sklearn.ensemble import VotingClassifier

    params = spawn_parameters()
    estimators = spawn_classifiers()

    eclf = VotingClassifier(estimators=estimators, voting='soft', n_jobs=settings.processors)

    grid = GridSearchCV(estimator=eclf, param_grid=params, cv=folds, return_train_score=True, n_jobs=settings.processors)
    pipe.append(('grid', grid))

    classifier = Pipeline(pipe)
    clf = classifier.fit(X, Y)

    print("Best-Stimator", classifier.named_steps['grid'].best_estimator_)
    print("Best-Params", classifier.named_steps['grid'].best_params_)
    print("Best-Score", classifier.named_steps['grid'].best_score_)
    print("CV-Result", classifier.named_steps['grid'].cv_results_)

    #holdout(classifier, X_test, Y_test)


def main_ensamble(options, arguments):

    # ------ Read input options and overwrite settings when redundant
    path_samples = options.input
    if not path_samples:
        raise AttributeError('Invalid --input (-i)')

    # ------ init
    X_train, Y_train, class_names, fvector_labels, samples = prepare_data_crossvalidation('../results/testprobs-all.csv')
    X_test, Y_test, class_names, fvector_labels, samples = prepare_data_crossvalidation('../results/validationprobs-all_probsonly.csv')


    # ------ Preprocess data
    X_train = np.asarray(X_train)
    Y_train = np.asarray(Y_train)
    X_test = np.asarray(X_test)
    Y_test = np.asarray(Y_test)
    std_scale = preprocessing.RobustScaler().fit(X_train) # StandardScaler --- RobustScaler
    X_train = std_scale.transform(X_train)
    X_test = std_scale.transform(X_test)

    # ------ Build classifier
    classifier = spawn_classifier()

    #  ------ Feature selection
    fselection_model = feature_selection(settings.feature_selection, settings.processors)
    if fselection_model:
        classifier = Pipeline([('feature_selection', fselection_model), ('classification', classifier)])

    # ------ Train and Test holdout
    classifier.fit(X_train, Y_train)
    predicted = classifier.predict(X_test)

    #------- Feature Ranking and Metrics
    print_metrics(Y_test, predicted, class_names, [class_names[get_index_relevant_class()]])

    print(classifier.coef_)
    print(classifier.intercept_)


def debug(options, arguments):

    print('--- DEBUG ----')


if __name__ == "__main__" :
    parser = OptionParser()
    for option in options:
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    if options.debug:
        debug(options, arguments)
    else:
        #main_holdout(options, arguments)
        main_crossvalidation(options, arguments)
        #main_ensamble(options, arguments)
