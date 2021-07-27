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



    for index, row in dm_rules.iterrows():
        name_set = row["antecedents"]
        name = ""
        for el in name_set:
            if name == "":
                name = el
            else:
                name = el + " AND " + name

        if name not in rules.keys():
            rules[name] = {}

        consequent = list(row["consequents"])[0]
        if consequent not in rules[name].keys():
            rules[name][consequent] = {}


            supp_ant_cons = len(semantic_feature_representation.loc[(semantic_feature_representation[name] == 1) & (semantic_feature_representation["predicted_label"] == consequent)])
            percent_present = round(supp_ant_cons / len(semantic_feature_representation), 3)
            if supp_ant_cons== 0:
                percent_correct =0.0
            else:
                percent_correct =round(len(semantic_feature_representation.loc[(semantic_feature_representation[name] == 1) & (semantic_feature_representation["predicted_label"] == consequent) & (semantic_feature_representation["classification_check"] == "Correctly classified")])/ supp_ant_cons, 3)
                    
            supp_ant = len(semantic_feature_representation.loc[(semantic_feature_representation[name] == 1) ])
            supp_cons = len((semantic_feature_representation.loc[semantic_feature_representation["predicted_label"] == consequent]))
            if supp_ant != 0:
                confidence = round(supp_ant_cons / supp_ant , 3)
            else:
                confidence = 0
            if (supp_ant != 0) and (supp_cons != 0):
                lift = round(supp_ant_cons / (supp_ant * supp_cons) , 3)
            else:
                lift = 0
            percent_present_antecedent = round(supp_ant_cons / supp_cons, 3)


            rules[name][consequent]["percent_present"] = percent_present
            rules[name][consequent]["percent_correct"] = percent_correct
            rules[name][consequent]["typicality"] = lift
            rules[name][consequent]["percent_present_antecedent"] = percent_present_antecedent

    """
    for i in range(len(dm_rules["antecedents"])):
        name_set = antecedent_list[i]
        name = ""
        for el in name_set:
            if name == "":
                name = el
            else:
                name = el + " AND " + name

        dict_rule = {}
        current_rule_info = {}

        # try to get the already existing set of info in this dict, and if it does not exist you initialize it
        try:
            dict_rule = rules[name]
        except:
            rules[name] = dict_rule

        

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
                print("current_rule_info")
                current_rule_info["percent_present"] = len(current_rule_info) \
                                                       / len(semantic_feature_representation["image_name"])
                current_rule_info["percent_correct"] = num_correct / \
                                                       (len(current_rule_info) )
                current_rule_info["typicality"] = lift_scores[i]
                current_rule_info["percent_present_antecedent"] =  len(current_rule_info) / len(semantic_feature_representation.loc[semantic_feature_representation["predicted_label"] == consequent])

            # If there is nothing in this part of the dict, there is no relevant info so we remove it
            else:
                del dict[consequent]


        if len(rules[name]) < 1:
            del rules[name]
    """

    # adds all columns that were in the semantic feature representation

    print("conceots now")
    for col in semantic_feature_representation.columns:
        if col == "image_name" or col == "true_label" or col == "predicted_label" or col == "classification_check":
            continue

        supp_ant = len(semantic_feature_representation.loc[(semantic_feature_representation[col] == 1) ])
        percent_present =  round(supp_ant / len(semantic_feature_representation), 3)
        
        supp_correct = len(semantic_feature_representation.loc[(semantic_feature_representation[col] == 1)  & (semantic_feature_representation["classification_check"] == "Correctly classified")])
        percent_correct = round(supp_correct / supp_ant, 3)
        concepts[col] = {"percent_present": percent_present, "percent_correct":percent_correct, "typicality":sf_stats[col]["cramers_value"]}

        

        # Compute concept info.
        """
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

        """
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
    #print("len modified rep", (modified_representation))
    #print("consequent", list_consequents)
    # extract rules (this method takes the longest time)
    rules, frequent_itemsets = get_rules(modified_representation, min_support_score,
                                         min_lift_score, min_confidence_score, list_antecedents=list_antecedents, list_consequents=list_consequents)
    #print("output", rules)
    rules.replace([np.inf, -np.inf], 999999, inplace=True)
    data_mining_rules = rules
    #print("output2", rules)

    # filter rules, and produce list of wanted rules
    #filtered_rules = rules.loc[
    #                 rules['consequents'].apply(lambda f: False if len(
    #                     f.intersection(list_antecedents)) > 0 else True), :]
    #data_mining_rules = filtered_rules.loc[filtered_rules['antecedents'].apply(
    #    lambda f: False
    #    if len(f.intersection(list_consequents)) > 0 else True)]
    #print("output3", data_mining_rules)

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

            print("prepare to filter")
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
    #print(len(data_mining_rules_filtered))
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
    new_rep = new_rep.loc[:,~new_rep.columns.duplicated()]


    return new_rep

def filter_concept_function(x, or_queries, or_not_query):
    #print("filtering...")
    #print("x", x)
    result = 0
    if len(or_queries) > 0:
        for elem in or_queries:
            #print(type(elem))
            #print(elem)

            if type(elem) == frozenset:
                temp_res = 0
                for frozen_elem in list(elem):
                    if frozen_elem[:4] == "NOT ":
                        if x[frozen_elem[4:]]== 0:
                            temp = 1
                        elif x[frozen_elem[4:]] == 1:
                            temp = 0
                        temp_res += temp

                        #print(x[frozen_elem])
                    else:
                        temp_res += x[frozen_elem]#.iloc[0]
                if temp_res == len(list(elem)):
                    result += 1
                
                #print("frozenset")
            
            else:
                #print(x[elem])
                #print(elem)
                if elem[:4] == "NOT ":
                    if x[elem[4:]].iloc[0]== 0:
                        temp = 1
                    elif x[elem[4:]].iloc[0] == 1:
                        temp = 0
                    result += temp
                else:
                    result += x[elem].iloc[0]
    #print("filtering2")
    if len(or_not_query) > 0:
        for elem in or_not_query:
            if type(elem) == frozenset:
                for frozen_elem in list(elem):
                    if x[frozen_elem]== 0:
                        temp = 1
                    elif x[frozen_elem] == 1:
                        temp = 0
                    else:
                        print("problem")
                    result += temp

            else:


                if x[elem].iloc[0] == 0:
                    temp = 1
                elif x[elem].iloc[0] == 1:
                    temp = 0
                else:
                    print("problem")
                result += temp
    #print("fi3")
    #print("res", result)
    if result > 0:
        return 1
    else:
        return 0



def execute_image_query_pipeline(image_set_setting, return_setting="CONCEPTS_AND_RULES", binary_task_classes=None,
                                 max_antecedent_length=10, min_support_score=0.1,
                                 min_lift_score=0.1, min_confidence_score=0.1,
                                 filter_concepts="ALL", or_queries=[],
                                 desired_classes=["ALL"], class_selection=["ALL"],
                                 predicted_class=["ALL"], not_predicted_class=["ALL"],
                                 or_exclude=[], or_not_query=[], exclude_concepts=[],
                                 exclude_predicted_classes=[], exclude_true_classes=[],
                                 only_true_class=["ALL"], only_predicted_class=["ALL"],
                                 session_id=-1):
    print("image query pipeline")
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
    #print(image_list)
    if stat != status.HTTP_200_OK:
        return image_list, stat

    # 2. Make tabular representation with only these images
    print("prepare structure")
    structured_representation, semantic_features = make_tabular_representation(
        image_list, image_set_setting)
    # a copy is made here, because structured_representation gets changed in rule mining
    rep_old = structured_representation.copy(deep=True)
    #print(structured_representation)
    #print(semantic_features)


    # Filter images based on classes.
    if only_true_class != ["ALL"]:
        #print(only_true_class)
        structured_representation = structured_representation[structured_representation["true_label"] == only_true_class[0]]
    if only_predicted_class!= ["ALL"]:
        #print(only_predicted_class)
        structured_representation = structured_representation[structured_representation["predicted_label"] == only_predicted_class[0]]
    if exclude_predicted_classes != []:
        #print(exclude_predicted_classes)
        structured_representation = structured_representation[structured_representation["predicted_label"] != exclude_predicted_classes[0]]
    if exclude_true_classes != []:
        #print(exclude_true_classes)
        structured_representation = structured_representation[structured_representation["true_label"] != exclude_true_classes[0]]


    #print(structured_representation)
    # Filter images based on queried concepts.

    # Create the column of the concepts.
    #print("filter concetps")
    #print(or_not_query)
    #print(or_queries)
    if (len(or_not_query) > 0) or (len(or_queries) > 0):
        structured_representation["filter_concepts"] = structured_representation.apply(lambda x: filter_concept_function(x, or_queries, or_not_query), axis=1)
    else:
        structured_representation["filter_concepts"] = 1
    #print("filter", structured_representation["filter_concepts"] )
    return structured_representation, status.HTTP_200_OK

def or_filter(x, or_queries):
    bool_ = False
    #print(type(x))
    for query in or_queries:
        #print(query, x)
        if len(query.intersection(x)) == len(query):
            bool_ = True
    return bool_


def filter_rules(or_queries, or_not_query, or_exclude, exclude_concepts, filter_concepts, data_mining_rules_filter_length):
    #print("prepare to filter", or_queries, or_not_query, or_exclude, exclude_concepts, filter_concepts)
    #print("list t fikter", data_mining_rules_filter_length)
    
    data_mining_rules_filter_length = data_mining_rules_filter_length.loc[data_mining_rules_filter_length["antecedents"].apply(lambda x: or_filter(x, or_queries))]
    #print(len(data_mining_rules_filter_length))
    return data_mining_rules_filter_length

def create4task(x):
    if x["predicted_label"] == x["true_label"]:
        return "correctly predicted " + x["true_label"]
    else:
        return x["true_label"] + " predicted as " + x["predicted_label"]

def execute_basic_rule_mining_pipeline(image_set_setting, return_setting="CONCEPTS_AND_RULES", binary_task_classes=None,
                                 max_antecedent_length=10, min_support_score=0.1,
                                 min_lift_score=0.1, min_confidence_score=0.1,
                                 filter_concepts="ALL", or_queries=[],
                                 desired_classes=["ALL"], class_selection=["ALL"],
                                 predicted_class=["ALL"], not_predicted_class=["ALL"],
                                 or_exclude=[], or_not_query=[], exclude_concepts=[],
                                 exclude_predicted_classes=[], exclude_true_classes=[],
                                 only_true_class=["ALL"], only_predicted_class=["ALL"],
                                 session_id=-1):
    print("basic rule mining")
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
    #print(image_list)
    #print(image_list)
    if stat != status.HTTP_200_OK:
        return image_list, stat

    # 2. Make tabular representation with only these images
    structured_representation, semantic_features = make_tabular_representation(
        image_list, image_set_setting)





    if class_selection != ["ALL"]:
        print("filter classes")
        structured_representation = structured_representation.loc[structured_representation["predicted_label"].isin(class_selection)]
    # a copy is made here, because structured_representation gets changed in rule mining
    rep_old = structured_representation.copy(deep=True)

    #### Get rules.
    modified_representation, list_antecedents, list_consequents = prepare_data_mining_input(
        structured_representation)
    #print("consequent", list_consequents)
    # extract rules (this method takes the longest time)
    #print("len modified rep", (modified_representation))

    rules, frequent_itemsets = get_rules(modified_representation, min_support_score,
                                         min_lift_score, min_confidence_score, list_antecedents=list_antecedents, list_consequents=list_consequents, need_subset=False)
    #print("output", rules)
    rules.replace([np.inf, -np.inf], 999999, inplace=True)
    data_mining_rules = rules
    print("we found rullllles", len(data_mining_rules))
    #print(data_mining_rules)
    if len(data_mining_rules) > 0:
        data_mining_rules_filter_length = data_mining_rules[data_mining_rules['antecedent_len']
                                                            <= max_antecedent_length]
        print(data_mining_rules_filter_length)
        data_mining_rules_filtered =  filter_rules(or_queries, or_not_query, or_exclude, exclude_concepts, filter_concepts, data_mining_rules_filter_length)
    
    if len(data_mining_rules_filtered) > 0:
        print("nb rules fitered", len(data_mining_rules_filtered))

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
        #print((data_mining_rules_filtered))
        #return data_mining_rules_filtered, antecedents, supp_conf
        data_mining_rules = data_mining_rules_filtered
        antecendets_from_rule_mining = list(set(antecedents))
        structured_representation_rule_mining = make_tabular_representation_rule_mining_included(
            rep_old, semantic_features, antecendets_from_rule_mining)



        # 5. Run compute_statistical_tests with rule mining tabular representation
        semantic_feature_stats_dict = compute_statistical_tests_custom(
            structured_representation_rule_mining[["image_name", "true_label", "predicted_label"] + antecendets_from_rule_mining + ["classification_check"]])
        #print(semantic_feature_stats_dict)
        #print("got results here", len(data_mining_rules), len(semantic_feature_stats_dict), len(structured_representation_rule_mining[["image_name", "true_label", "predicted_label"] + antecendets_from_rule_mining + ["classification_check"]]))
        return data_mining_rules, semantic_feature_stats_dict, structured_representation_rule_mining[["image_name", "true_label", "predicted_label"] + antecendets_from_rule_mining + ["classification_check"]] #"a", "b", "c"
    else:
        print("no rule")
        return [], [], []

def get_list_concepts(image_set_setting, binary_task_classes=None,
                                 session_id=-1):
    if image_set_setting not in VALID_IMAGE_SET_SETTINGS:
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
    #print(image_list)
    #print(image_list)
    if stat != status.HTTP_200_OK:
        return image_list, stat

    # 2. Make tabular representation with only these images
    structured_representation, semantic_features = make_tabular_representation(
        image_list, image_set_setting)
    return list(structured_representation.columns)[3:-1]


def execute_basic_concept_score_pipeline(image_set_setting, return_setting="CONCEPTS_AND_RULES", binary_task_classes=None,
                                 max_antecedent_length=10, min_support_score=0.1,
                                 min_lift_score=0.1, min_confidence_score=0.1,
                                 filter_concepts="ALL", or_queries=[],
                                 desired_classes=["ALL"], class_selection=["ALL"],
                                 predicted_class=["ALL"], not_predicted_class=["ALL"],
                                 or_exclude=[], or_not_query=[], exclude_concepts=[],
                                 exclude_predicted_classes=[], exclude_true_classes=[],
                                 only_true_class=["ALL"], only_predicted_class=["ALL"],
                                 session_id=-1):
    print("execute_basic_concept_score_pipeline")
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
    #print(image_list)
    #print(image_list)
    if stat != status.HTTP_200_OK:
        return image_list, stat

    # 2. Make tabular representation with only these images
    structured_representation, semantic_features = make_tabular_representation(
        image_list, image_set_setting)
    # a copy is made here, because structured_representation gets changed in rule mining
    rep_old = structured_representation.copy(deep=True)
    #print(structured_representation)

    #### Get rules.
    #modified_representation, list_antecedents, list_consequents = prepare_data_mining_input(
    #    structured_representation)
    #print(modified_representation)
    print("prepare to filter", or_queries, or_not_query, or_exclude, exclude_concepts, filter_concepts)
    if (len(or_not_query) > 0) or (len(or_queries) > 0):
        structured_representation["filter_concepts"] = structured_representation.apply(lambda x: filter_concept_function(x, or_queries, or_not_query), axis=1)
    else:
        structured_representation["filter_concepts"] = 1
    #print(structured_representation)

    if class_selection != ["ALL"]:
        print("filter classes")
        structured_representation = structured_representation.loc[structured_representation["predicted_label"].isin(class_selection)]

    # Get the scores: support antecedent, support consequent,  and lift.
    #positive_rules = structured_representation[structured_representation["filter_concepts"] == 1]
    #print(len(positive_rules))
    list_scores = []
    list_classes = list(set(structured_representation["predicted_label"]))
    #print(list_classes)
    for class_name in list_classes:
        common_supp = len(structured_representation.loc[(structured_representation["predicted_label"] == class_name) & (structured_representation["filter_concepts"] == 1)])
        cons_sup = len(structured_representation[structured_representation["predicted_label"] == class_name])
        ant_sup = len(structured_representation[structured_representation["filter_concepts"] == 1])
        list_scores.append({"consequent_name": class_name,\
         "consequent_supp": cons_sup,\
         "antecedent_supp": ant_sup,\
         "ant_cons_supp": common_supp,\
         "lift": (common_supp)/(cons_sup * ant_sup)})
    #print(list_scores)
    semantic_feature_stats_dict = compute_statistical_tests_custom(
        structured_representation[["image_name", "true_label", "predicted_label", "filter_concepts", "classification_check"]])
    #print(semantic_feature_stats_dict)
    return list_scores, structured_representation[["image_name", "true_label", "predicted_label", "filter_concepts", "classification_check"]], semantic_feature_stats_dict


def execute_concept_mining_pipeline(image_set_setting, return_setting="CONCEPTS_AND_RULES", binary_task_classes=None,
                                 max_antecedent_length=10, min_support_score=0.1,
                                 min_lift_score=0.1, min_confidence_score=0.1,
                                 filter_concepts="ALL", or_queries=[],
                                 desired_classes=["ALL"], class_selection=["ALL"],
                                 predicted_class=["ALL"], not_predicted_class=["ALL"],
                                 or_exclude=[], or_not_query=[], exclude_concepts=[],
                                 exclude_predicted_classes=[], exclude_true_classes=[],
                                 only_true_class=["ALL"], only_predicted_class=["ALL"],
                                 session_id=-1, rule_setting="R_MINING"):
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
    #print(image_list)
    #print(image_list)
    if stat != status.HTTP_200_OK:
        return image_list, stat


    # 2. Make tabular representation with only these images
    structured_representation, semantic_features = make_tabular_representation(
        image_list, image_set_setting)


    if rule_setting == "STATS_S":
        semantic_features_dict_list =[]
        for label in list(set(structured_representation["true_label"])):
            transf_data = structured_representation.copy()
            transf_data["predicted_label"] = transf_data["predicted_label"].apply(lambda x: "others" if x != label else label)
            semantic_features_dict_list.append(compute_statistical_tests_custom(transf_data))


    elif rule_setting == "R_MINING":
        semantic_feature_stats_dict = compute_statistical_tests_custom(
        structured_representation)

    if rule_setting == "STATS_S":
        print("compute....")
        return getScoresForOneVsALL(semantic_features_dict_list, structured_representation), []
    elif rule_setting == "R_MINING":
    
        return structured_representation, semantic_feature_stats_dict


def getScoresForOneVsALL(semantic_features_dict_list, structured_representation_rule_mining):
    print("scores")
    data = {}
    for class_ in list(set(structured_representation_rule_mining["true_label"])):
        data[class_] = {}

    for class_name, class_ in zip(list(set(structured_representation_rule_mining["true_label"])), semantic_features_dict_list):
        for concept in class_.keys():

            supp_ant_cons = len(structured_representation_rule_mining.loc[(structured_representation_rule_mining[concept] == 1) & (structured_representation_rule_mining["predicted_label"] == class_name)])
            percent_present = round(supp_ant_cons / len(structured_representation_rule_mining), 3)
            if supp_ant_cons== 0:
                percent_correct =0.0
            else:
                percent_correct =round(len(structured_representation_rule_mining.loc[(structured_representation_rule_mining[concept] == 1) & (structured_representation_rule_mining["predicted_label"] == class_name) & (structured_representation_rule_mining["classification_check"] == "Correctly classified")])/ supp_ant_cons, 3)
                
            supp_ant = len(structured_representation_rule_mining.loc[(structured_representation_rule_mining[concept] == 1) ])
            supp_cons = len((structured_representation_rule_mining.loc[structured_representation_rule_mining["predicted_label"] == class_name]))
            if supp_ant != 0:
                confidence = round(supp_ant_cons / supp_ant , 3)
            else:
                confidence = 0
            if supp_cons == 0:
                percent_present_antecedent = 0.0
            else:
                percent_present_antecedent = supp_ant_cons / supp_cons

            #data[class_name][concept] = 2
            #data[class_name][concept] = (percent_present, confidence, percent_present, percent_correct)
            data[class_name][concept] = (percent_present, confidence, percent_present, percent_correct, class_[concept]["cramers_value"], percent_present_antecedent)
    return data



def execute_rule_mining_pipeline(image_set_setting, return_setting="CONCEPTS_AND_RULES", binary_task_classes=None,
                                 max_antecedent_length=10, min_support_score=0.1,
                                 min_lift_score=0.1, min_confidence_score=0.1,
                                 filter_concepts="ALL", or_queries=[],
                                 desired_classes=["ALL"], class_selection=["ALL"],
                                 predicted_class=["ALL"], not_predicted_class=["ALL"],
                                 or_exclude=[], or_not_query=[], exclude_concepts=[],
                                 exclude_predicted_classes=[], exclude_true_classes=[],
                                 only_true_class=["ALL"], only_predicted_class=["ALL"],
                                 session_id=-1, task_type="binary", rule_setting="R_MINING"):
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
    #print(image_list)
    #print(image_list)
    if stat != status.HTTP_200_OK:
        return image_list, stat


    # 2. Make tabular representation with only these images
    structured_representation, semantic_features = make_tabular_representation(
        image_list, image_set_setting)

    if task_type == "4task":
        structured_representation["predicted_label"] = structured_representation.apply(lambda x: create4task(x), axis=1)

    # a copy is made here, because structured_representation gets changed in rule mining
    rep_old = structured_representation.copy(deep=True)
    #print(semantic_features)

    # 3. Perform rule mining
    print("perform rule mining")
    data_mining_rules, antecendets_from_rule_mining, supp_conf = perform_rule_mining(
        structured_representation, max_antecedent_length, min_support_score, min_lift_score, min_confidence_score,
        filter_concepts=filter_concepts, or_queries=or_queries, or_exclude=or_exclude,
        or_not_query=or_not_query, exclude_concepts=exclude_concepts)
    #print(data_mining_rules)
    print("NB rules: ", len(data_mining_rules))

    if return_setting == "RULES_ONLY":  # if the user only wants the data mining rules
        return data_mining_rules.to_dict('records'), [], status.HTTP_200_OK

    # 4. Re-make tabular represenation with new found rule mining antecendets/concepts
    structured_representation_rule_mining = make_tabular_representation_rule_mining_included(
        rep_old, semantic_features, antecendets_from_rule_mining)

    # 5. Run compute_statistical_tests with rule mining tabular representation

    if rule_setting == "STATS_S":
        semantic_features_dict_list =[]
        for label in list(set(structured_representation_rule_mining["true_label"])):
            transf_data = structured_representation_rule_mining.copy()
            transf_data["predicted_label"] = transf_data["predicted_label"].apply(lambda x: "others" if x != label else label)
            semantic_features_dict_list.append(compute_statistical_tests_custom(transf_data))

    elif rule_setting == "R_MINING":
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
    #print("filter")
    for element_to_remove in exclude_concepts:
        if element_to_remove in filter_single_concepts:
            filter_single_concepts.remove(element_to_remove)

    for for_element_to_remove in or_exclude:
        if for_element_to_remove in filter_single_concepts:
            filter_single_concepts.remove(for_element_to_remove)
    #print(structured_representation_rule_mining)
    if task_type == "4task":
        structured_representation["true_label"] = "correctly predicted " + structured_representation["true_label"]

    if rule_setting == "STATS_S":
        print("compute....")
        return getScoresForOneVsALL(semantic_features_dict_list, structured_representation_rule_mining), [], []
    elif rule_setting == "R_MINING":
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

def string_concept_name(concept_name):
  
    if len(concept_name) == 1:
        return concept_name[0]
    else:
        name_ = ""
        for elem in concept_name:
            name_ += "("
            name_ += elem
            name_ += ") OR "

        return name_[:-4]

def post_process_concepts_rules(list_scores, struct_rep, stat_scores, list_rules, stat_rules, df_info, concept_name):

    
    # Get concept name
    concept_name_string = string_concept_name(concept_name)
    #print(concept_name_string)
    #print("name", concept_name_string)
    #print(list_scores)
    #print(struct_rep)
    #print(stat_scores)

    concept_data = []
    rule_data = {}

    # Input info queried concept.
    info_concept = {}
    info_concept["concept_name"] = concept_name_string
    info_concept["typicality"] = round(stat_scores["filter_concepts"]["cramers_value"], 3)
    info_concept["percent_present"] = round(len(struct_rep.loc[struct_rep["filter_concepts"] == 1]) / len(struct_rep), 3)
    info_concept["percent_correct"] = round(len(struct_rep.loc[(struct_rep["filter_concepts"] == 1) & (struct_rep["classification_check"] == "Correctly classified")]) / len(struct_rep.loc[struct_rep["filter_concepts"] == 1]), 3)

    concept_data.append(info_concept)

    # Input info queried rule.
    for class_ in list_scores:
        info_rule = {}
        info_rule["rule_name"] = concept_name_string + " -> " + class_["consequent_name"]
        info_rule["typicality"] = round(class_["lift"], 3)
        info_rule["percent_present"] = round(len(struct_rep.loc[(struct_rep["filter_concepts"] == 1) & (struct_rep["predicted_label"] == class_["consequent_name"])]) / len(struct_rep), 3)
        
        if len(struct_rep.loc[(struct_rep["filter_concepts"] == 1) & (struct_rep["predicted_label"] == class_["consequent_name"])]) == 0:
            info_rule["percent_correct"] = 0.0
        else:
            info_rule["percent_correct"] = round(len(struct_rep.loc[(struct_rep["filter_concepts"] == 1) & (struct_rep["predicted_label"] == class_["consequent_name"]) & (struct_rep["classification_check"] == "Correctly classified")])/ len(struct_rep.loc[(struct_rep["filter_concepts"] == 1) & (struct_rep["predicted_label"] == class_["consequent_name"])]), 3)
        if concept_name_string not in list(rule_data.keys()):
            rule_data[concept_name_string] = [info_rule]
        else:
            rule_data[concept_name_string].append(info_rule)

    # If we also found other similar rules, add them here.
    #print(list_rules, stat_rules, df_info)
    if len(list_rules) > 0:
        for class_name in stat_rules.keys():
            class_set = set(class_name.split(" AND "))
            list_rules["antecedents"] =list_rules["antecedents"].apply(lambda x: set(x))

            list_concept_names = [l["concept_name"] for l in concept_data]
            if class_name not in list_concept_names:
                info_concept = {}
                info_concept["concept_name"] = class_name
                info_concept["typicality"] = round(stat_rules[class_name]["cramers_value"], 3)
                info_concept["percent_present"] = round(len(df_info.loc[df_info[class_name] == 1]) / len(df_info), 3)
                info_concept["percent_correct"] = round(len(df_info.loc[(df_info[class_name] == 1) & (df_info["classification_check"] == "Correctly classified")]) / len(df_info.loc[df_info[class_name] == 1]), 3)

                concept_data.append(info_concept)

            info_rule = {}
            info_rule["rule_name"] = class_name + " -> " 
            #GET RULE
            rule = list_rules.loc[list_rules["antecedents"].apply(lambda x: True if len(x.intersection(class_set)) == len(class_set) else False)].iloc[0]
            consequent_name = str(list(rule['consequents'])[0])
            info_rule["rule_name"] += consequent_name
            info_rule["typicality"] = round(rule["lift"], 3)
            info_rule["percent_present"] = round(len(df_info.loc[(df_info[class_name] == 1) & (df_info["predicted_label"] == consequent_name)]) / len(df_info), 3)
            info_rule["percent_correct"] = round(len(df_info.loc[(df_info[class_name] == 1) & (df_info["predicted_label"] == consequent_name) & (df_info["classification_check"] == "Correctly classified")])/ len(df_info.loc[(df_info[class_name] == 1) & (df_info["predicted_label"] == consequent_name)]), 3)
            
            #print(list(rule_data.keys()))
            #print(class_name)
            if class_name not in list(rule_data.keys()):
                rule_data[class_name] = [info_rule]
            else:
                list_rule_names = [l["rule_name"] for l in rule_data[class_name]]
                #print(list_rule_names)
                #print(info_rule["rule_name"])
                if info_rule["rule_name"] not in list_rule_names:
                    rule_data[class_name].append(info_rule)
        # Remove ducplictes.
        for key in rule_data.keys():
            rule_data[key] = [dict(t) for t in {tuple(d.items()) for d in rule_data[key]}]
            #rule_data[key] = list(set(rule_data[key]))


    return  concept_data, rule_data
