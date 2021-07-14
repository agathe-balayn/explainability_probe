# from __future__ import annotations

import numpy as np
import pandas as pd
from django.core.exceptions import FieldError
from django.db.models import F
from numpy import imag
from rest_framework import status
from SECA_algorithm.analysis_tools import get_rules, prepare_data_mining_input
from sklearn.feature_extraction import image

from .models import Annotations, Images, Sessions
from .seca_helper_methods import (compute_statistical_tests_custom,
                                  get_exclusion_data,
                                  get_tabular_representation,
                                  get_tabular_representation_rule_mining,
                                  make_annotations, verify_all_filters,
                                  concept_is_used)
from .serializer import (AnnotationSerializer,
                         SerializerClassNotFoundException, UniversalSerializer)

VALID_IMAGE_SET_SETTINGS = set(
    ["ALL_IMAGES", "CORRECT_PREDICTION_ONLY", "WRONG_PREDICTION_ONLY", "BINARY_MATRIX_VIEW"])

VALID_RETURN_SETTINGS = set(
    ["CONCEPTS_AND_RULES", "CONCEPTS_ONLY", "RULES_ONLY"]
)


def get_concept_and_rule_classifications(semantic_feature_representation, sf_stats, dm_rules, filter_concepts="ALL",
                                         desired_classes=["ALL"], class_selection=["ALL"], predicted_class=["ALL"],
                                         not_predicted_class=["ALL"], exclude_predicted_classes=[],
                                         exclude_true_classes=[], only_true_class=["ALL"],
                                         only_predicted_class=["ALL"]):
    """

    :param semantic_feature_representation: the sfr that we will be getting the classificaations from
    :param sf_stats: semantic feature statistics, with information on the cramer values that the corresponding semantic
                     feature representation has. This is used to give the cramer values as a typicality score
    :param dm_rules: the datamined rules that we will be getting the rules extracted from. Must match the SFR layout,
                     as they will be linked together
    :param rule_names: the dm_rules may not have the same names as those shown in the semantic feature representation
                       or the sf_stats, so the rule_names should also be input with the same positions as the dm_rules
    :param filter_concepts: the concepts which we should look for specifically, if we only want to look at some and not
                            all. We add it as a list here
    :param desired_classes: If we want to only look for images which are actually certain classes, we add that
                            here as a list
    :param class_selection: if we want to look for images which are either really a certain class, or have been
                            predicted as a class, we add them here as a list.
    :param predicted_class: A list which includes all the classes which we will filter for to check if an image was
                            predicted as something in this list
    :param not_predicted_class: A list which will be used to filter for classes which are not in the list. Each set is
                                done all at once, so inputting 'table' and 'chair' will get you all classes that are
                                neither 'table' or 'chair', instead of returning everything.
    :param exclude_true_classes: A list which is there to exclude any images which are truly part of a class
    :param exclude_predicted_classes: A list, excludes all images which are predicted to be a class
    :param only_true_class: A list which excludes all images which are not truly part of the specified classes
    :param only_predicted_class: A list which excludes all images which have been predicted to be part of the
                                 specified classes
    :return: (pd.dataframe) Dataframe containing all the rules, with all the times that rule was present, and if it was
    correctly or incorrectly classified in the end, along with a decimal showing the frequency of it appearing
    (0.2 for 20%, etc) and a percent correct showing the percentage of the time that it was correctly classified

    Returns two dicts as one: the concepts and the rules seperately.

    To just get percent of the time it was correctly classified you look through the dict and look for
    - "percent_present" for percentage of the time that rule was present in the set
    - "percent_correct" for percentage of the time that the rules that were present were correctly classified
    eg: look for res[table, percent_correct] for percent correct when the feature 'table' is present
    """
    res = {}
    concepts = {}
    rules = {}
    res['concepts'] = concepts
    res['rules'] = rules

    # If filter concepts are not ALL, make the frozensets into the same format as our displayed strings
    # eg: from frozenset("table", "chair") to table AND chair
    if filter_concepts != "ALL":
        filter_names = []
        for name_set in filter_concepts:

            name = ""
            for el in name_set:
                if name == "":
                    name = el
                else:
                    name = el + " AND " + name
            filter_names.append(name)

    # This is the rule segmentation part

    antecedent_list = list(dm_rules["antecedents"])
    consequent_list = list(dm_rules["consequents"])
    lift_scores = list(dm_rules["lift"])
    for i in range(len(dm_rules["antecedents"])):
        name_set = antecedent_list[i]
        name = ""
        for el in name_set:
            if name == "":
                name = el
            else:
                name = el + " AND " + name

        dict = {}
        current_rule_info = {}

        # try to get the already existing set of info in this dict, and if it does not exist you initialize it
        try:
            dict = rules[name]
        except:
            rules[name] = dict

        # This is the most useless loop of all time but its a frozenset, so we must iterate through it with a loop.
        # This is supposed to be a list with a single element in it. We look for the semantic feature representation
        # for if the rule is present, get the related image name, and what the image really is.
        for consequent in consequent_list[i]:
            dict[consequent] = current_rule_info

            # Again, default case. If the filter inputs have not been changed we just return everything we get
            if desired_classes == ["ALL"] and class_selection == ["ALL"] and predicted_class == ["ALL"] and \
                    not_predicted_class == ["ALL"] and exclude_predicted_classes == [] and exclude_true_classes == [] \
                    and only_true_class == ["ALL"] and only_predicted_class == ["ALL"]:
                for sfr_length in range(
                        len(semantic_feature_representation[semantic_feature_representation.columns[0]])):
                    if semantic_feature_representation.loc[sfr_length, name] == 1 and \
                            semantic_feature_representation.loc[sfr_length, "predicted_label"] == consequent:
                        current_rule_info[semantic_feature_representation.loc[sfr_length, "image_name"]] = \
                            semantic_feature_representation.loc[sfr_length,
                                                                "true_label"]

            # Otherwise, we filter for everything in the same way that we filter the concepts
            else:
                for sfr_length in range(
                        len(semantic_feature_representation[semantic_feature_representation.columns[0]])):
                    if semantic_feature_representation.loc[sfr_length, name] == 1 and \
                            verify_all_filters(semantic_feature_representation=semantic_feature_representation,
                                               sfr_length=sfr_length, desired_classes=desired_classes,
                                               class_selection=class_selection,
                                               predicted_class=predicted_class,
                                               not_predicted_class=not_predicted_class,
                                               exclude_true_classes=exclude_true_classes,
                                               exclude_predicted_classes=exclude_predicted_classes,
                                               only_true_classes=only_true_class,
                                               only_predicted_classes=only_predicted_class) \
                            and semantic_feature_representation.loc[sfr_length, 'predicted_label'] == consequent:
                        current_rule_info[semantic_feature_representation.loc[sfr_length, "image_name"]] = \
                            semantic_feature_representation.loc[sfr_length,
                                                                "true_label"]

            num_correct = 0
            for e in current_rule_info:
                if current_rule_info[e] == consequent:
                    num_correct += 1

            if len(current_rule_info) > 0:
                current_rule_info["percent_present"] = len(current_rule_info) \
                                                       / len(semantic_feature_representation["image_name"])
                current_rule_info["percent_correct"] = num_correct / \
                                                       (len(current_rule_info) - 1)
                current_rule_info["typicality"] = lift_scores[i]

            # If there is nothing in this part of the dict, there is no relevant info so we remove it
            else:
                del dict[consequent]

        if len(rules[name]) < 1:
            del rules[name]

    # adds all columns that were in the semantic feature representation
    for col in semantic_feature_representation.columns:
        if col == "image_name" or col == "true_label" or col == "predicted_label" or col == "classification_check":
            continue

        # removes all columns that were the basic concepts without any joins (AND's) because the rules ensure that
        # only the rules which are relevant to us are kept, while the basic concepts are always present and should
        # be removed
        if not concept_is_used(rule_dict=rules, concept_name=col):
            continue

        present = {}
        concepts[col] = present

        # if we did not get any specific changes, the default option is to add everything into the response
        if desired_classes == ["ALL"] and class_selection == ["ALL"] and predicted_class == ["ALL"] and \
                not_predicted_class == ["ALL"] and exclude_predicted_classes == [] and exclude_true_classes == [] \
                and only_predicted_class == ["ALL"] and only_true_class == ["ALL"]:

            # looks through the results in the seen column and if there is a 1, adds the corresponding image to the
            # list, along with if they were classified correctly or not

            for i in range(len(semantic_feature_representation[semantic_feature_representation.columns[0]])):
                if semantic_feature_representation.loc[i, col] == 1:
                    present[semantic_feature_representation.loc[i, semantic_feature_representation.columns[0]]] = \
                        semantic_feature_representation.loc[i, 'classification_check']

        # otherwise, we filter for all our input filters to add in for the desired inputs
        else:
            for i in range(len(semantic_feature_representation[semantic_feature_representation.columns[0]])):

                # If the results column is a 1, and any one of the filters results in that specific class being present,
                # then we add it to the output. The only issue is that we cannot add classes specifically named ALL

                if semantic_feature_representation.loc[i, col] == 1 \
                        and verify_all_filters(semantic_feature_representation=semantic_feature_representation,
                                               sfr_length=i, desired_classes=desired_classes,
                                               class_selection=class_selection,
                                               predicted_class=predicted_class,
                                               not_predicted_class=not_predicted_class,
                                               exclude_predicted_classes=exclude_predicted_classes,
                                               exclude_true_classes=exclude_true_classes,
                                               only_predicted_classes=only_predicted_class,
                                               only_true_classes=only_true_class):
                    present[semantic_feature_representation.loc[i, semantic_feature_representation.columns[0]]] = \
                        semantic_feature_representation.loc[i,
                                                            'classification_check']

        num_correct = 0
        for e in present:
            if present[e] == "Correctly classified":
                num_correct += 1

        # Adds relevant information to the number of 'hits' compared to the total number of images, the percent of those
        # chosen images which were correctly classified, and their typicality scores
        if len(present) > 0:
            present["percent_present"] = len(present) / len(semantic_feature_representation[
                                                                semantic_feature_representation.columns[0]])
            present["percent_correct"] = num_correct / (len(present) - 1)
            present["typicality"] = sf_stats[col]["cramers_value"]

        # If there is nothing in the class, there is no relevant info so we remove it
        else:
            del concepts[col]

    return res


def retrieve_images(image_set_setting, binary_task_classes=None, session_id=0):
    '''
    :param image_set_setting: Setting for image filtering
    :type image_set_setting: str
    :param binary_task_classes: class names for matrix entry in Interface 3
    :type binary_task_classes: List
    :param session_id: id for the Sessions object that we will get the images from
    :type session_id: int
    :returns: A set of image names that match the setting
    :rtype: Set
    '''
    if session_id == -1 or len(Sessions.objects.filter(id=session_id)) == 0:
        return {
                   "The given session does not exist"
               }, status.HTTP_400_BAD_REQUEST

    session = Sessions.objects.filter(id=session_id)[0]

    if image_set_setting not in VALID_IMAGE_SET_SETTINGS:
        return {
                   "The given image setting is not valid"
               }, status.HTTP_400_BAD_REQUEST
    image_list = []
    if image_set_setting == "ALL_IMAGES":
        image_list = Sessions.objects.filter(id=session_id)[0].images.values_list('id')
    elif image_set_setting == "CORRECT_PREDICTION_ONLY":
        image_list = session.images.filter(
            actual_image__exact=F('predicted_image')).values_list('id')
    elif image_set_setting == "WRONG_PREDICTION_ONLY":
        image_list = session.images.exclude(
            actual_image__exact=F('predicted_image')).values_list('id')
    elif image_set_setting == "BINARY_MATRIX_VIEW":
        if binary_task_classes is None or len(binary_task_classes) < 2:
            return {
                       "Please give two classes for a binary matrix view request"
                   }, status.HTTP_400_BAD_REQUEST
        GT = binary_task_classes[0]  # GT = ground truth
        PC = binary_task_classes[1]  # PC = predicted class
        # Get all images where actual_image = GT and predicted_image = GT
        set_one = session.images.filter(
            actual_image__iexact=GT, predicted_image__iexact=GT)
        # Get all images where actual_image = PC and predicted_image = PC
        set_two = session.images.filter(
            actual_image__iexact=PC, predicted_image__iexact=PC)

        # Get all images where actual_image = GT and predicted_image = PC
        set_three = session.images.filter(
            actual_image__iexact=GT, predicted_image__iexact=PC)

        # Get all images where actual_image = PC and predicted_image = GT
        set_four = session.images.filter(
            actual_image__iexact=PC, predicted_image__iexact=GT)

        image_list = set_one.union(
            set_two, set_three, set_four).values_list('id')
    res = []
    for i in image_list:
        res.append(i[0])
    return set(res), status.HTTP_200_OK


def make_tabular_representation(image_list, image_set_setting):
    """
    Creates a tabular representation of the images which are in the image_list. Displays the image name, the true label
    of the image, the predicted label, a showing of if the image was correctly or incorrectly classified, followed by
    all annotations in the image set with a 1 to show if that image has that annotation, and a 0 otherwise.
    :param image_list: A list of image id numbers which match the id's of the images we wish to create a representation
                       of
    :param image_set_setting: The setting of the image set, for example BINARY_MATRIX_VIEW or ALL_IMAGES. All valid
                              settings are visible at the top of this file, as VALID_IMAGE_SET_SETTINGS
    :return representation df: The resulting tabular representation dataframe
    :return unique_semantic_features: Displays all the unique semantic features that are present in the representation
            df

    """
    # get annotations related to the image_list
    annotations = Annotations.objects.all().filter(
        image_id__in=image_list)
    # get a set of all UNIQUE semantic features from the batch
    semantic_features = annotations.distinct().values_list('annotation')

    # setup the tabular representation
    structured_representation_cols = [
        'image_name', 'true_label', 'predicted_label'
    ]
    for feature in semantic_features:
        structured_representation_cols.append(feature[0])
    representation_df = pd.DataFrame(columns=structured_representation_cols)

    # Populate structured representation
    seen_images = set()
    index_dict = {}
    cur_index = 0
    for b in annotations:
        image_name = b.image_id  #
        # if we are seeing this image for the first time, we create a new row for it, with the data
        if image_name not in seen_images:
            image = Images.objects.get(id=image_name)
            true_label = image.actual_image
            predicted_label = image.predicted_image

            representation_df.loc[cur_index, 'image_name'] = Images.objects.all().filter(
                id=b.image_id)[0].image_name
            representation_df.loc[cur_index, 'true_label'] = true_label
            representation_df.loc[cur_index,
                                  'predicted_label'] = predicted_label
            representation_df.loc[cur_index, b.annotation] = 1

            seen_images.add(image_name)
            index_dict[image_name] = cur_index
            cur_index = cur_index + 1
        # if we have seen this image already, we find the row, and add new data
        else:
            df_index = index_dict[image_name]
            representation_df.loc[df_index, b.annotation] = 1

    # Its possible that for some images, there existed no annotations, so in that case,
    # we need to add a new empty row for that image

    # TODO: Ask Agathe if we need this extra for loop.
    """
        Essentially, if this for loop is included, any image that didn't have annotations will still exist in our structured representation
        but it will be a row of 0's. 
        I think this is required for the Matrix View, as these images are part of the set of images found from the combinations of GT and PC
        and therefore, including them vs not including them WILL change the %'s that we compute. 
        This also applies for the other interfaces. For now, i have not included the loop, as including it creates 143 rows in the table
        and slows down the rule mining slightly
    """
    if image_set_setting == "BINARY_MATRIX_VIEW":
        for i in image_list:
            if i not in index_dict:
                image = Images.objects.get(id=i)
                representation_df.loc[cur_index, 'image_name'] = Images.objects.all().filter(
                    id=i)[0].image_name
                representation_df.loc[cur_index,
                                      'true_label'] = image.actual_image
                representation_df.loc[cur_index,
                                      'predicted_label'] = image.predicted_image
                cur_index = cur_index + 1

    # fill empty values with 0
    representation_df = representation_df.fillna(0)
    # add classification column
    representation_df['classification_check'] = (
            representation_df['true_label'] == representation_df['predicted_label']
    )
    representation_df['classification_check'] = representation_df[
        'classification_check'].map({
        True: 'Correctly classified',
        False: 'Misclassified'
    })
    unique_semantic_features = []
    #    if filtered_concepts is not "ALL":

    for s in semantic_features:
        unique_semantic_features.append(s[0])

    return representation_df, unique_semantic_features


def perform_rule_mining(structured_representation, max_antecedent_length, min_support_score, min_lift_score,
                        min_confidence_score, filter_concepts="ALL", or_queries=[], or_exclude=[],
                        or_not_query=[], exclude_concepts=[]):
    """
    This method performs rule mining using the structured representation which was given. Everything else is secondary,
    and are only tuning parameters. Rule mining is performed, and the antecedents (rules) and consequents (predictions
    from the rules) are slown, along with antecedent support, consequent support, confidence score, lift score,
    leverage and conviction of the rules are displayed. This is displayed in the first return, while the second return
    displays the names of the rules which were created/found.

    The final return only returns a list of the support and confidence scores of each rule which was found. This is not
    used anywhere else in the rule mining pipeline and is only used in the Explore tab on frontend. The query method
    does not return this value, and for the most part can be ignored.

    :param structured_representation: The tabular representation of all the images, their predicted/actual classes,
                                      their annotations, etc. An example of a method used to create this is the
                                      make_tabular_representation method
    :param max_antecedent_length: The maximum amount of rules that can be chained  together - for example a rule table
                                  AND 'chair AND bench' would be an antecedent length of 3.
    :param min_support_score: The minimum support score that a rule would need to have to be displayed in this output
    :param min_lift_score: The minumum lift score that a rule would need to have to be displayed here
    :param min_confidence_score: The minimum confidence score that a rule would need to have to be displayed here
    :param filter_concepts: The specific concepts that would be kept in the resulting table after rule mining is run.
                            eg: if filter concepts included only ["window", "bed AND table"] - then only the rules window
                            and bed AND table would be included in the final result.
    :param or_queries: All rules which include any of the concepts entered here would be included in the final result,
                       and nothing else. eg: or_query = ["window AND chair"], then the rules included would include only
                       - "window AND chair", "window AND chair AND table", "window AND chair AND bed", etc
    :param or_exclude: All rules which are a superset of any of the sets in this array will be excluded from the final
                       resulting table, regardless of if it was added by any of the other parameters.
    :param or_not_query: All rules which are NOT a superset of any of the concepts in this array will be included in the
                         final resulting table. or_not_query = ["bed"] results in the rules "table", "chair", etc etc,
                         but will not include anything including 'bed' unless it is included from any of the other
                         inclusion parameters
    :param exclude_concepts: Excludes all rules which are part of this array exactly. Exluding 'table' will not exclude
                             'table AND chair'. That is for the or_exclude query.
    :return data_mining_rules_filtered - A dataframe with all the rules, their predictions, the antecedent/consequent
                                         support for them, their lift scores, leverage scores and confidence scores.
    :return antecedents - A list of all the rules / antecedents that were included in the produced dataframe.
    :return supp_conf - A list of all the antecedents that were included and their support scores + confidence scores
    """
    # prepare data mining input
    modified_representation, list_antecedents, list_consequents = prepare_data_mining_input(
        structured_representation)
    # extract rules (this method takes the longest time)
    rules, frequent_itemsets = get_rules(modified_representation, min_support_score,
                                         min_lift_score, min_confidence_score)
    rules.replace([np.inf, -np.inf], 999999, inplace=True)

    # filter rules, and produce list of wanted rules
    filtered_rules = rules.loc[
                     rules['consequents'].apply(lambda f: False if len(
                         f.intersection(list_antecedents)) > 0 else True), :]
    data_mining_rules = filtered_rules.loc[filtered_rules['antecedents'].apply(
        lambda f: False
        if len(f.intersection(list_consequents)) > 0 else True)]

    # filter the data mining results based on the maximum set antecedent length, and if we need to filter any concepts
    if filter_concepts == "ALL":
        data_mining_rules_filtered = data_mining_rules[data_mining_rules['antecedent_len']
                                                       <= max_antecedent_length]
    # If filter concepts are not set to all, then they must have some relevant information in them which we will use
    # to filter the results
    else:
        data_mining_rules_filter_length = data_mining_rules[data_mining_rules['antecedent_len']
                                                            <= max_antecedent_length]

        # if there are no 'or' queries, just apply the filter concepts and ignore the rest of the calculation below
        if len(or_queries) == 0 and len(or_exclude) == 0 and len(or_not_query) == 0 and len(exclude_concepts) == 0:
            if len(filter_concepts) == 0:
                filter_overall = data_mining_rules_filter_length['antecedents']
            else:
                filter_overall = data_mining_rules_filter_length['antecedents'].isin(
                    filter_concepts)

        else:
            # Making a pandas set which we can use to filter the shortened set to include all results in which the given
            # 'or sets' are subsets of them. This is done by getting the indices of the positions, checking if the
            # current set should be included or not, and if it should, marks it with 'True'. Otherwise, it sets it
            # to 'False'.
            index_list, custom_ruleset = get_exclusion_data(or_queries, data_mining_rules_filter_length)
            or_exclusion_index_list, custom_or_exclusion_ruleset = get_exclusion_data(or_exclude,
                                                                                      data_mining_rules_filter_length)

            or_not_query_exclusion_list = []
            custom_or_not_ruleset = []
            for index in data_mining_rules_filter_length['antecedents'].index:
                set = data_mining_rules_filter_length.loc[index, 'antecedents']
                current_pos = False

                for or_sets in or_not_query:
                    if not or_sets.issubset(set):
                        custom_or_not_ruleset.append(True)
                        or_not_query_exclusion_list.append(index)
                        current_pos = True
                        break

                if not current_pos:
                    custom_or_not_ruleset.append(False)
                    or_not_query_exclusion_list.append(index)

            # filters rule set by creating the relevant boolean series
            # filters concepts we should exclude by looking for anywhere the class is not
            # filters concepts by checking if the chosen tuples are in the filter_concepts list
            filter_ruleset = pd.Series(
                custom_ruleset, index_list, dtype='bool', name="antecedents")
            filter_or_exclude_set = pd.Series(custom_or_exclusion_ruleset, or_exclusion_index_list, dtype='bool',
                                              name="antecedents")
            filter_or_not_set = pd.Series(custom_or_not_ruleset, or_not_query_exclusion_list, dtype='bool',
                                          name="antecedents")
            filter_exclusion = data_mining_rules_filter_length['antecedents'].isin(
                exclude_concepts)

            if len(filter_concepts) == 0:
                filter_overall = data_mining_rules_filter_length['antecedents'].copy()

                if len(or_queries) == 0 and len(or_not_query) == 0:
                    for index in filter_overall.index:
                        filter_overall[index] = True
                else:
                    for index in filter_overall.index:
                        filter_overall[index] = False
            else:
                filter_overall = data_mining_rules_filter_length['antecedents'].isin(
                    filter_concepts)

            # ensures that the correct indices are set to be true, only taking true where filter_ruleset and
            # filter_overall are true - the indices we should keep
            for index in filter_overall.index:
                if len(or_not_query) != 0:
                    if filter_or_not_set.at[index]:
                        filter_overall[index] = True
                    else:
                        filter_overall[index] = False

                if filter_ruleset.at[index]:
                    filter_overall[index] = True

                if filter_or_exclude_set.at[index]:
                    filter_overall[index] = False

                if filter_exclusion.at[index]:
                    filter_overall[index] = False

        data_mining_rules_filtered = data_mining_rules_filter_length[filter_overall]

    # saving the antecedents that we are using in a readable format which can be nicely sent to front end:
    # such as bed AND table, instead of frozenset("bed", "table")
    antecedents = []
    supp_conf = []
    for row in data_mining_rules_filtered.iterrows():
        concepts = list(row[1].get("antecedents"))
        antecedent = concepts[0]
        if len(concepts) > 1:
            for i in range(1, len(concepts)):
                antecedent = concepts[i] + " AND " + antecedent
        antecedents.append(antecedent)
        supp_conf.append((antecedent, row[1].get(
            "support"), row[1].get("confidence")))
    return data_mining_rules_filtered, antecedents, supp_conf


def make_tabular_representation_rule_mining_included(old_structured_representation, semantic_features,
                                                     antecedents_from_rule_mining):
    """
    Creates a new tabular representation with an extended amount of rules which were found in the rule mining process.
    :param old_structured_representation: A dataframe of the old tabular representation which the new tabular
                                          representation will be based off of.
    :param semantic_features: A list of the semantic features that were present in the old structured representation
    :param antecedents_from_rule_mining: A list of the new semantic features which were extracted from rule mining
    :return: new_rep - A new dataframe with all the information of the old structured representation, but with all the
                       rules which were found in the rule mining as additional columns.
    """
    # Rule mining has some antecedents that our old structured representation already had, so we filter them out
    new_antecedents = []
    for a in antecedents_from_rule_mining:
        if a not in semantic_features:
            new_antecedents.append(a)
    # Deleting the 'classification_check' column and will add it again later
    new_rep = old_structured_representation.drop('classification_check', 1)

    # make dictionary for each new column
    for cur_antecedent in new_antecedents:
        concepts = cur_antecedent.split(" AND ")
        col_values = []
        for row in new_rep.iterrows():
            # if this image has all concepts, then this image also gets a 1 for this new antecedent
            add_image = True
            for c in concepts:
                if (row[1].get(c) == 0):
                    add_image = False
            if add_image:
                col_values.append(1)
            else:
                col_values.append(0)
        new_rep[cur_antecedent] = col_values
    # add classification column
    new_rep['classification_check'] = (
            new_rep['true_label'] == new_rep['predicted_label']
    )
    new_rep['classification_check'] = new_rep[
        'classification_check'].map({
        True: 'Correctly classified',
        False: 'Misclassified'
    })

    return new_rep


def execute_rule_mining_pipeline(image_set_setting, return_setting="CONCEPTS_AND_RULES", binary_task_classes=None,
                                 max_antecedent_length=3, min_support_score=0.000001,
                                 min_lift_score=0.2, min_confidence_score=0.3,
                                 filter_concepts="ALL", or_queries=[],
                                 desired_classes=["ALL"], class_selection=["ALL"],
                                 predicted_class=["ALL"], not_predicted_class=["ALL"],
                                 or_exclude=[], or_not_query=[], exclude_concepts=[],
                                 exclude_predicted_classes=[], exclude_true_classes=[],
                                 only_true_class=["ALL"], only_predicted_class=["ALL"],
                                 session_id=-1):
    """
    A master method to execute the entire rule mining pipeline in one go. It takes in the following input parameters and
    runs rule mining on all the images which are in the database, using that session id, and only on the images which
    make it through all the filtration processes.
    :param image_set_setting: A string that is part of the VALID_IMAGE_SET_SETTINGS at the top of this file. Most of the
                              settings are intuitively named. Binary matrix view requires 2 desired classes
                              (actual/predicted images in the database) to be input in binary_task_classes, and displays
                              a binary matrix of the predictions and rules present in those two classes.
    :param return_setting: A string that is part of the VALID_RETURN_SETTINGS at the top of this file.
    :param binary_task_classes: A list that contains 2 classes to be used in a displayed binary matrix. Only used when
                                image_set_setting is set to BINARY_MATRIX_VIEW. If BINARY_MATRIX_VIEW is selected and
                                fewer than 2 classes are selected, and error message is returned. If BINARY_MATRIX_VIEW
                                is selected and more than 2 classes are selected, only the classes in the first two
                                positions of the list will be used
    :param max_antecedent_length: Integer. The maximum antecedent length of the outputs that will be found.
                                  'table AND chair' has an antecedent length of 2, 'table' has a length of 1, etc.
    :param min_support_score: Float. The minimum support score that must be present to be displayed in the output
    :param min_lift_score: Float. The minimum lift score that must be present to be displayed in the output
    :param min_confidence_score: Float. The minimum confidence score that must be present to be displayed in the output
    :param filter_concepts: List of strings. Shows all specific concepts that would be included in the output. If all
                            of the filtration inputs (this and everything below except for session_id) are left to
                            their default values, then all concepts/rules will be included
    :param or_queries: List of strings. All supersets of any strings present will be included in the output
    :param desired_classes: List of strings. All images which are truly a class which is in the array will be included
                            in the output
    :param class_selection: List of strings. All images which are either actually, or which are predicted as being part
                            of any of the classes in the array will be included in the output
    :param predicted_class: List of strings. All images which are predicted as being a class which is in the array will
                            be included in the output
    :param not_predicted_class: List of strings. All images which are predicted as not being part of any of the classes
                                in the array will be included in the output.
    :param or_exclude: List of strings. All concepts which are supersets of any of the concepts in the array will be
                       specifically excluded from the output, regardless of if they were said to be 'included' or not
    :param or_not_query: List of strings. Includes all concepts which are not part of the included set of queries.
                         eg: or_not = ["bed"], output = "table", "chair", "carpet", "table AND chair", etc, but no bed.
    :param exclude_concepts: List of strings. Excludes any specific concepts which are included here, but only those
                             which are listed here. excluding 'bed' will still allow "table AND bed".
    :param exclude_predicted_classes: List of strings. Excludes any images which are predicted as being any of the
                                      classes in the list.
    :param exclude_true_classes: List of strings. Excludes any images which are actually classified as any of the
                                 classes in the list.
    :param only_true_class: List of strings. While the name overlaps with the 'desired_class' input, this does not
                            retrieve any classes to add to the output, instead it excludes all classes that are not
                            part of the elements in the list
    :param only_predicted_class: List of strings. Does not retrieve any classes to add, but instead excludes all classes
                                 that are not present in this list.
    :param session_id: Integer. Gives the id of the Sessions objects that the pipeline will retrieve images for, and
                       run the rule mining algorithm for. By default it is set to -1, as if there is no specific input
                       we do not know what session to look for, and as such will by default return an error message
    :return RULES_ONLY: a dict object with all the data mined rules
    :return CONCEPTS_ONLY: a dataframe - the semantic feature representation with all the conept data

    :return CONCEPTS_AND_RULES:
     - concept_and_rule_classifications: A dict with two more dicts stored within, with keys: 'concepts' and 'rules'.
                                      'concepts' gives information on the concepts themselves, such as images which
                                      have that concept as an annotation, the percentage of the time that this concept
                                      is present and the percentage of the time that the prediction is correct.

                                      'rules' gives information on the predictions of the rules. Each value in the rules
                                      object is another dict, with different classes which the rule results in
                                      predictions of. Inside, the keys are image names, and their values are their
                                      actual classes. There is also the typicality stored here, along with the
                                      percentage of the time they are present over all images found with these settings,
                                      and the percentage of the time the predictions are correct.

                                      An example of what the dict for rules might look like looks like this:

                                      rules: {
                                            table: {
                                                bedroom: {
                                                    'image_72': 'living_room',
                                                    'image 85': 'bedroom',
                                                    'percent_present': 0.25,
                                                    'percent_correct': 0.5,
                                                    'typicality': 1.0
                                                },
                                                hospital_room: {
                                                    etc
                                                }
                                            }
                                            chair: {
                                                etc
                                            }

                                     With table being the concept, bedroom being the predicted class, living room being
                                     the predicted class for image_72, and bedroom being the predicted class for
                                     image_85
     - supp_conf: An array with all the support scores and confidence scores of the rules found
     - status: the status code of the overall request. HTTP_200_OK if everything was good, an appropriate error code
               otherwise.
    """
    if image_set_setting not in VALID_IMAGE_SET_SETTINGS or return_setting not in VALID_RETURN_SETTINGS:
        return {
                   "Non-valid input for settings"
               }, [], status.HTTP_400_BAD_REQUEST

    if session_id < 0:
        return {
                   "Non-valid input for session id"
               }, [], status.HTTP_400_BAD_REQUEST
    # 1. Get subset of images
    image_list, stat = retrieve_images(
        image_set_setting, binary_task_classes, session_id)
    if stat != status.HTTP_200_OK:
        return image_list, stat

    # 2. Make tabular representation with only these images
    structured_representation, semantic_features = make_tabular_representation(
        image_list, image_set_setting)
    # a copy is made here, because structured_representation gets changed in rule mining
    rep_old = structured_representation.copy(deep=True)

    # 3. Perform rule mining
    data_mining_rules, antecendets_from_rule_mining, supp_conf = perform_rule_mining(
        structured_representation, max_antecedent_length, min_support_score, min_lift_score, min_confidence_score,
        filter_concepts=filter_concepts, or_queries=or_queries, or_exclude=or_exclude,
        or_not_query=or_not_query, exclude_concepts=exclude_concepts)

    if return_setting == "RULES_ONLY":  # if the user only wants the data mining rules
        return data_mining_rules.to_dict('records'), [], status.HTTP_200_OK

    # 4. Re-make tabular represenation with new found rule mining antecendets/concepts
    structured_representation_rule_mining = make_tabular_representation_rule_mining_included(
        rep_old, semantic_features, antecendets_from_rule_mining)

    # 5. Run compute_statistical_tests with rule mining tabular representation
    semantic_feature_stats_dict = compute_statistical_tests_custom(
        structured_representation_rule_mining)

    if return_setting == "CONCEPTS_ONLY":  # if the user only wants the concept data
        return semantic_feature_stats_dict, [], status.HTTP_200_OK

    # 6. Compute the % values for the rules/concepts

    # Combines the concepts and the rule sets together so the concept and rule classifications can take them as a nice,
    # structured input
    filter_single_concepts = []
    if filter_concepts == "ALL" and len(or_queries) == 0:
        filter_single_concepts == "ALL"
    elif filter_concepts == "ALL":
        filter_single_concepts = or_queries
    else:
        filter_single_concepts = filter_concepts
        filter_single_concepts.extend(or_queries)

    # If we want to remove a 'base' concept, we need to make sure that it is not in this list, so we check
    # if it is in the list. If so, we remove it
    for element_to_remove in exclude_concepts:
        if element_to_remove in filter_single_concepts:
            filter_single_concepts.remove(element_to_remove)

    for for_element_to_remove in or_exclude:
        if for_element_to_remove in filter_single_concepts:
            filter_single_concepts.remove(for_element_to_remove)

    concept_and_rule_classifications = get_concept_and_rule_classifications(structured_representation_rule_mining,
                                                                            semantic_feature_stats_dict,
                                                                            data_mining_rules,
                                                                            filter_concepts=filter_single_concepts,
                                                                            desired_classes=desired_classes,
                                                                            class_selection=class_selection,
                                                                            predicted_class=predicted_class,
                                                                            not_predicted_class=not_predicted_class,
                                                                            exclude_predicted_classes=exclude_predicted_classes,
                                                                            exclude_true_classes=exclude_true_classes,
                                                                            only_true_class=only_true_class,
                                                                            only_predicted_class=only_predicted_class)

    # 7. Return everything
    return concept_and_rule_classifications, supp_conf, status.HTTP_200_OK