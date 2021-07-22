from __future__ import annotations
from numpy import imag
from django.db.models import F
from sklearn.feature_extraction import image
from .models import Images, Annotations, Sessions
from SECA_algorithm.analysis_tools import get_rules, prepare_data_mining_input
from .seca_helper_methods import compute_statistical_tests_custom, make_annotations, get_tabular_representation, \
    get_tabular_representation_rule_mining, split_ands
import pandas as pd
from rest_framework import status
from .serializer import UniversalSerializer, SerializerClassNotFoundException
from django.core.exceptions import FieldError
from .pipeline import execute_rule_mining_pipeline, execute_image_query_pipeline, execute_basic_rule_mining_pipeline, execute_basic_concept_score_pipeline, get_list_concepts


def query_classes(input):
    """
    Takes in any JSON string as a query of the format:
    {
        'query': class,
        include: [
            arg1: arg1_data,
            arg2: arg2_data,
            arg3: arg3_data
            ]

        'exclude': [
            arg_excl: excluded_argument1,
            arg_excl2: excluded_argument2
            ]
        etc
    }
    :param input: the input from the POST request
    :return: a JSON string of the queried db elements
    """
    to_filter = {}
    to_exclude = {}
    query_class = None
    error = False
    errors_found = {}
    for point in input:

        # essentially creating a switch statement to check all the inputs of the query, and save them appropriately
        if point == "query":
            if input[point] == "Images":
                query_class = Images
            elif input[point] == "Sessions":
                query_class = Sessions
            elif input[point] == "Annotations":
                query_class = Annotations
            continue

        elif point == "include":
            to_filter = input[point]

        elif point == "exclude":
            to_exclude = input[point]

        else:
            error = True
            errors_found[point] = input[point]

    # if the JSON input included something that was not defined by the switch statement above, it replies that
    # there we found an error
    if error:
        return {
                   "An error was encountered": errors_found
               }, status.HTTP_417_EXPECTATION_FAILED

    # If the JSON string did not actually include any class to query, we respond with an error message
    if query_class is None:
        return {
                   "A problem was encountered:": "There was no input class to query"
               }, status.HTTP_417_EXPECTATION_FAILED

    try:
        # retrieves the objects from the queried class with the following restrictions
        res = query_class.objects.filter(**to_filter).exclude(**to_exclude)

        # Serializes the filtered objects so they can be sent as JSON strings
        serializer = UniversalSerializer(list(res), query_class)
        return {'Response:': serializer.data}, status.HTTP_200_OK

    except FieldError:
        return {
                   'An exception was thrown':
                       'There is a problem with the Fields given, likely one of the '
                       'class attributes.'
               }, status.HTTP_417_EXPECTATION_FAILED

    # If the query_class attribute is set to a class that we cannot serialize (Images, Sessions, Annotations),
    # we catch the error and return this message
    except SerializerClassNotFoundException:
        return {
                   'An exception was thrown':
                       'The input query class is not valid'
               }, status.HTTP_417_EXPECTATION_FAILED

def simple_rule_search(input):
    # Execute a basic rule search simply filtered on main data filters.
    session_id = -1
    to_filter = []
    or_queries = []
    to_exclude = []
    or_exclude = []
    or_not_query = []
    binary_task_classes = []
    desired_classes = ["ALL"]
    class_selection = ["ALL"]
    predicted_class = ["ALL"]
    not_predicted_class = ["ALL"]
    exclude_predicted_class = []
    only_predicted_class = ["ALL"]
    exclude_true_class = []
    only_true_class = ["ALL"]
    image_setting = None

    # By default the settings here are the default settings we have given for the rule mining pipeline
    max_ant_length = 10
    min_support_score = 0.1
    min_lift_score = 0.1
    min_confidence_score = 0.1
    mistake_found = False
    mistakes = []
    for point in input:

        # essentially making a switch statement for all the possible inputs for the query. We cannot make a true
        # match case statement because that was introduced in python 3.10 and I believe we are running this in
        # Python 3.9.4 - Other alternatives to switch statements exist but this is the most clear to edit in the future

        if point == "image_setting":
            if input[point] == "all":
                image_setting = "ALL_IMAGES"

            elif input[point] == "correct_only":
                image_setting = "CORRECT_PREDICTION_ONLY"

            elif input[point] == "incorrect_only":
                image_setting = "WRONG_PREDICTION_ONLY"

            elif input[point] == "binary_matrix":
                image_setting = "BINARY_MATRIX_VIEW"
            continue

        elif point == "session_id":
            session_id = input[point]

        elif point == "exclude":
            to_exclude = input[point]

        elif point == "or_exclude":
            or_exclude = input[point]

        elif point == "or_not_query":
            or_not_query = input[point]

        elif point == "include":
            to_filter = input[point]

        elif point == "or_query":
            or_queries = input[point]

        elif point == "add_class":
            binary_task_classes = input[point]

        elif point == "max_antecedent_length":
            max_ant_length = input[point]

        elif point == "min_support_score":
            min_support_score = input[point]

        elif point == "min_lift_score":
            min_lift_score = input[point]

        elif point == "min_confidence_score":
            min_confidence_score = input[point]

        elif point == "true_class":
            desired_classes = input[point]

        elif point == "class_selection":
            class_selection = input[point]

        elif point == "predicted_class":
            predicted_class = input[point]

        elif point == "not_predicted_class":
            not_predicted_class = input[point]

        elif point == "exclude_predicted_class":
            exclude_predicted_class = input[point]

        elif point == "exclude_true_class":
            exclude_true_class = input[point]

        elif point == "only_true_class":
            only_true_class = input[point]

        elif point == "only_predicted_class":
            only_predicted_class = input[point]

        else:
            mistake_found = True
            mistakes.append(point)

    if image_setting is None:
        image_setting = "BINARY_MATRIX_VIEW"

    if mistake_found:
        return {
                   "a given input was invalid. Please set the following arguments into the correct format: ": mistakes
               }, status.HTTP_417_EXPECTATION_FAILED

    if session_id < 0:
        return {
            "you did not input a valid session id, there will be no information for this session"
        }, status.HTTP_417_EXPECTATION_FAILED

    try:
        
        # Create a frozenset of all the names in the queries such as 'bed AND table AND window',
        # to properly filter them out for all rule mining and such. This should be done for all the required sets.
        filtered_concepts = split_ands(to_filter)
        excluded_concepts = split_ands(to_exclude)
        or_sets = split_ands(or_queries)
        exclude_or = split_ands(or_exclude)
        or_not_divided = split_ands(or_not_query)

        # If there are no filtered concepts, set it to get all results
        if len(filtered_concepts) == 0 and len(or_sets) == 0 and len(excluded_concepts) == 0 and len(or_exclude) == 0 \
                and len(or_not_divided) == 0:
            filtered_concepts = "ALL"

        # executes the rule mining pipeline using the filtered data
        res, stat_rules, df_info = execute_basic_rule_mining_pipeline(image_set_setting=image_setting,
                                                            binary_task_classes=binary_task_classes,
                                                            max_antecedent_length=max_ant_length,
                                                            min_support_score=min_support_score,
                                                            min_lift_score=min_lift_score,
                                                            min_confidence_score=min_confidence_score,
                                                            filter_concepts=filtered_concepts, or_queries=or_sets,
                                                            desired_classes=desired_classes, or_exclude=exclude_or,
                                                            or_not_query=or_not_divided,
                                                            exclude_concepts=excluded_concepts,
                                                            class_selection=class_selection,
                                                            predicted_class=predicted_class,
                                                            not_predicted_class=not_predicted_class,
                                                            exclude_predicted_classes=exclude_predicted_class,
                                                            exclude_true_classes=exclude_true_class,
                                                            only_true_class=only_true_class,
                                                            only_predicted_class=only_predicted_class,
                                                            session_id=session_id)
        print("got results", res, stat_rules, df_info)
        return res, stat_rules, df_info
    except ValueError:
        return {
                   'There were no results for that combination in the binary matrix'
               }, status.HTTP_206_PARTIAL_CONTENT


def query_score_concepts(input):
    print("query score concepts")
    # Execute a basic rule search simply filtered on main data filters.
    session_id = -1
    to_filter = []
    or_queries = []
    to_exclude = []
    or_exclude = []
    or_not_query = []
    binary_task_classes = []
    desired_classes = ["ALL"]
    class_selection = ["ALL"]
    predicted_class = ["ALL"]
    not_predicted_class = ["ALL"]
    exclude_predicted_class = []
    only_predicted_class = ["ALL"]
    exclude_true_class = []
    only_true_class = ["ALL"]
    image_setting = None

    # By default the settings here are the default settings we have given for the rule mining pipeline
    max_ant_length = 10
    min_support_score = 0.1
    min_lift_score = 0.1
    min_confidence_score = 0.1
    mistake_found = False
    mistakes = []
    for point in input:

        # essentially making a switch statement for all the possible inputs for the query. We cannot make a true
        # match case statement because that was introduced in python 3.10 and I believe we are running this in
        # Python 3.9.4 - Other alternatives to switch statements exist but this is the most clear to edit in the future

        if point == "image_setting":
            if input[point] == "all":
                image_setting = "ALL_IMAGES"

            elif input[point] == "correct_only":
                image_setting = "CORRECT_PREDICTION_ONLY"

            elif input[point] == "incorrect_only":
                image_setting = "WRONG_PREDICTION_ONLY"

            elif input[point] == "binary_matrix":
                image_setting = "BINARY_MATRIX_VIEW"
            continue

        elif point == "session_id":
            session_id = input[point]

        elif point == "exclude":
            to_exclude = input[point]

        elif point == "or_exclude":
            or_exclude = input[point]

        elif point == "or_not_query":
            or_not_query = input[point]

        elif point == "include":
            to_filter = input[point]

        elif point == "or_query":
            or_queries = input[point]

        elif point == "add_class":
            binary_task_classes = input[point]

        elif point == "max_antecedent_length":
            max_ant_length = input[point]

        elif point == "min_support_score":
            min_support_score = input[point]

        elif point == "min_lift_score":
            min_lift_score = input[point]

        elif point == "min_confidence_score":
            min_confidence_score = input[point]

        elif point == "true_class":
            desired_classes = input[point]

        elif point == "class_selection":
            class_selection = input[point]

        elif point == "predicted_class":
            predicted_class = input[point]

        elif point == "not_predicted_class":
            not_predicted_class = input[point]

        elif point == "exclude_predicted_class":
            exclude_predicted_class = input[point]

        elif point == "exclude_true_class":
            exclude_true_class = input[point]

        elif point == "only_true_class":
            only_true_class = input[point]

        elif point == "only_predicted_class":
            only_predicted_class = input[point]

        else:
            mistake_found = True
            mistakes.append(point)
    print(mistakes)

    if image_setting is None:
        image_setting = "BINARY_MATRIX_VIEW"

    if mistake_found:
        return {
                   "a given input was invalid. Please set the following arguments into the correct format: ": mistakes
               }, status.HTTP_417_EXPECTATION_FAILED

    if session_id < 0:
        return {
            "you did not input a valid session id, there will be no information for this session"
        }, status.HTTP_417_EXPECTATION_FAILED

    try:
        
        # Create a frozenset of all the names in the queries such as 'bed AND table AND window',
        # to properly filter them out for all rule mining and such. This should be done for all the required sets.
        filtered_concepts = split_ands(to_filter)
        excluded_concepts = split_ands(to_exclude)
        or_sets = split_ands(or_queries)
        exclude_or = split_ands(or_exclude)
        or_not_divided = split_ands(or_not_query)

        # If there are no filtered concepts, set it to get all results
        if len(filtered_concepts) == 0 and len(or_sets) == 0 and len(excluded_concepts) == 0 and len(or_exclude) == 0 \
                and len(or_not_divided) == 0:
            filtered_concepts = "ALL"
        print("cmpute scores...")
        list_scores, struct_rep, stat_scores = execute_basic_concept_score_pipeline(image_set_setting=image_setting,
                                                                binary_task_classes=binary_task_classes,
                                                                max_antecedent_length=max_ant_length,
                                                                min_support_score=min_support_score,
                                                                min_lift_score=min_lift_score,
                                                                min_confidence_score=min_confidence_score,
                                                                filter_concepts=filtered_concepts, or_queries=or_sets,
                                                                desired_classes=desired_classes, or_exclude=exclude_or,
                                                                or_not_query=or_not_divided,
                                                                exclude_concepts=excluded_concepts,
                                                                class_selection=class_selection,
                                                                predicted_class=predicted_class,
                                                                not_predicted_class=not_predicted_class,
                                                                exclude_predicted_classes=exclude_predicted_class,
                                                                exclude_true_classes=exclude_true_class,
                                                                only_true_class=only_true_class,
                                                                only_predicted_class=only_predicted_class,
                                                                session_id=session_id)
        return list_scores, struct_rep, stat_scores
    except ValueError:
        return {
                   'There were no results for that combination in the binary matrix'
               }, status.HTTP_206_PARTIAL_CONTENT


def get_list_all_concepts(image_set_setting,
                                                                binary_task_classes,
                                                                session_id):
    return get_list_concepts(image_set_setting=image_set_setting,
                                                                binary_task_classes=binary_task_classes,
                                                                session_id=session_id)

def query_all_concepts_scores(input):
    l_s = []
    l_struct = []
    s_stat = []
    
    # List of concepts
    session_id = -1
    to_filter = []
    or_queries = []
    to_exclude = []
    or_exclude = []
    or_not_query = []
    binary_task_classes = []
    desired_classes = ["ALL"]
    class_selection = ["ALL"]
    predicted_class = ["ALL"]
    not_predicted_class = ["ALL"]
    exclude_predicted_class = []
    only_predicted_class = ["ALL"]
    exclude_true_class = []
    only_true_class = ["ALL"]
    image_setting = None

    # By default the settings here are the default settings we have given for the rule mining pipeline
    max_ant_length = 10
    min_support_score = 0.1
    min_lift_score = 0.1
    min_confidence_score = 0.1
    mistake_found = False
    mistakes = []
    for point in input:

        # essentially making a switch statement for all the possible inputs for the query. We cannot make a true
        # match case statement because that was introduced in python 3.10 and I believe we are running this in
        # Python 3.9.4 - Other alternatives to switch statements exist but this is the most clear to edit in the future

        if point == "IMAGE_SET_SETTING":
            if input[point] == "ALL_IMAGES":
                image_setting = "ALL_IMAGES"

            elif input[point] == "CORRECT_PREDICTION_ONLY":
                image_setting = "CORRECT_PREDICTION_ONLY"

            elif input[point] == "WRONG_PREDICTION_ONLY":
                image_setting = "WRONG_PREDICTION_ONLY"

            elif input[point] == "BINARY_MATRIX_VIEW":
                image_setting = "BINARY_MATRIX_VIEW"
            continue

        elif point == "session_id":
            session_id = input[point]

        elif point == "exclude":
            to_exclude = input[point]

        elif point == "or_exclude":
            or_exclude = input[point]

        elif point == "or_not_query":
            or_not_query = input[point]

        elif point == "include":
            to_filter = input[point]

        elif point == "or_query":
            or_queries = input[point]

        elif point == "add_class":
            binary_task_classes = input[point]

        elif point == "max_antecedent_length":
            max_ant_length = input[point]

        elif point == "min_support_score":
            min_support_score = input[point]

        elif point == "min_lift_score":
            min_lift_score = input[point]

        elif point == "min_confidence_score":
            min_confidence_score = input[point]

        elif point == "true_class":
            desired_classes = input[point]

        elif point == "class_selection":
            class_selection = input[point]

        elif point == "predicted_class":
            predicted_class = input[point]

        elif point == "not_predicted_class":
            not_predicted_class = input[point]

        elif point == "exclude_predicted_class":
            exclude_predicted_class = input[point]

        elif point == "exclude_true_class":
            exclude_true_class = input[point]

        elif point == "only_true_class":
            only_true_class = input[point]

        elif point == "only_predicted_class":
            only_predicted_class = input[point]

        else:
            mistake_found = True
            mistakes.append(point)

    if image_setting is None:
        image_setting = "BINARY_MATRIX_VIEW"
    if mistake_found:
        return {
                   "a given input was invalid. Please set the following arguments into the correct format: ": mistakes
               }, status.HTTP_417_EXPECTATION_FAILED

    if session_id < 0:
        return {
            "you did not input a valid session id, there will be no information for this session"
        }, status.HTTP_417_EXPECTATION_FAILED

    
        
    # Create a frozenset of all the names in the queries such as 'bed AND table AND window',
    # to properly filter them out for all rule mining and such. This should be done for all the required sets.
    filtered_concepts = split_ands(to_filter)
    excluded_concepts = split_ands(to_exclude)
    or_sets = split_ands(or_queries)
    exclude_or = split_ands(or_exclude)
    or_not_divided = split_ands(or_not_query)

        # If there are no filtered concepts, set it to get all results
    if len(filtered_concepts) == 0 and len(or_sets) == 0 and len(excluded_concepts) == 0 and len(or_exclude) == 0 \
                and len(or_not_divided) == 0:
        filtered_concepts = "ALL"
    list_concepts = get_list_all_concepts(image_set_setting=image_setting,
                                                                binary_task_classes=binary_task_classes,
                                                                session_id=session_id)

    print("list concpts", list_concepts)
    for i in list_concepts:
        input_info = input.copy()
        if input["IMAGE_SET_SETTING"] == "ALL_IMAGES":
            image_setting = "all"

        elif input["IMAGE_SET_SETTING"] == "CORRECT_PREDICTION_ONLY":
            image_setting = "correct_only"

        elif input["IMAGE_SET_SETTING"] == "WRONG_PREDICTION_ONLY":
            image_setting = "incorrect_only"

        elif input["IMAGE_SET_SETTING"] == "BINARY_MATRIX_VIEW":
            image_setting = "binary_matrix"
        print("concept", i)
        input_info["or_query"] = [i]
        input_info["image_setting"] = image_setting
        del input_info["IMAGE_SET_SETTING"]
        list_scores, struct_rep, stat_scores = query_score_concepts(input_info)
        #print("RESULTSSS")
        #print(i, list_scores, struct_rep, stat_scores)
        l_s.append(list_scores)
        l_struct.append(struct_rep)
        s_stat.append(stat_scores)
    return list_concepts,l_s, l_struct, s_stat


def query_rules(input):
    """
    Takes in any query with the format:
    {
        "image_setting": "binary matrix",
        "add_class": ["bathroom", "hospital_room"],
        "include": ["bed", "wall AND windowsill AND window"],
        "min_lift_score": 0.3
    }   etc

    The order is not important.
    Possible inputs are: (input type, default, what it is used for)
     - session_id -> the id of the desired session
     - image_setting -> single string, one of "all", "correct_only", "incorrect_only", "binary_matrix". If
                        left blank will default to all. Sets the pipeline to one of the following settings
     - exclude -> array of strings. Allows us to remove individual concepts from the final set
     - include -> array of strings. This looks for the concepts that we will filter for in the rule mining
     - or_query -> array of strings. This allows us to make 'or queries', meaning that all supersets including the
                   concepts in the query will be included
     - or_exclude -> array of strings. Allows us to exclude all supersets of the concepts provided
     - or_not_query -> array of strings. Adds everything that is not part of the chosen classes, but does not
                       explicitly exclude them if they are introduced by anything else
     - add_class -> array of strings. If the image setting is set to binary matrix, this will take the first two classes
                    and use them as the input to that calculation. Does nothing otherwise
     - true_class -> array of strings. Allows us to filter for only images whose true classes (not predicted classes)
                     are given here.
     - class_selection -> array of strings. Allows the user to filter for only images where the actual or predicted
                          class is one of the entered classes
     - predicted_class -> array of strings. Allows the user to filter for images which are predicted as one of the
                          entered classes
     - not_predicted_class -> array of strings. Allows the user to filter for images which are not predicted as one
                              of the entered classes, instead looking for everything that is not in the entered classes
     - exclude_predicted_class -> array of strings. Allows the user to exclude images which are predicted to be any
                                   of the specified classes
     - exclude_true_class -> array of strings. Allows the user to exclude images which are truly part of any of the
                               specified classes
     - only_true_class -> array of strings. Allows the user to filter for only images which are part of the specified
                          classes
     - only_predicted_class -> array of strings. Allows the user to filter for only  images which have been predicted
                               to be part of the specified classes
     - max_antecedent_length -> integer. Default 3. Used to set the max length for antecedents (rule combinations)
     - min_support_score -> float. Default 0.000001. Used to set min support score in pipeline
     - min_lift_score -> float. Default 0.2. Used to set min lift score in pipeline
     - min_confidence_score -> float. Default 0.3. Used to set min_confidence score in pipeline

    :param input: The incoming data from a request in a JSON format, as a python dict
    :return: The filtered rules and concepts, along with a HTTP status for if it was successful or not.
    """
    session_id = -1
    to_filter = []
    or_queries = []
    to_exclude = []
    or_exclude = []
    or_not_query = []
    binary_task_classes = []
    desired_classes = ["ALL"]
    class_selection = ["ALL"]
    predicted_class = ["ALL"]
    not_predicted_class = ["ALL"]
    exclude_predicted_class = []
    only_predicted_class = ["ALL"]
    exclude_true_class = []
    only_true_class = ["ALL"]
    image_setting = None

    # By default the settings here are the default settings we have given for the rule mining pipeline
    max_ant_length = 10
    min_support_score = 0.15
    min_lift_score = 0.01
    min_confidence_score = 0.3
    mistake_found = False
    mistakes = []
    for point in input:

        # essentially making a switch statement for all the possible inputs for the query. We cannot make a true
        # match case statement because that was introduced in python 3.10 and I believe we are running this in
        # Python 3.9.4 - Other alternatives to switch statements exist but this is the most clear to edit in the future

        if point == "image_setting":
            if input[point] == "all":
                image_setting = "ALL_IMAGES"

            elif input[point] == "correct_only":
                image_setting = "CORRECT_PREDICTION_ONLY"

            elif input[point] == "incorrect_only":
                image_setting = "WRONG_PREDICTION_ONLY"

            elif input[point] == "binary_matrix":
                image_setting = "BINARY_MATRIX_VIEW"
            continue

        elif point == "session_id":
            session_id = input[point]

        elif point == "exclude":
            to_exclude = input[point]

        elif point == "or_exclude":
            or_exclude = input[point]

        elif point == "or_not_query":
            or_not_query = input[point]

        elif point == "include":
            to_filter = input[point]

        elif point == "or_query":
            or_queries = input[point]

        elif point == "add_class":
            binary_task_classes = input[point]

        elif point == "max_antecedent_length":
            max_ant_length = input[point]

        elif point == "min_support_score":
            min_support_score = input[point]

        elif point == "min_lift_score":
            min_lift_score = input[point]

        elif point == "min_confidence_score":
            min_confidence_score = input[point]

        elif point == "true_class":
            desired_classes = input[point]

        elif point == "class_selection":
            class_selection = input[point]

        elif point == "predicted_class":
            predicted_class = input[point]

        elif point == "not_predicted_class":
            not_predicted_class = input[point]

        elif point == "exclude_predicted_class":
            exclude_predicted_class = input[point]

        elif point == "exclude_true_class":
            exclude_true_class = input[point]

        elif point == "only_true_class":
            only_true_class = input[point]

        elif point == "only_predicted_class":
            only_predicted_class = input[point]

        else:
            mistake_found = True
            mistakes.append(point)

    if image_setting is None:
        image_setting = "BINARY_MATRIX_VIEW"

    if mistake_found:
        return {
                   "a given input was invalid. Please set the following arguments into the correct format: ": mistakes
               }, status.HTTP_417_EXPECTATION_FAILED

    if session_id < 0:
        return {
            "you did not input a valid session id, there will be no information for this session"
        }, status.HTTP_417_EXPECTATION_FAILED

    try:
        # Create a frozenset of all the names in the queries such as 'bed AND table AND window',
        # to properly filter them out for all rule mining and such. This should be done for all the required sets.
        filtered_concepts = split_ands(to_filter)
        excluded_concepts = split_ands(to_exclude)
        or_sets = split_ands(or_queries)
        exclude_or = split_ands(or_exclude)
        or_not_divided = split_ands(or_not_query)

        # If there are no filtered concepts, set it to get all results
        if len(filtered_concepts) == 0 and len(or_sets) == 0 and len(excluded_concepts) == 0 and len(or_exclude) == 0 \
                and len(or_not_divided) == 0:
            filtered_concepts = "ALL"

        # executes the rule mining pipeline using the filtered data
        res, supp_conf, stat = execute_rule_mining_pipeline(image_set_setting=image_setting,
                                                            binary_task_classes=binary_task_classes,
                                                            max_antecedent_length=max_ant_length,
                                                            min_support_score=min_support_score,
                                                            min_lift_score=min_lift_score,
                                                            min_confidence_score=min_confidence_score,
                                                            filter_concepts=filtered_concepts, or_queries=or_sets,
                                                            desired_classes=desired_classes, or_exclude=exclude_or,
                                                            or_not_query=or_not_divided,
                                                            exclude_concepts=excluded_concepts,
                                                            class_selection=class_selection,
                                                            predicted_class=predicted_class,
                                                            not_predicted_class=not_predicted_class,
                                                            exclude_predicted_classes=exclude_predicted_class,
                                                            exclude_true_classes=exclude_true_class,
                                                            only_true_class=only_true_class,
                                                            only_predicted_class=only_predicted_class,
                                                            session_id=session_id)
        return res, stat

    # If there is a value error thrown, it will catch it. Currently there are no errors that would realistically occur
    # however, but if we find cases where we want to catch an error here we can add them below
    except ValueError:
        return {
                   'There were no results for that combination in the binary matrix'
               }, status.HTTP_206_PARTIAL_CONTENT



def query_images(input):
    session_id = -1
    to_filter = []
    or_queries = []
    to_exclude = []
    or_exclude = []
    or_not_query = []
    binary_task_classes = []
    desired_classes = ["ALL"]
    class_selection = ["ALL"]
    predicted_class = ["ALL"]
    not_predicted_class = ["ALL"]
    exclude_predicted_class = []
    only_predicted_class = ["ALL"]
    exclude_true_class = []
    only_true_class = ["ALL"]
    image_setting = None

    # By default the settings here are the default settings we have given for the rule mining pipeline
    max_ant_length = 3
    min_support_score = 0.000001
    min_lift_score = 0.2
    min_confidence_score = 0.3
    mistake_found = False
    mistakes = []
    for point in input:

        # essentially making a switch statement for all the possible inputs for the query. We cannot make a true
        # match case statement because that was introduced in python 3.10 and I believe we are running this in
        # Python 3.9.4 - Other alternatives to switch statements exist but this is the most clear to edit in the future

        if point == "image_setting":
            if input[point] == "all":
                image_setting = "ALL_IMAGES"

            elif input[point] == "correct_only":
                image_setting = "CORRECT_PREDICTION_ONLY"

            elif input[point] == "incorrect_only":
                image_setting = "WRONG_PREDICTION_ONLY"

            elif input[point] == "binary_matrix":
                image_setting = "BINARY_MATRIX_VIEW"
            continue

        elif point == "session_id":
            session_id = input[point]

        elif point == "exclude":
            to_exclude = input[point]

        elif point == "or_exclude":
            or_exclude = input[point]

        elif point == "or_not_query":
            or_not_query = input[point]

        elif point == "include":
            to_filter = input[point]

        elif point == "or_query":
            or_queries = input[point]

        elif point == "add_class":
            binary_task_classes = input[point]

        elif point == "max_antecedent_length":
            max_ant_length = input[point]

        elif point == "min_support_score":
            min_support_score = input[point]

        elif point == "min_lift_score":
            min_lift_score = input[point]

        elif point == "min_confidence_score":
            min_confidence_score = input[point]

        elif point == "true_class":
            desired_classes = input[point]

        elif point == "class_selection":
            class_selection = input[point]

        elif point == "predicted_class":
            predicted_class = input[point]

        elif point == "not_predicted_class":
            not_predicted_class = input[point]

        elif point == "exclude_predicted_class":
            exclude_predicted_class = input[point]

        elif point == "exclude_true_class":
            exclude_true_class = input[point]

        elif point == "only_true_class":
            only_true_class = input[point]

        elif point == "only_predicted_class":
            only_predicted_class = input[point]

        else:
            mistake_found = True
            mistakes.append(point)

    if image_setting is None:
        image_setting = "BINARY_MATRIX_VIEW"

    if mistake_found:
        return {
                   "a given input was invalid. Please set the following arguments into the correct format: ": mistakes
               }, status.HTTP_417_EXPECTATION_FAILED

    if session_id < 0:
        return {
            "you did not input a valid session id, there will be no information for this session"
        }, status.HTTP_417_EXPECTATION_FAILED

    try:
        # Create a frozenset of all the names in the queries such as 'bed AND table AND window',
        # to properly filter them out for all rule mining and such. This should be done for all the required sets.
        filtered_concepts = split_ands(to_filter)
        excluded_concepts = split_ands(to_exclude)
        or_sets = split_ands(or_queries)
        exclude_or = split_ands(or_exclude)
        or_not_divided = split_ands(or_not_query)

        # If there are no filtered concepts, set it to get all results
        if len(filtered_concepts) == 0 and len(or_sets) == 0 and len(excluded_concepts) == 0 and len(or_exclude) == 0 \
                and len(or_not_divided) == 0:
            filtered_concepts = "ALL"
        # executes the rule mining pipeline using the filtered data
        res, stat = execute_image_query_pipeline(image_set_setting=image_setting,
                                                            binary_task_classes=binary_task_classes,
                                                            max_antecedent_length=max_ant_length,
                                                            min_support_score=min_support_score,
                                                            min_lift_score=min_lift_score,
                                                            min_confidence_score=min_confidence_score,
                                                            filter_concepts=filtered_concepts, or_queries=or_sets,
                                                            desired_classes=desired_classes, or_exclude=exclude_or,
                                                            or_not_query=or_not_divided,
                                                            exclude_concepts=excluded_concepts,
                                                            class_selection=class_selection,
                                                            predicted_class=predicted_class,
                                                            not_predicted_class=not_predicted_class,
                                                            exclude_predicted_classes=exclude_predicted_class,
                                                            exclude_true_classes=exclude_true_class,
                                                            only_true_class=only_true_class,
                                                            only_predicted_class=only_predicted_class,
                                                            session_id=session_id)
        return res, stat

    # If there is a value error thrown, it will catch it. Currently there are no errors that would realistically occur
    # however, but if we find cases where we want to catch an error here we can add them below
    except ValueError:
        return {
                   'There were no results for that combination in the binary matrix'
               }, status.HTTP_206_PARTIAL_CONTENT


def universal_query(input):
    """
    If we want to have one endpoint to decide the query type, and we only change the JSON string we can use this.
    It looks for an input 'query_type' and returns the results for query_classes if the type is 'class',
    and returns the results for query_rules if the type is 'rules'. It sends an error message otherwise
    :param input: the incoming data from the JSON string, as a python dict
    :return: the output of whatever query the user wanted, either rules or classes in their own format
    """
    try:
        if input["query_type"] == "class":
            del input["query_type"]
            return query_classes(input)

        elif input["query_type"] == "rules":
            del input["query_type"]
            return query_rules(input)

        else:
            return {
                       "The input 'query_type' was invalid and is not supported": input["query_type"]
                   }, status.HTTP_417_EXPECTATION_FAILED

    except KeyError:
        return {
                   "There was no 'query_type' included in the JSON string, so we do not know what to query"
               }, status.HTTP_417_EXPECTATION_FAILED
