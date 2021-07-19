import json
import re
import numpy as np
import pandas as pd
from SECA_algorithm.analysis_tools import chi2_contingency, compute_cramers_v
from UserSECA.models import SECAUser
from django.contrib.auth.models import User
from io import StringIO
from django.db.utils import IntegrityError
from rest_framework import status
from SECAAlgo.models import Annotations, Images, Sessions, Notes
from Wiki_SECA.models import Problem_wiki


def concept_is_used(rule_dict, concept_name):
    try:
        rule_dict[concept_name]
        return True

    except:
        return False


def compute_cramers_v_no_div_by_0(chi_squared_statistic, contingency_table):
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
    if k <= 1:
        k = 2
    cramers_v = np.sqrt(chi_squared_statistic / (n * (k - 1)))
    rounded_cramers_v = np.round(cramers_v, 2)
    return rounded_cramers_v


def verify_all_filters(semantic_feature_representation, sfr_length, desired_classes, class_selection, predicted_class,
                       not_predicted_class, exclude_predicted_classes, exclude_true_classes, only_true_classes,
                       only_predicted_classes):
    """
    A method to verify if an input in the semantic feature representation makes it through all the filters. It will be
    rare that all the filters are actively doing something, instead with only a subset of the filters doing anything at
    any given moment.
    :param semantic_feature_representation: the semantic feature representation that we are checking the input of
    :param sfr_length: the index of the sfr that we want to check either the 'predicted_label' or 'true_label' of
    :param desired_classes: classes specifically made to include -> checks the true_label
    :param class_selection: classes to include, if they are included in the true_label or predicted_label
    :param predicted_class: classes to include if their predicted_label is part of the list
    :param not_predicted_class: classes to include, adds everything that is not part of a specified set of predicted
                                classes
    :param exclude_predicted_classes: excludes specified 'predicted_label's from the final result
    :param exclude_true_classes: excludes specified 'true_label's from the final result
    :param only_true_classes: excludes all classes which have 'true_label's that are not in this set
    :param only_predicted_classes: excludes all classes which have 'predicted_label's that are not present here
    :return: a boolean, true if the specific instance in the sfr has made it through all the filters, false otherwise
    """
    # I cannot make this any nicer to look at because we cannot add any spaces or anything between the lines, or the
    # entire thing would break. You could break the bool calculation into ~7 different steps instead of 1 if you really
    # wanted to I suppose

    if desired_classes == ["ALL"] and class_selection == ["ALL"] and predicted_class == ["ALL"] and \
            not_predicted_class == ["ALL"]:
        class_true_or_predicted = True
    else:
        class_true_or_predicted = ((semantic_feature_representation.loc[sfr_length, 'true_label'] in desired_classes)
                                   or (semantic_feature_representation.loc[sfr_length, 'true_label'] in class_selection
                                       or semantic_feature_representation.loc[sfr_length, 'predicted_label']
                                       in class_selection) or semantic_feature_representation.loc[
                                       sfr_length, 'predicted_label'] in predicted_class
                                   or (semantic_feature_representation.loc[sfr_length, 'predicted_label']
                                       not in not_predicted_class and not_predicted_class != ["ALL"]))

    explicit_exclusions = (semantic_feature_representation.loc[sfr_length, 'predicted_label']
                           not in exclude_predicted_classes and semantic_feature_representation.loc[
                               sfr_length, 'true_label'] not in
                           exclude_true_classes and (semantic_feature_representation.loc[sfr_length, 'true_label'] in
                                                     only_true_classes or only_true_classes == ["ALL"]) and
                           (semantic_feature_representation.loc[
                                sfr_length, 'predicted_label'] in only_predicted_classes or
                            only_predicted_classes == ["ALL"]))
    bool = class_true_or_predicted and explicit_exclusions

    return bool


def split_ands(input_set):
    """
    simply splits the 'AND' s from the given set. EG: the set including table AND chair, roof,
    window AND windowsill AND glass would become a set of frozensets, the first including (table, chair), the second
    including just rood, and the third including window, windowsill, glass
    :param input_set: A set or list including concept names you would like an equivalent frozenset of.
    :return: A list of frozensets with the elements from the input set, divided from their 'AND' s
    """
    res = []
    for set_to_split in input_set:
        divided_set = set_to_split.split(" AND ")
        fs = frozenset(divided_set)
        res.append(fs)
    return res


def get_exclusion_data(input_set, data_mining_rules_filter_length):
    index_list = []
    custom_ruleset = []
    for index in data_mining_rules_filter_length['antecedents'].index:
        set = data_mining_rules_filter_length.loc[index, 'antecedents']
        current_pos = False
        if input_set == "ALL":
            custom_ruleset.append(True)
            index_list.append(index)
            current_pos = True

        else:
            for or_sets in input_set:
                if or_sets.issubset(set):
                    custom_ruleset.append(True)
                    index_list.append(index)
                    current_pos = True
                    break

        if not current_pos:
            custom_ruleset.append(False)
            index_list.append(index)
    return index_list, custom_ruleset


def save_csv_predictions(input_data):
    """
        Given a directory name, this method saves data in that file into the database
        Args:
            input_data (str): data from csv files of format (image_name, category, predicted)
        Return:
            A string 'done' if all images are successfully saved into the database

    """
    try:
        csv = pd.read_csv(StringIO(input_data['data_set']))
        session = Sessions(name=input_data['dataset_name'])
        session.save()
        add_notes_and_wiki(input_data, session)

    except KeyError:
        return 'Either data_set or dataset_name is not present in the input data. Please make sure the input ' \
               'parameters are created properly.', status.HTTP_417_EXPECTATION_FAILED, -1

    except IntegrityError:
        return 'There was already another set with the same name, please change the name or add an additional ' \
               'identifier such as set_name_1', status.HTTP_417_EXPECTATION_FAILED, -1

    for username in input_data['username']:
        user = SECAUser.objects.filter(user=User.objects.filter(username=username)[0])[0]
        session.users.add(user)

    if "confidence" not in csv.columns:
        csv["confidence"] = "unknown"

    for i in range(len(csv[csv.columns[0]])):
        image = Images(image_name=csv.loc[i, csv.columns[0]], actual_image=csv.loc[i, csv.columns[1]],
                       predicted_image=csv.loc[i, csv.columns[2]],
                       confidence=csv.loc[i, "confidence"])
        image.save()
        session.images.add(image)
    return 'done', status.HTTP_200_OK, session.id


def add_notes_and_wiki(input_data, predict):
    for user in input_data["username"]:
        notes = Notes(content="")
        notes.save()
        notes.user.add(SECAUser.objects.filter(
            user=User.objects.filter(username=user)[0])[0])
        notes.session.add(predict)

    problem_wiki = Problem_wiki(session=predict, title=input_data['dataset_name'], intro="", image="")
    problem_wiki.save()


def link_annotations(annotation_input, session_id):
    """
        Given an input directory for the batch data, this method reads it and saves relevant information into the database
        Args:
            annotation_input (str): a string for the info of the csv file
            session_id (str): the id of the Session that the annotations will be linked to
        Return:
            a string 'saved' if all the annotations were successfully saved into the database
    """
    annotations = json.loads(annotation_input)

    for annotation_pair in annotations:
        # Identify how many annotations there are.
        keys_annotation = []
        for item in annotation_pair.keys():
            if "object" in item:
                temp = re.findall(r'\d+', item)
                res = list(map(int, temp))
                if len(res) > 0:
                    keys_annotation.append(res[0])




        # Run the code for each of them.
        for item_annotation in keys_annotation:
            if annotation_pair["object" + str(item_annotation) + "_label"] is not None:
                if ("reason" not in annotation_pair.keys()):
                    annotation_pair["reason"] = "unknown"
                elif (annotation_pair["reason"] is  None):
                    annotation_pair["reason"] = "unknown"
                if "weight" not in annotation_pair.keys():
                    annotation_pair["weight"] = 1
                elif annotation_pair["weight"] is None:
                    annotation_pair["weight"] = 1
                a1 = Annotations(image=Sessions.objects.filter(id=session_id)[0].images.filter(
                        image_name=annotation_pair["image_name"])[0],
                                    annotation=annotation_pair["object" + str(item_annotation) + "_label"],
                                    bounding_box_coordinates=annotation_pair["object" + str(item_annotation) + "_bbox"],
                                weight=annotation_pair["weight"], reason=annotation_pair["reason"])
                a1.save()

        """
        if annotation_pair["object1_label"] is not None:
            if annotation_pair["reason"] is not None:
                a1 = Annotations(image=Sessions.objects.filter(id=session_id)[0].images.filter(
                    image_name=annotation_pair["image_name"])[0],
                                 annotation=annotation_pair["object1_label"],
                                 bounding_box_coordinates=annotation_pair["object1_bbox"],
                                 weight=annotation_pair["weight"], reason=annotation_pair["reason"])
                a1.save()

            else:
                a1 = Annotations(image=Sessions.objects.filter(id=session_id)[0].images.filter(
                    image_name=annotation_pair["image_name"])[0],
                                 annotation=annotation_pair["object1_label"],
                                 bounding_box_coordinates=annotation_pair["object1_bbox"],
                                 weight=annotation_pair["weight"])
                a1.save()
        if annotation_pair["object2_label"] is not None:
            if annotation_pair["reason"] is not None:
                a2 = Annotations(image=Sessions.objects.filter(id=session_id)[0].images.filter(
                    image_name=annotation_pair["image_name"])[0],
                                 annotation=annotation_pair["object2_label"],
                                 bounding_box_coordinates=annotation_pair["object2_bbox"],
                                 weight=annotation_pair["weight"], reason=annotation_pair["reason"])
                a2.save()

            else:
                a2 = Annotations(image=Sessions.objects.filter(id=session_id)[0].images.filter(
                    image_name=annotation_pair["image_name"])[0],
                                 annotation=annotation_pair["object2_label"],
                                 bounding_box_coordinates=annotation_pair["object2_bbox"],
                                 weight=annotation_pair["weight"])
                a2.save()
            """

    return "saved"


# Method to extract tabular representation of data given batch files (this one is written by Floris)
def make_annotations(annotation):
    """
        Given a path to json file, this method reads it and returns annotation data in proper format
        Args:
            annotation (str): path to batch json file
        Returns:
            a dictionary of annotations
    """
    with open(annotation) as f:
        batch = json.load(f)

    res = {}

    for b in batch:
        keys_annotation = []
        for item in b.keys():
            if "object" in item:
                temp = re.findall(r'\d+', item)
                res = list(map(int, temp))
                if len(res) > 0:
                    keys_annotation.append(res[0])
        loc = b["image_name"]
        #f1 = b["object1_label"]
        #f2 = b["object2_label"]
        init = res.get(loc)
        if init is None:
            res[loc] = {}

        for item in keys_annotation:
            if b["object" + item_annotation + "_label"] is not None:
                res[loc].update({b["object" + item_annotation + "_label"]: 1})
        #if f1 is not None:
        #    res[loc].update({f1: 1})
        #if f2 is not None:
        #    res[loc].update({f2: 1})
    return res


# Method to extract tabular representation of data given batch files (similar to one above, this one is written by Kanish)
def get_tabular_representation(batch_file, batch_prediction_file):
    """
        Given batch file and prediction file paths, this method returns a structured representation using data from said files
        Args:
            batch_file (Str): path to batch.csv file
            batch_prediction_file (str): path to batch_prediction.csv file
        Returns:
            A pandas dataframe that represents the structured representation 
    """
    # read in batch1, which is a list of dictionaries
    with open(batch_file) as f:
        batch = json.load(f)

    # read in batch1_predictions, is a table where each row has the image name, and its ground truth + predicted label
    prediction_data = pd.read_csv(batch_prediction_file, delimiter=',')

    # get a set of all UNIQUE semantic features from the batch
    semantic_features = set()
    for b in batch:
        keys_annotation = []
        for item in b.keys():
            if "object" in item:
                temp = re.findall(r'\d+', item)
                res = list(map(int, temp))
                if len(res) > 0:
                    keys_annotation.append(res[0])
        for item in keys_annotation:
            if b["object" + item_annotation + "_label"] is not None:
                semantic_features.add(b["object" + item_annotation + "_label"])
        #f1 = b["object1_label"]
        #f2 = b["object2_label"]
        #if f1 is not None:
        #    semantic_features.add(f1)
        #if f2 is not None:
        #    semantic_features.add(f2)

    # setup the tabular representation
    structured_representation_cols = [
        'image_name', 'true_label', 'predicted_label'
    ]
    for feature in semantic_features:
        structured_representation_cols.append(feature)
    representation_df = pd.DataFrame(columns=structured_representation_cols)

    # Populate structured representation
    seen_images = set()
    index_dict = {}
    cur_index = 0
    for b in batch:
        image_name = b["image_name"]
        # if we are seeing this image for the first time, we create a new row for it, with the data
        if image_name not in seen_images:
            true_label = prediction_data.loc[prediction_data['image_name'] ==
                                             image_name].iloc[0]['category']
            predicted_label = prediction_data.loc[
                prediction_data['image_name'] ==
                image_name].iloc[0]['predicted']

            representation_df.loc[cur_index, 'image_name'] = image_name
            representation_df.loc[cur_index, 'true_label'] = true_label
            representation_df.loc[cur_index,
                                  'predicted_label'] = predicted_label


            keys_annotation = []
            for item in b.keys():
                if "object" in item:
                    temp = re.findall(r'\d+', item)
                    res = list(map(int, temp))
                    if len(res) > 0:
                        keys_annotation.append(res[0])
            for item in keys_annotation:
                if b["object" + item_annotation + "_label"] is not None:
                    representation_df.loc[cur_index, b["object" + item_annotation + "_label"]] = 1
                    #semantic_features.add(b["object" + item_annotation + "_label"])

            #f1 = b["object1_label"]
            #f2 = b["object2_label"]
            #if f1 is not None:
            #    representation_df.loc[cur_index, f1] = 1
            #if f2 is not None:
            #    representation_df.loc[cur_index, f2] = 1

            # update misc data structures
            seen_images.add(image_name)
            index_dict[image_name] = cur_index
            cur_index = cur_index + 1
        # if we have seen this image already, we find the row, and add new data
        else:
            df_index = index_dict[image_name]
            keys_annotation = []
            for item in b.keys():
                if "object" in item:
                    temp = re.findall(r'\d+', item)
                    res = list(map(int, temp))
                    if len(res) > 0:
                        keys_annotation.append(res[0])
            for item in keys_annotation:
                if b["object" + item_annotation + "_label"] is not None:
                    representation_df.loc[df_index, b["object" + item_annotation + "_label"]] = 1
            #f1 = b["object1_label"]
            #f2 = b["object2_label"]
            #if f1 is not None:
            #    representation_df.loc[df_index, f1] = 1
            #if f2 is not None:
            #    representation_df.loc[df_index, f2] = 1

    representation_df = representation_df.fillna(0)  # fill empty values with 0
    representation_df['classification_check'] = (
            representation_df['true_label'] == representation_df['predicted_label']
    )
    representation_df['classification_check'] = representation_df[
        'classification_check'].map({
        True: 'Correctly classified',
        False: 'Misclassified'
    })
    return representation_df


# Method to extract tabular representation of data given batch files and given a set of new antecedents
# found from rule mining (similar to one above, this one is written by Kanish)
def get_tabular_representation_rule_mining(batch_file, batch_prediction_file, antecedents_from_rule_mining):
    """
        Given batch file and prediction file paths and a list of antecedents, this method returns a structured representation using data from said files
        Args:
            batch_file (Str): path to batch.csv file
            batch_prediction_file (str): path to batch_prediction.csv file
            antecedents_from_rule_mining (list): a list of antecedents found from rule mining
        Returns:
            A pandas dataframe that represents the new structured representation which appends columns representing the new antecedents found from rule mining
    """
    # read in batch1, which is a list of dictionaries
    with open(batch_file) as f:
        batch = json.load(f)

    # read in batch1_predictions, is a table where each row has the image name, and its ground truth + predicted label
    prediction_data = pd.read_csv(batch_prediction_file, delimiter=',')

    # get a set of all UNIQUE semantic features from the batch
    semantic_features = set()
    for b in batch:
        keys_annotation = []
        for item in b.keys():
            if "object" in item:
                temp = re.findall(r'\d+', item)
                res = list(map(int, temp))
                if len(res) > 0:
                    keys_annotation.append(res[0])
        for item in keys_annotation:
            if b["object" + item_annotation + "_label"] is not None:
                semantic_features.add(b["object" + item_annotation + "_label"])

        #f1 = b["object1_label"]
        #f2 = b["object2_label"]
        #if f1 is not None:
        #    semantic_features.add(f1)
        #if f2 is not None:
        #    semantic_features.add(f2)

    # setup the tabular representation
    structured_representation_cols = [
        'image_name', 'true_label', 'predicted_label'
    ]
    for feature in semantic_features:
        structured_representation_cols.append(feature)
    representation_df = pd.DataFrame(columns=structured_representation_cols)

    # Populate structured representation
    seen_images = set()
    index_dict = {}
    cur_index = 0
    for b in batch:
        image_name = b["image_name"]
        # if we are seeing this image for the first time, we create a new row for it, with the data
        if image_name not in seen_images:
            true_label = prediction_data.loc[prediction_data['image_name'] ==
                                             image_name].iloc[0]['category']
            predicted_label = prediction_data.loc[
                prediction_data['image_name'] ==
                image_name].iloc[0]['predicted']

            representation_df.loc[cur_index, 'image_name'] = image_name
            representation_df.loc[cur_index, 'true_label'] = true_label
            representation_df.loc[cur_index,
                                  'predicted_label'] = predicted_label

            keys_annotation = []
            for item in b.keys():
                if "object" in item:
                    temp = re.findall(r'\d+', item)
                    res = list(map(int, temp))
                    if len(res) > 0:
                        keys_annotation.append(res[0])
            for item in keys_annotation:
                if b["object" + item_annotation + "_label"] is not None:
                    representation_df.loc[cur_index, b["object" + item_annotation + "_label"]] = 1
            #f1 = b["object1_label"]
            #f2 = b["object2_label"]
            #if f1 is not None:
            #    representation_df.loc[cur_index, f1] = 1
            #if f2 is not None:
            #    representation_df.loc[cur_index, f2] = 1

            # update misc data structures
            seen_images.add(image_name)
            index_dict[image_name] = cur_index
            cur_index = cur_index + 1
        # if we have seen this image already, we find the row, and add new data
        else:
            df_index = index_dict[image_name]
            keys_annotation = []
            for item in b.keys():
                if "object" in item:
                    temp = re.findall(r'\d+', item)
                    res = list(map(int, temp))
                    if len(res) > 0:
                        keys_annotation.append(res[0])
            for item in keys_annotation:
                if b["object" + item_annotation + "_label"] is not None:
                    representation_df.loc[df_index, b["object" + item_annotation + "_label"]] = 1
            #f1 = b["object1_label"]
            #f2 = b["object2_label"]
            #if f1 is not None:
            #    representation_df.loc[df_index, f1] = 1
            #if f2 is not None:
            #    representation_df.loc[df_index, f2] = 1

    representation_df = representation_df.fillna(0)  # fill empty values with 0
    new_antecedent = []
    for a in antecedents_from_rule_mining:
        if a not in semantic_features:
            new_antecedent.append(a)

    # make dictionary for each new column
    for cur_antecedent in new_antecedent:
        concepts = cur_antecedent.split(" AND ")
        col_values = []
        for row in representation_df.iterrows():
            # if this image has all concepts, then this image also gets a 1 for this new antecedent
            add_image = True
            for c in concepts:
                if (row[1].get(c) == 0):
                    add_image = False
            if add_image:
                col_values.append(1)
            else:
                col_values.append(0)
        representation_df[cur_antecedent] = col_values

    representation_df['classification_check'] = (
            representation_df['true_label'] == representation_df['predicted_label']
    )
    representation_df['classification_check'] = representation_df[
        'classification_check'].map({
        True: 'Correctly classified',
        False: 'Misclassified'
    })
    return representation_df


def compute_statistical_tests_custom(semantic_feature_representation, print_values=False):
    """
        Note this is almost identical to the compute_statistical_tests method implemented by the Delft AI Bias Detectives, however, 
        we did not want to alter it, so it was duplicated and alterered here. 
        
        Given semantic representation, this method computes and returns the cramers values for each of the features
        Args:
            semantic_feature_representation (Dataframe): the sfr to be used
            print_values (bool): boolean indicating if the computed values are to be printed or not
        Returns:
            a dictionary where key is the semantic feature, and value is another dictionary of cramer value, p_value and class_name_frequencies
    """
    semantic_feature_stats_dict = {}
    for semantic_feature in semantic_feature_representation.columns[3:-1]:
        contingency_table = pd.pivot_table(
            semantic_feature_representation,
            index=['predicted_label'],
            columns=[semantic_feature],
            aggfunc={semantic_feature: 'count'},
            fill_value=0)
        stat, p_value, dof, expected_freq = chi2_contingency(
            contingency_table)
        cramers_v_value = compute_cramers_v_no_div_by_0(stat, contingency_table)

        class_frequencies = np.round(
            contingency_table[semantic_feature][1] / np.sum(
                contingency_table[semantic_feature], axis=1),
            2)
        class_names = contingency_table[semantic_feature].index
        class_name_frequencies = ' | '.join([
            name + ': ' + str(class_frequencies[i])
            for i, name in enumerate(class_names)
        ])
        if print_values:
            print('Semantic feature:', semantic_feature,
                  '| Probably dependent:', 'p=%.3f' % p_value,
                  '| Cramér’s V:', cramers_v_value,
                  '| Class frequencies:', class_name_frequencies)
        semantic_feature_stats_dict[semantic_feature] = {
            'cramers_value': cramers_v_value,
            'p_value': p_value,
            'class_name_frequencies': class_name_frequencies
        }
    return semantic_feature_stats_dict
