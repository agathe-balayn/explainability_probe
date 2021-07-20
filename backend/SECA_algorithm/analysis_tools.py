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


from itertools import combinations
import numpy as np
import pandas as pd


def minimum_association_rules(df, metric="confidence",
                      min_threshold=0.8, support_only=False, list_consequents=[]):
    """Generates a DataFrame of association rules including the
    metrics 'score', 'confidence', and 'lift'
    Parameters
    -----------
    df : pandas DataFrame
      pandas DataFrame of frequent itemsets
      with columns ['support', 'itemsets']
    metric : string (default: 'confidence')
      Metric to evaluate if a rule is of interest.
      **Automatically set to 'support' if `support_only=True`.**
      Otherwise, supported metrics are 'support', 'confidence', 'lift',
      'leverage', and 'conviction'
      These metrics are computed as follows:
      - support(A->C) = support(A+C) [aka 'support'], range: [0, 1]
      - confidence(A->C) = support(A+C) / support(A), range: [0, 1]
      - lift(A->C) = confidence(A->C) / support(C), range: [0, inf]
      - leverage(A->C) = support(A->C) - support(A)*support(C),
        range: [-1, 1]
      - conviction = [1 - support(C)] / [1 - confidence(A->C)],
        range: [0, inf]
    min_threshold : float (default: 0.8)
      Minimal threshold for the evaluation metric,
      via the `metric` parameter,
      to decide whether a candidate rule is of interest.
    support_only : bool (default: False)
      Only computes the rule support and fills the other
      metric columns with NaNs. This is useful if:
      a) the input DataFrame is incomplete, e.g., does
      not contain support values for all rule antecedents
      and consequents
      b) you simply want to speed up the computation because
      you don't need the other metrics.
    Returns
    ----------
    pandas DataFrame with columns "antecedents" and "consequents"
      that store itemsets, plus the scoring metric columns:
      "antecedent support", "consequent support",
      "support", "confidence", "lift",
      "leverage", "conviction"
      of all rules for which
      metric(rule) >= min_threshold.
      Each entry in the "antecedents" and "consequents" columns are
      of type `frozenset`, which is a Python built-in type that
      behaves similarly to sets except that it is immutable
      (For more info, see
      https://docs.python.org/3.6/library/stdtypes.html#frozenset).
    Examples
    -----------
    For usage examples, please see
    http://rasbt.github.io/mlxtend/user_guide/frequent_patterns/association_rules/
    """

    # check for mandatory columns
    if not all(col in df.columns for col in ["support", "itemsets"]):
        raise ValueError("Dataframe needs to contain the\
                         columns 'support' and 'itemsets'")

    def conviction_helper(sAC, sA, sC):
        confidence = sAC/sA
        conviction = np.empty(confidence.shape, dtype=float)
        if not len(conviction.shape):
            conviction = conviction[np.newaxis]
            confidence = confidence[np.newaxis]
            sAC = sAC[np.newaxis]
            sA = sA[np.newaxis]
            sC = sC[np.newaxis]
        conviction[:] = np.inf
        conviction[confidence < 1.] = ((1. - sC[confidence < 1.]) /
                                       (1. - confidence[confidence < 1.]))

        return conviction

    # metrics for association rules
    metric_dict = {
        "antecedent support": lambda _, sA, __: sA,
        "consequent support": lambda _, __, sC: sC,
        "support": lambda sAC, _, __: sAC,
        "confidence": lambda sAC, sA, _: sAC/sA,
        "lift": lambda sAC, sA, sC: metric_dict["confidence"](sAC, sA, sC)/sC,
        "leverage": lambda sAC, sA, sC: metric_dict["support"](
             sAC, sA, sC) - sA*sC,
        "conviction": lambda sAC, sA, sC: conviction_helper(sAC, sA, sC)
        }

    columns_ordered = ["antecedent support", "consequent support",
                       "support",
                       "confidence", "lift",
                       "leverage", "conviction"]

    # check for metric compliance
    if support_only:
        metric = 'support'
    else:
        if metric not in metric_dict.keys():
            raise ValueError("Metric must be 'confidence' or 'lift', got '{}'"
                             .format(metric))

    # get dict of {frequent itemset} -> support
    keys = df['itemsets'].values
    values = df['support'].values
    frozenset_vect = np.vectorize(lambda x: frozenset(x))
    frequent_items_dict = dict(zip(frozenset_vect(keys), values))

    # prepare buckets to collect frequent rules
    rule_antecedents = []
    rule_consequents = []
    rule_supports = []

    # iterate over all frequent itemsets
    for k in frequent_items_dict.keys():
        
        if len(k.intersection(list_consequents)) > 0:
            #print("consequenct")
            #print("k", k)
            sAC = frequent_items_dict[k]
            # to find all possible combinations
            for idx in range(len(k)-1, 0, -1):
                #print("idx", idx)
                # of antecedent and consequent
                for c in combinations(k, r=idx):
                    #print("c", c)
                    antecedent = frozenset(c)
                    consequent = k.difference(antecedent)
                    if len(consequent.intersection(list_consequents)) > 0:
                        #print("good")

                        if support_only:
                            # support doesn't need these,
                            # hence, placeholders should suffice
                            sA = None
                            sC = None

                        else:
                            try:
                                #print("jkfjdkjg")
                                sA = frequent_items_dict[antecedent]
                                sC = frequent_items_dict[consequent]
                                #print("got sa, sc")
                            except KeyError as e:
                                s = (str(e) + 'You are likely getting this error'
                                              ' because the DataFrame is missing '
                                              ' antecedent and/or consequent '
                                              ' information.'
                                              ' You can try using the '
                                              ' `support_only=True` option')
                                raise KeyError(s)
                            # check for the threshold
                        #print("score")
                        score = metric_dict[metric](sAC, sA, sC)
                        #if score >= min_threshold:
                        rule_antecedents.append(antecedent)
                        rule_consequents.append(consequent)
                        rule_supports.append([sAC, sA, sC])

    # check if frequent rule was generated
    if not rule_supports:
        return pd.DataFrame(
            columns=["antecedents", "consequents"] + columns_ordered)

    else:
        # generate metrics
        rule_supports = np.array(rule_supports).T.astype(float)
        df_res = pd.DataFrame(
            data=list(zip(rule_antecedents, rule_consequents)),
            columns=["antecedents", "consequents"])

        if support_only:
            sAC = rule_supports[0]
            for m in columns_ordered:
                df_res[m] = np.nan
            df_res['support'] = sAC

        else:
            sAC = rule_supports[0]
            sA = rule_supports[1]
            sC = rule_supports[2]
            for m in columns_ordered:
                df_res[m] = metric_dict[m](sAC, sA, sC)

        return df_res




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
    list_consequents = frozenset(semantic_feature_representation["predicted_label"])
    #print(semantic_feature_representation)
    #print(list_antecedents)
    #print(list_consequents)
    return clean_list_dataset, list_antecedents, list_consequents


def get_rules(semantic_feature_representation,
              min_support_score=0.75,
              min_lift_score=1.2,
              min_confidence_score=0.75, list_antecedents=[], list_consequents=[]):
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
    #print(semantic_feature_representation)
    te = TransactionEncoder()
    te_ary = te.fit(semantic_feature_representation).transform(
        semantic_feature_representation)
    print("starting the frequent itemsets bit")
    df = pd.DataFrame(te_ary, columns=te.columns_)
    print("run a priori")
    frequent_itemsets = apriori(df,
                                min_support=min_support_score,
                                use_colnames=True)
    #if len(frequent_itemsets) > 10000:
    #print(frequent_itemsets)
    # Keep itemsets with labels, and a number of others.
    print("found frequent_itemsets", frequent_itemsets)
    #itemsets_labels = frequent_itemsets.loc[frequent_itemsets["itemsets"].apply(lambda f: True if ((len(
                             #f.intersection(list_consequents)) > 0) and (len(f.intersection(list_antecedents)) <0)) else False), :]
    itemsets_labels = frequent_itemsets.loc[frequent_itemsets["itemsets"].apply(lambda f: False if ( (len(f.intersection(list_consequents)) <1)) else True), :]
    other_sets = frequent_itemsets.loc[frequent_itemsets["itemsets"].apply(lambda f: False if ( (len(
                             f.intersection(list_consequents)) > 0)) else True), :]#.nlargest(min(25000, len(frequent_itemsets) - len(itemsets_labels)),'support')
    #other_sets["nb_item"] = other_sets["itemsets"].apply(lambda x: len(x))
    #other_sets = other_sets[itemsets_labels["nb_item"] < 6]
    #other_sets = other_sets[["itemsets", "support"]]
    other_sets = other_sets.loc[other_sets["itemsets"].apply(lambda x: False if len(x) > 10 else True )]

    #itemsets_labels["nb_item"] = itemsets_labels["itemsets"].apply(lambda x: len(x))
    #itemsets_labels = itemsets_labels[itemsets_labels["nb_item"] < 6]
    #itemsets_labels = itemsets_labels[["itemsets", "support"]]
    itemsets_labels = itemsets_labels.loc[itemsets_labels["itemsets"].apply(lambda x: False if len(x) > 10 else True )]


    frequent_itemsets = pd.concat([other_sets,itemsets_labels])#itemsets_labels.nlargest(min(2000, len(itemsets_labels)),'support') #pd.concat([other_sets,itemsets_labels])#frequent_itemsets.nlargest(min(20000, len(frequent_itemsets)),'support')
    
    k = 10
    while ((len(frequent_itemsets) > 50000) and (k > 4)):
        frequent_itemsets = frequent_itemsets.loc[frequent_itemsets["itemsets"].apply(lambda x: False if len(x) > k else True )]
        k = k-1
        print(k, len(frequent_itemsets))

    #frequent_itemsets = frequent_itemsets[["itemsets", "support"]]
    #print(frequent_itemsets)
    # frequent_itemsets.to_json('frequent_itemsets_0.json')
    # frequent_itemsets.to_csv('frequent_itemsets_0.csv', index=False)
    print("Finished extracting frequent itemsets")
    #print("fre ", frequent_itemsets, len(frequent_itemsets))
    # frequent_itemsets = pd.read_json('frequent_itemsets_0.json')

    frequent_itemsets['itemsets'] = frequent_itemsets['itemsets'].apply(
        lambda x: frozenset(x))
    print(frequent_itemsets)


    if len(list(list_consequents)) > 2:
        print("start rules")
        # Post filter the rules, for instance to use two metrics
        rules = association_rules(frequent_itemsets,
                                  metric="lift",
                                  min_threshold=min_lift_score)
        
        #print(list_consequents)
        #print((rules.columns))
        #print("ant", len(list_antecedents))

        if len(list_antecedents) > 0:
            rules.replace([np.inf, -np.inf], 999999, inplace=True)
            
            # filter rules, and produce list of wanted rules
            rules = rules.loc[
                             rules['consequents'].apply(lambda f: False if len(
                                 f.intersection(list_antecedents)) > 0 else True), :]
            rules = rules.loc[rules['antecedents'].apply(
                lambda f: False if len(f.intersection(list_consequents)) > 0 else True)]
            #print("output222", len(rules))
        print("WE found: " , len(rules))
    if len(list(list_consequents)) <= 2:
        """
        if len(rules) < 20:
            rules = association_rules(frequent_itemsets,
                              metric="lift",
                              min_threshold=0.000001)
            print(list_consequents)
            print(len(rules))
            #print("ant", len(list_antecedents))

            if len(list_antecedents) > 0:
                rules.replace([np.inf, -np.inf], 999999, inplace=True)
                print(rules['consequents'].apply(lambda f: len(
                                     f.intersection(list_antecedents))))
                # filter rules, and produce list of wanted rules
                rules = rules.loc[
                                 rules['consequents'].apply(lambda f: False if len(
                                     f.intersection(list_antecedents)) > 0 else True), :]
                rules = rules.loc[rules['antecedents'].apply(
                    lambda f: False if len(f.intersection(list_consequents)) > 0 else True)]
                #print("output222", len(rules))
            print("WE found: " , len(rules))
        if len(rules) < 20:
        """
        print("let's get rules")
        rules = minimum_association_rules(frequent_itemsets,
                              metric="lift",
                              min_threshold=0.01, list_consequents=list_consequents)
        #print(rules)
        rules = rules.loc[rules['consequents'].apply(lambda f: False if len(
                                     f.intersection(list_antecedents)) > 0 else True), :]
        rules = rules.loc[rules['antecedents'].apply(
                    lambda f: False if len(f.intersection(list_consequents)) > 0 else True)]
        print("we found ", len(rules), " rules")

    else:
        if len(rules) < 500:
            print("compute rules again")
            """
            frequent_itemsets = apriori(df,
                                    min_support=0.05,
                                    use_colnames=True)
            itemsets_labels = frequent_itemsets.loc[frequent_itemsets["itemsets"].apply(lambda f: False if ( (len(f.intersection(list_consequents)) <1)) else True), :]
            other_sets = frequent_itemsets.loc[frequent_itemsets["itemsets"].apply(lambda f: False if ( (len(
                                     f.intersection(list_consequents)) > 0)) else True), :]#.nlargest(min(25000, len(frequent_itemsets) - len(itemsets_labels)),'support')
            
            other_sets = other_sets.loc[other_sets["itemsets"].apply(lambda x: False if len(x) > 10 else True )]

            itemsets_labels = itemsets_labels.loc[itemsets_labels["itemsets"].apply(lambda x: False if len(x) > 10 else True )]


            frequent_itemsets = pd.concat([other_sets,itemsets_labels])#itemsets_labels.nlargest(min(2000, len(itemsets_labels)),'support') #pd.concat([other_sets,itemsets_labels])#frequent_itemsets.nlargest(min(20000, len(frequent_itemsets)),'support')
            
            k = 10
            while ((len(frequent_itemsets) > 50000) and (k > 4)):
                frequent_itemsets = frequent_itemsets.loc[frequent_itemsets["itemsets"].apply(lambda x: False if len(x) > k else True )]
                k = k-1
                print(k, len(frequent_itemsets))

            frequent_itemsets['itemsets'] = frequent_itemsets['itemsets'].apply(
                lambda x: frozenset(x))
            print(frequent_itemsets)
            """
            # Post filter the rules, for instance to use two metrics
            print("compute rules....")
            rules = association_rules(frequent_itemsets,
                                      metric="lift",
                                      min_threshold=0.05)
            if len(list_antecedents) > 0:
                rules.replace([np.inf, -np.inf], 999999, inplace=True)
                # filter rules, and produce list of wanted rules
                rules = rules.loc[
                                 rules['consequents'].apply(lambda f: False if len(
                                     f.intersection(list_antecedents)) > 0 else True), :]
                rules = rules.loc[rules['antecedents'].apply(
                    lambda f: False
                    if len(f.intersection(list_consequents)) > 0 else True)]


    rules["antecedent_len"] = rules["antecedents"].apply(lambda x: len(x))
    rules = rules[(rules['antecedent_len'] >= 0)
                  & (rules['confidence'] > min_confidence_score) &
                  (rules['lift'] > min_lift_score)]
    rules_temp = rules.copy()
    while len(rules_temp) > 500:
        print(len(rules_temp))
        min_confidence_score += 0.1
        min_lift_score += 0.1
        rules_temp = rules_temp[(rules_temp['antecedent_len'] >= 0)
                  & (rules_temp['confidence'] > min_confidence_score) &
                  (rules_temp['lift'] > min_lift_score)]
    print(len(rules_temp))
    if len(rules_temp) < 100:
        print(len(rules))
        rules_temp = rules[(rules['antecedent_len'] >= 0)
                  & (rules['confidence'] > min_confidence_score - 0.1) &
                  (rules['lift'] > min_lift_score - 0.1)]
        print("corrdcted", len(rules_temp))
        rules_temp_temp = rules_temp.copy()
        min_confidence_score = min_confidence_score - 0.1
        min_lift_score = min_lift_score - 0.1
        while len(rules_temp) > 500:
            print("hhh", len(rules_temp))
            min_confidence_score += 0.005
            min_lift_score += 0.005
            rules_temp = rules_temp[(rules_temp['antecedent_len'] >= 0)
                      & (rules_temp['confidence'] > min_confidence_score) &
                      (rules_temp['lift'] > min_lift_score)]
        if len(rules_temp) < 20:
            rules = rules_temp_temp[(rules_temp_temp['antecedent_len'] >= 0)
                  & (rules_temp_temp['confidence'] > min_confidence_score - 0.005) &
                  (rules_temp_temp['lift'] > min_lift_score - 0.005)]
        else:
            rules = rules_temp
        del rules_temp, rules_temp_temp

        if len(list(list_consequents)) <= 2:
            if len(rules) > 100:
                rules = rules.nlargest(100,'support')
        else:
            if len(rules) > 500:
                rules = rules.nlargest(500,'support')
        print("final", len(rules))

    else:
        rules = rules_temp
        #rules = rules_temp
        del rules_temp

    #if len(rules) < 20:
    #    rules = rules[(rules['antecedent_len'] >= 0)
    #              & (rules['confidence'] > 0.1) &
    #              (rules['lift'] > 0.1)]

    print("Data mining rules: ", rules)
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
