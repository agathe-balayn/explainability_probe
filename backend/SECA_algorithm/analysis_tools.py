from sklearn.model_selection import train_test_split, StratifiedKFold
from scipy.stats import chi2_contingency, pointbiserialr
from mlxtend.frequent_patterns import association_rules
from mlxtend.preprocessing import TransactionEncoder
from sklearn.linear_model import LogisticRegression
from mlxtend.frequent_patterns import apriori
from .utils import plot_stacked_bar_chart
from sklearn import preprocessing
import matplotlib.pyplot as plt
from sklearn.svm import SVC
from sklearn import tree
import pandas as pd
import numpy as np
import graphviz


def fit_classifier(semantic_feature_representation,
                   significant_semantic_features=None,
                   classifier='decision-tree',
                   tree_filename='',
                   evaluate_classifier=False):
    """
        Fit a decision tree to the semantic feature representation first using 10-fold cross-validation and then train-test splits with
        varying numbers of training data. The learned tree representation of the model with the most training data is exported to a pdf file.
        Args:
            semantic_feature_representation (pd.DataFrame): contains the semantic feature representation extracted from the crowd annotations
            significant_semantic_features (list): features characterized as significant from the Chi-Square test
            classifier (str): classifier to use. An option among decision tree, linear SVM and rbf SVM
            tree_filename (str): path that the trained tree visualized will be saved
    """
    # Extracting features and labels
    if significant_semantic_features is None:
        X = semantic_feature_representation.iloc[:, 3:-1]
    else:
        X = semantic_feature_representation[significant_semantic_features]
    y = semantic_feature_representation['predicted_label']
    # Convert to binary labels
    le = preprocessing.LabelEncoder()
    le.fit(y)
    y = le.transform(y)  # male: 1, female: 0
    if classifier == 'decision-tree':
        clf = tree.DecisionTreeClassifier(random_state=0)
    elif classifier == 'svm-rbf':
        clf = SVC(kernel='rbf', random_state=0)
    elif classifier == 'svm-linear':
        clf = SVC(kernel='linear', random_state=0)
    elif classifier == 'log-regression':
        clf = LogisticRegression(random_state=0)
    if evaluate_classifier:
        # Stratified 10-fold cross-validation
        skf = StratifiedKFold(n_splits=10)
        skf.get_n_splits(X, y)
        accuracy_per_fold = []
        for train_index, test_index in skf.split(X, y):
            X_train, X_test = X.iloc[train_index, :], X.iloc[test_index, :]
            y_train, y_test = y[train_index], y[test_index]
            # Fit and predict
            clf = clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            accuracy_per_fold.append(sum(y_test == y_pred) / len(y_test) * 100)
        # 10-fold metrics
        print('Accuracies per fold:', accuracy_per_fold)
        print('Accuracy mean:', np.mean(accuracy_per_fold))
        print('Accuracy st dev:', np.std(accuracy_per_fold))
        # Train-test split with varying number of training samples
        test_set_sizes = [0.75, 0.5, 0.25, 0]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=595
        )  # Test set remains the same regardless of the training samples
        for size in test_set_sizes:
            if size == 0:
                X_train_subset = X_train
                y_train_subset = y_train
            else:
                X_train_subset, _, y_train_subset, _ = train_test_split(
                    X_train, y_train, test_size=size)
            clf = clf.fit(X_train_subset, y_train_subset)
            y_pred = clf.predict(X_test)
            print(len(y_train_subset), 'Training Samples', '| Test accuracy:',
                  sum(y_test == y_pred) / len(y_test) * 100)
        if classifier == 'svm-linear' or classifier == 'log-regression':
            # Print learned coefficients
            semantic_feature_coefficients = {}
            for feat_idx, coeffcient in enumerate(clf.coef_[0]):
                semantic_feature_coefficients[X.columns[feat_idx]] = coeffcient
            # Sort feature/coefficients according to the coefficient absolute value - magnitude of importance
            max_abs_coefficient = np.max(
                [np.abs(v) for v in semantic_feature_coefficients.values()])
            semantic_feature_coefficients = {
                k: np.round(v / max_abs_coefficient, 2)
                for k, v in sorted(
                    semantic_feature_coefficients.items(),
                    key=lambda item: np.abs(item[1] / max_abs_coefficient),
                    reverse=True)
            }
            print(classifier, 'coefficients', semantic_feature_coefficients)
    if classifier == 'decision-tree':
        # Plot decision tree learned by the model
        clf.fit(X, y)
        dot_data = tree.export_graphviz(clf,
                                        out_file=None,
                                        feature_names=X.columns,
                                        class_names=list(le.classes_),
                                        filled=True,
                                        rounded=True,
                                        special_characters=True,
                                        max_depth=5)
        graph = graphviz.Source(dot_data, filename=tree_filename, format='png')
        graph.view()
        return clf


def compute_cramers_v(chi_squared_statistic, contingency_table):
    """
        Compute the Cramér’s V statistical metric for the provided chi-squared value and contingency table.
        Args:
            chi_squared_statistic (np.float64):
            contingency_table (pd.DataFrame):
        Return:
           rounded_cramers_v (np.float64): Cramér’s V value rounded to two decimals
    """
    n = contingency_table.sum().sum()  # number of samples
    if contingency_table.shape[0] <= contingency_table.shape[1]:
        k = contingency_table.shape[
            0]  # lesser number of categories of either variable
    else:
        k = contingency_table.shape[1]
    cramers_v = np.sqrt(chi_squared_statistic / (n * (k - 1)))
    rounded_cramers_v = np.round(cramers_v, 2)
    return rounded_cramers_v


def compute_statistical_tests(semantic_feature_representation,
                              print_test_values=False,
                              representation_values='binary',
                              cramers_v_filter=0.0):
    """
        Computes the Chi-Square test to find features that are significantly related with the model predictions and the Cramér’s V measure
        to compute the strength of the association.

        Args:
            semantic_feature_representation (pd.DataFrame): contains the semantic feature representation extracted from the crowd annotations
            print_test_values (bool): option to print the results of the semantic tests
            representation_values (str): binary values referring to the presence or absence of the concept or numeric values referring to its gradient intensity
            cramers_v_filter (float): filter semantic features with a minimum value of cramers_v_filter
        Return:
           significant_semantic_features (list): features indicated as significant according to the Chi-Square test
           significant_features_cramers_values (list): corresponding Cramer's V values for the semantic featuers that were found to be salient
    """
    significant_semantic_features = []
    significant_features_cramers_values = []
    significant_pointbiserialr_corr_values = []
    for semantic_feature in semantic_feature_representation.columns[3:-1]:
        if representation_values == 'binary':
            # Chi-Squared Test
            contingency_table = pd.pivot_table(
                semantic_feature_representation,
                index=['predicted_label'],
                columns=[semantic_feature],
                aggfunc={semantic_feature: 'count'},
                fill_value=0)
            stat, p_value, dof, expected_freq = chi2_contingency(
                contingency_table)
            if p_value <= 0.05:
                cramers_v_value = compute_cramers_v(stat, contingency_table)
                if cramers_v_value >= cramers_v_filter:
                    if print_test_values:
                        class_frequencies = np.round(
                            contingency_table[semantic_feature][1] / np.sum(
                                contingency_table[semantic_feature], axis=1),
                            2)
                        class_names = contingency_table[semantic_feature].index
                        class_name_frequencies = ' | '.join([
                            name + ': ' + str(class_frequencies[i])
                            for i, name in enumerate(class_names)
                        ])
                        print('Semantic feature:', semantic_feature,
                              '| Probably dependent:', 'p=%.3f' % p_value,
                              '| Cramér’s V:', cramers_v_value,
                              '| Class frequencies:', class_name_frequencies)
                    significant_semantic_features.append(semantic_feature)
                    significant_features_cramers_values.append(cramers_v_value)
            elif p_value > 0.05 and print_test_values:
                print('Semantic feature:', semantic_feature,
                      '| Probably independent:', 'p=%.3f' % p_value,
                      '| Cramér’s V:',
                      compute_cramers_v(stat, contingency_table))
        elif representation_values == 'numeric':
            corr, p_value = pointbiserialr(
                semantic_feature_representation['predicted_label'].map({
                    'male':
                    1,
                    'female':
                    0
                }), semantic_feature_representation[semantic_feature])
            if p_value <= 0.05:
                if print_test_values:
                    print('Semantic feature:', semantic_feature,
                          '| Probably dependent:', 'p=%.3f' % p_value,
                          '| Correlation:%.2f' % corr)
                significant_semantic_features.append(semantic_feature)
                significant_pointbiserialr_corr_values.append(np.round(
                    corr, 2))
            elif p_value > 0.05 and print_test_values:
                print('Semantic feature:', semantic_feature,
                      '| Probably independent:', 'p=%.3f' % p_value,
                      '| Correlation:%.2f' % corr)
    if representation_values == 'binary':
        return significant_semantic_features, significant_features_cramers_values
    elif representation_values == 'numeric':
        return significant_semantic_features, significant_pointbiserialr_corr_values


def print_features_counts_per_prediction(semantic_feature_representation,
                                         count_filter=0,
                                         bar_chart=False):
    """
        Print the count of each semantic feature per predicted label.
        Args:
            semantic_feature_representation (pd.DataFrame): contains the semantic feature representation extracted from the crowd annotations
            count_filter (int): filters the semantic features whose total count for all classes is less that the specified integer
            bar_chart (bool): plots the counts into a stacked barchart if True
    """
    # Fix print truncation
    pd.options.display.max_colwidth = -1
    pd.options.display.max_columns = None
    pd.options.display.width = 260
    representation_pivot = semantic_feature_representation.groupby(
        [semantic_feature_representation.columns[2]]).sum()
    if count_filter > 0:
        representation_pivot = representation_pivot.loc[:,
                                                        representation_pivot.
                                                        sum(axis=0) >=
                                                        count_filter]  # Filter features that appear at least x times overall
    print(representation_pivot)
    if bar_chart:
        plot_stacked_bar_chart('Element count per predicted class',
                               representation_pivot,
                               (semantic_feature_representation.columns[2],
                                semantic_feature_representation.columns[1]))
        plt.show()
    else:
        return representation_pivot


def representation_rule_mining(semantic_feature_representation):
    """
        Computes the frequent items and generates the rules that can be extracted from them.
        Args:
            semantic_feature_representation (pd.DataFrame): contains the semantic feature representation extracted from the crowd annotations
        Return:
           data_mining_rules (pd.DataFrame): data mining rules extracted from the semantic feature representation
    """
    modified_representation, list_antecedents, list_consequents = prepare_data_mining_input(
        semantic_feature_representation)
    rules, _ = get_rules(modified_representation, 0.1, 0.2, 0.3)
    # Filter rules containing labels in antecedents and semantic features in consequents
    filtered_rules = rules.loc[
        rules['consequents'].apply(lambda f: False if len(
            f.intersection(list_antecedents)) > 0 else True), :]
    data_mining_rules = filtered_rules.loc[filtered_rules['antecedents'].apply(
        lambda f: False
        if len(f.intersection(list_consequents)) > 0 else True)]
    return data_mining_rules


def prepare_data_mining_input(semantic_feature_representation):
    """
        Convert the DataFrame structured representation into a list of lists of antecedents and consequents
        Args:
            semantic_feature_representation (pd.DataFrame): contains the semantic feature representation extracted from the crowd annotations
        Return:
           clean_list_dataset (list): features indicated as significant according to the Chi-Square test
           list_antecedents (frozenset): frozen set of antecedents
           list_consequents (frozenset): frozen set of consequents
    """
    cols_to_transform = list(semantic_feature_representation.columns[3:])
    if "classification_check" in cols_to_transform:
        cols_to_transform.remove("classification_check")
    # Replace ones with the semantic feature name
    semantic_feature_representation.loc[:, cols_to_transform] = semantic_feature_representation.loc[:,
                                                                                                    cols_to_transform] \
        .replace(1, pd.Series(semantic_feature_representation.columns, semantic_feature_representation.columns))
    cols_to_transform = cols_to_transform + ["predicted_label"]
    list_dataset = semantic_feature_representation[
        cols_to_transform].values.tolist()
    # Filter out the zeros
    clean_list_dataset = [
        list(filter(lambda a: a != 0, row)) for row in list_dataset
    ]
    list_antecedents = frozenset(cols_to_transform)
    list_consequents = frozenset(["predicted_label"])
    return clean_list_dataset, list_antecedents, list_consequents


def get_rules(semantic_feature_representation,
              min_support_score=0.75,
              min_lift_score=1.2,
              min_confidence_score=0.75):
    """
        Extract the rules and frequent item sets from the structured representation
        Args:
            semantic_feature_representation (pd.DataFrame): contains the semantic feature representation extracted from the crowd annotations
            min_support_score (float): min support score of extracted rules
            min_lift_score (float): min lift score of extracted rules
            min_confidence_score (float): min confidence score of extracted rules
        Return:
           rules (pd.DataFrame): DataFrame containing the extracted rules
           frequent_itemsets (pd.DataFrame): DataFrame containing the frequent item sets
    """
    # Get frequent item set
    te = TransactionEncoder()
    te_ary = te.fit(semantic_feature_representation).transform(
        semantic_feature_representation)
    print("starting the frequent itemsets bit")
    df = pd.DataFrame(te_ary, columns=te.columns_)
    frequent_itemsets = apriori(df,
                                min_support=min_support_score,
                                use_colnames=True)
    # frequent_itemsets.to_json('frequent_itemsets_0.json')
    # frequent_itemsets.to_csv('frequent_itemsets_0.csv', index=False)
    print("Finished extracting frequent itemsets")
    # frequent_itemsets = pd.read_json('frequent_itemsets_0.json')

    frequent_itemsets['itemsets'] = frequent_itemsets['itemsets'].apply(
        lambda x: frozenset(x))
    # Post filter the rules, for instance to use two metrics
    rules = association_rules(frequent_itemsets,
                              metric="lift",
                              min_threshold=min_lift_score)
    rules["antecedent_len"] = rules["antecedents"].apply(lambda x: len(x))
    rules = rules[(rules['antecedent_len'] >= 0)
                  & (rules['confidence'] > min_confidence_score) &
                  (rules['lift'] > min_lift_score)]
    return rules, frequent_itemsets

if __name__ == "__main__":
    print('-----All samples-----')
    structured_representation_df = pd.read_csv('./csv_files/elements.csv',
                                               delimiter=',')
    # print_features_counts_per_prediction(structured_representation_df, count_filter=2, bar_chart=False)
    significant_features = compute_statistical_tests(
        structured_representation_df,
        print_test_values=True,
        representation_values='binary')

    # fit_classifier(structured_representation_df, significant_semantic_features=significant_features, classifier='log-regression')
    # mined_rules = representation_rule_mining(structured_representation_df)
    # print(mined_rules.sort_values(by=['confidence'], ascending=False))

    # print('-----Correctly classified samples-----')
    # correctly_classified_df = structured_representation_df[structured_representation_df['classification_check'] == 'Correctly classified']
    # print('-----Misclassified samples-----')
    # misclassified_df = structured_representation_df[structured_representation_df['classification_check'] == 'Misclassified']
