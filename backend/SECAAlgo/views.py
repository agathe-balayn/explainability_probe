from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from .models import Sessions, Images, Annotations
from .serializer import UniversalSerializer, SerializerClassNotFoundException
from .seca_helper_methods import get_tabular_representation, get_tabular_representation_rule_mining, \
    save_csv_predictions, link_annotations, compute_statistical_tests_custom
from .pipeline import execute_rule_mining_pipeline, post_process_concepts_rules
from .query import query_rules, query_classes, universal_query, query_images, simple_rule_search, query_score_concepts, query_all_concepts_scores
from .models import Sessions, Images, Notes, ExplanationSet
from django.core.exceptions import FieldError
from django.views.generic import View
from UserSECA.models import SECAUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import ast
from django.contrib.auth.models import User
from sklearn.metrics import f1_score
from .confusion_matrix_methods import get_confusion_matrix_data, get_matrix_images, calculate_f1_scores

import random
import pandas as pd
import numpy as np
from pathlib import Path
import base64
import os
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from sklearn.metrics import f1_score


# These are the views relating to the confusion matrix
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def confusion_matrix(self):
    """
        This endpoint returns class names, and there absolute and releative frequencies; to be used in the 
        matrix interface. 
        Args:
            self (Request): object representing the HTTP request
        Returns:
            A dictionary with three K/V pairs. The first being categories which has all the unique class names,
            the second being matrix (absolute) which has a list of absolte frequencies for each class, 
            and the third being matrix (relative) which has a list of relative frequencies for each class 
    """

    session_id = self.GET.get('session_id')

    confusion_matrix_response, status = get_confusion_matrix_data(session_id)
    return Response(confusion_matrix_response, status=status)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def images_matrix(request): 
    """
    Receives a 'GET' request with information of 2 classes and a session id in the header. Returns all the images
    which are related to those two classes, in that 'session', in an ordered manner of the true class and what it was
    predicted as. There are 4 outputs: actually class A, predicted class A - actually class A, predicted class B, etc.
    :param request: The information sent through the GET request (aka: the url which we can extract info from)
    - classA -> One of the classes in the images matrix. Probably the actual class, but can be predicted if so desired
    - classB -> The other class chosen in the images matrix.
    - session_id -> The id of the predictions object that the images will be taken from
    :return: A dict with 4 keys: f(class A)_classified_as_(class A), f(class A)_classified_as_(class B), etc.
    """
    try:
        class_A = request.GET.get("classA")
        class_B = request.GET.get("classB")
        session_id = request.GET.get("session_id")
        print(session_id)
    except KeyError:
        return Response("There was an error in the input parameters, not all of 'classA', 'classB' and 'session_id' "
                        "were properly included in the request.", status=status.HTTP_417_EXPECTATION_FAILED)

    images, stat = get_matrix_images(class_A=class_A, class_B=class_B, session_id=session_id)
    #print("Found images", images)
    return Response(images, status=stat)


# These are the views relating to adding/removing images or adding/removing data from the database
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def data_all_images(request, *args, **kwargs):
    """
        This endpoint returns all data for the Explore interface, for the ALL_IMAGES setting
        Args:
            request (Request): the object representing the HTTP Request
        Returns:
            a dictionary that contains all antecedents and their scores, along with all rules and their scores
    """
    session_id = request.GET.get("session_id")
    res, supp_conf, stat = execute_rule_mining_pipeline(image_set_setting="ALL_IMAGES", session_id=session_id)
    return Response({"data": res}, status=stat)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def add_data(request):
    """
    Takes in an input with the required csv data for predictions, and a json file to save the annotations. Saves and
    links the relevant information in the database, and returns the appropriate status code for if it was properly
    saved or not
    :param request: The data received in the post request. Should have the following keys in its data:
    - data_set -> csv info with a column for image_name in the first column, the true class in the second, and the
    predicted class in the third
    - dataset_name -> the name that the session object will be saved as
    - username -> List of Strings. The names of the users that will be added to this prediction set
    - annotations -> the json information with the required annotations that will be linked to the prediction set.
    :return: a response object with a message and status code telling the sender if the information was properly saved
    or if there was an error.
    """
    response, status, prediction_id = save_csv_predictions(request.data)
    if prediction_id == -1 or response != "done" or status != 200:
        return Response(response, status=status)
    else:
        response2 = link_annotations(request.data['annotations'], prediction_id)
        return Response(response2, status=status)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def add_image(request):
    """
    Receives an http request containing a data set with images, and the name of the data set the user wishes to save
    their images as. It saves the images in the directory SECAAlgo/images/(data set name)/(image name)
    :param request: A http post request which has the following keys in its data:
    - dataset_name -> The name of the dataset, the session/prediction set that the images will be saved under
    - image_data -> The images that will be saved to the new directory
    :return: a string and a status code responding if the additions were done successfully or not.
    """
    parent_dir = os.path.join(Path(__file__).resolve().parent, "images")

    data_name = request.data["dataset_name"]
    image_data = request.data["image_data"]

    path = os.path.join(parent_dir, data_name)
    try:
        os.makedirs(path)

    except:
        ERROR_MSG = "Error making path, see output of Django console"
        print(ERROR_MSG)
        return Response(ERROR_MSG, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    for image in image_data:
        imageEncoded = image_data[image].replace("data:image/jpeg;base64,", "")
        with open(os.path.join(path, image), "wb") as fh:
            fh.write(base64.decodebytes(bytes(imageEncoded, 'utf-8')))

    return Response("success", status=status.HTTP_200_OK)


def twoDdf_to_df_of_df(df):
    new_df = {}
    for idx, item in df.iterrows():
        new_df[idx] = item.to_dict()
        #print(new_df[idx])
        #print(type(item))
    return new_df

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def query_concept_matrix(request):
    print("start query concept matrix")
    print(request.data)
    request.data["image_setting"] = "all"


    # Get number of target concepts per cell.
    res, code = query_images(request.data)
    list_labels = list(set(res["true_label"]))
    col_names = ["ground_truth"] + list_labels
    rows = []
    for label_name in list_labels:
        rows.append([label_name] + [0.0]*len(list_labels))
    empty_matrix = pd.DataFrame(rows, columns=col_names)
    empty_matrix.set_index("ground_truth", inplace=True)
    #print(len(empty_matrix))

    #print(res)
    concept_df = res.loc[res["filter_concepts"] == 1]
    count_concept = empty_matrix.copy()
    for row_gt in list_labels:
        for col_pred in list_labels:
            count_concept.at[row_gt, col_pred] = len(concept_df.loc[(concept_df["true_label"] == row_gt) & (concept_df["predicted_label"] == col_pred)])
    #print(count_concept)

    # Get total number of images with the concept.
    total_concept = len(concept_df)
    #print(total_concept)



    ### Compute top number (percentge concept among all images in the cell).
    # Get total number of images per cell.
    image_in_mat = empty_matrix.copy()
    for row_gt in list_labels:
        for col_pred in list_labels:
            image_in_mat.at[row_gt, col_pred] = len(res.loc[(res["true_label"] == row_gt) & (res["predicted_label"] == col_pred)])
    #print(image_in_mat)
    #print(count_concept)

    # Divide nb target concepts with total number per cell.
    top_number = empty_matrix.copy()
    for row_gt in list_labels:
        for col_pred in list_labels:
            #print(count_concept.at[row_gt, col_pred], image_in_mat.at[row_gt, col_pred], (count_concept.at[row_gt, col_pred] / image_in_mat.at[row_gt, col_pred]))
            top_number.at[row_gt, col_pred] = (count_concept.at[row_gt, col_pred] / image_in_mat.at[row_gt, col_pred]) *100 if image_in_mat.at[row_gt, col_pred] != 0 else 0.0
    #print(top_number)
    #for col in top_number:
    #    print(top_number[col].unique())
    #print(top_number.nunique())

    ### Compute bottom number (percentage concept among all images with the target concept)
    # Divide nb trget concepts with this total number.
    bottom_number = empty_matrix.copy()
    if total_concept > 0:
        for row_gt in list_labels:
            for col_pred in list_labels:
                bottom_number.at[row_gt, col_pred] = (count_concept.at[row_gt, col_pred] / total_concept) *100
    else:
        bottom_number.loc[:, :] = 0.0
    #for col in bottom_number:
    #    print(bottom_number[col].unique())

    editedResult = {}
    #print(bottom_number)
    editedResult["top_number"] = twoDdf_to_df_of_df(top_number.round(2))
    editedResult["bottom_number"] = twoDdf_to_df_of_df(bottom_number.round(2))
    #print(editedResult["top_number"])
    #print(editedResult["bottom_number"])
    return Response(editedResult, status.HTTP_200_OK)


    



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def query_specific_images(request):
    """
    Allows users to look for specific images in specified directories. Queries the database for these rules
    :param request: A HTTP POST request with the query data that is being sent. Has the same format as querying rules
    :return: A Response object with a set of images and a status code, 200 for success, and 400 for failure.
    """
    print("start looking for images")
    print(request.data)
    res, code = query_images(request.data)
    #print(res)
    editedResult = []
    image_names = []
    session_id = request.data['session_id']
    session = Sessions.objects.filter(id=session_id)
    dir = os.path.join(Path(__file__).resolve().parent,
                       "images/" + session[0].name)
    for idx, row in res[res["filter_concepts"] == 1].iterrows():
        obj = {'predicted_class': row["predicted_label"]}
        obj['image_name'] = row["image_name"]
        with open(os.path.join(dir, "ppp_" + row["image_name"]), "rb") as image:
            img = image.read()
            img = base64.b64encode(img).decode('utf-8')
            obj['saliency_map'] = img

        with open(os.path.join(dir, row["image_name"]), "rb") as image:
            img = image.read()
            img = base64.b64encode(img).decode('utf-8')
            obj['image'] = img

        obj['true_class'] = row["true_label"]
        obj['rules'] = ""
        editedResult.append(obj)
    for i in editedResult:
        image = Images.objects.filter(image_name=i['image_name'])
        list_annot = []
        for j in Annotations.objects.filter(image=image[0]):
            list_annot.append(j.annotation)
            #i['rules'] += j.annotation + ", "
        for elem in  list(set(list_annot)):
            i['rules'] += elem + ", "
    #print(editedResult)
    return Response(editedResult, code)
    
    """
    print(res['rules'])
    for rule in res['rules']:
        for predicted_class in res['rules'][rule]:
            for i in res['rules'][rule][predicted_class]:
                if ".jpg" in i:
                    if i not in image_names:
                        obj = {'predicted_class': predicted_class}
                        image_names.append(i)
                        obj['image_name'] = i

                        with open(os.path.join(dir, "ppp_" + i), "rb") as image:
                            img = image.read()
                            img = base64.b64encode(img).decode('utf-8')
                            obj['saliency_map'] = img

                        with open(os.path.join(dir, i), "rb") as image:
                            img = image.read()
                            img = base64.b64encode(img).decode('utf-8')
                            obj['image'] = img

                        obj['true_class'] = res['rules'][rule][predicted_class][i]
                        obj['rules'] = ""
                        editedResult.append(obj)

    for i in editedResult:
        image = Images.objects.filter(image_name=i['image_name'])
        for j in Annotations.objects.filter(image=image[0]):
            i['rules'] += j.annotation + ", "

    return Response(editedResult, code)
    """
    return


def all_images_from_problem_view(request):
    """
    This method retrieves images from a given Sessions object and returns a desired amount
    :param request: An HTTP GET request with the following parameters:
    - amount -> Integer. The amount of images to retrieve
    - session_id -> Integer. The session id of the prediction set we want to retrieve the images from
    :return:  A JsonResponse object with a dict with one key: images. The value to this key is the set of images that
    were requested with the parameters given.
    """
    amount = int(request.GET.get("amount", 1))
    session_id = int(request.GET.get("session_id", -1))

    session = get_object_or_404(Sessions, id=session_id)
    imagesObjects = session.images.all()
    images = []
    names = []
    for i in imagesObjects:
        names.append("images/" + session.name + "/" + i.image_name)
    # random.shuffle(names) #this could be uncommented in case you dont always want to retrieve the same images but a
    # random selection instead
    amount = min(len(names), amount)

    # TODO: change path to match where the images are
    path = Path(__file__).resolve().parent
    for i in range(0, amount):
        with open(os.path.join(path, names[i]), "rb") as image:
            img = image.read()
            img = base64.b64encode(img).decode('utf-8')
            images.append(img)
    return JsonResponse({"images": images})


# These are the views relating to querying the database with the methods in the query file
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def query_db(request):
    """
    Receives a HTTP post request and uses the query input to send data of the Images, Sessions or Annotations which are
    stored in the database. Currently queries this regardless of session_id, should likely be changed to have more
    specific queries.
    :param request: A HTTP post request with a JSON string with a query for query_classes
    :return: Python Dictionary object. The information from the query_classes method
    """
    res, code = query_classes(request.data)
    return Response(res, status=code)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def query_concepts_and_rules(request):
    """
    Queries the query_rules method with the data from the input HTTP POST request. The format of the data is a JSON
    string with the information that is specified in the query_rules method.
    :param request: A HTTP POST request with the data required for the query. More details specified in the query_rules
                    method in the query file.
    :return: A Response object containing a python dictionary object and an appropriate status code
    """
    print("query concepts and rules", request.data)
    res, code = query_rules(request.data)
    return Response(res, status=code)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def query_scores(request):
    print("querying scores.")
    # Search for rules which have the queried concepts.
    print(request.data)

    if ("or_query" not in request.data) or (len(request.data["or_query"]) == 0):
        print("nothing to query")
        return Response([], status=status.HTTP_417_EXPECTATION_FAILED)
        


    list_scores, struct_rep, stat_scores = query_score_concepts(request.data)


    has_not = False
    if ("or_query" in request.data) and (len(request.data["or_query"]) > 0):
        for item in request.data["or_query"]:
            if "NOT" in item:
                has_not = True
    if ("or_query" in request.data) and (len(request.data["or_query"]) > 0) and (has_not):
        #print("need to add additional conditions with negation")
        list_rules = []
        stat_rules = []
        df_info = []
    else:
        list_rules, stat_rules, df_info = simple_rule_search(request.data)
    
    
    res_concept, res_rule = post_process_concepts_rules(list_scores, struct_rep, stat_scores, list_rules, stat_rules, df_info, request.data["or_query"])

    res = {"concepts": res_concept, "rules": res_rule}
    code = status.HTTP_200_OK
    print(res)
    return Response(res, status=code)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def query_all(self):
    """
    Allows the user to query either the 'query rules' or 'query classes' method from the same endpoint. Just requires
    an additional input in the query specifying which query is desired
    :param self: A HTTP POST request with the required data for either query_rules or query_classes, and an additional
                 key named 'query_type' with either 'rules' or 'classes' as its value.
    :return: A Response object with the information from the query, and its appropriate status code.
    """
    print("query all...")
    print(self.data)



    session = Sessions.objects.filter(id=self.data["session_id"])[0]
    exp = session.explanations.filter(type_explanation="concepts_rules", image_setting=self.data["image_setting"], task_setting=self.data["task_type"], classA=self.data["add_class"][0], classB=self.data["add_class"][1])
    print(exp)
    if len(exp) > 0:
        print("data already collected")
        data = exp.last()
        return Response(data.explanation_list, status=status.HTTP_200_OK)
    else:
        res, code = universal_query(self.data)
        print(res)
        exp = ExplanationSet(type_explanation="concepts_rules", image_setting=self.data["image_setting"], task_setting=self.data["task_type"], classA=self.data["add_class"][0], classB=self.data["add_class"][1], explanation_list=res)
        exp.save()
        session.explanations.add(exp)
        return Response(res, status=code)


# These are the views used in the Explore tab
@api_view(['post'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def data_specific_explanations(request):
    """
    Retrieves specific explanations for the specified session_id.
    :param request: A HTTP POST request which contains the session id and the image setting which the user wants to
                    retrieve.
    :return: A response object with the specific explanation's data
    """
    session_id = request.data['session_id']
    setting = request.data["IMAGE_SET_SETTING"]
    rule_setting = request.data["RULE_SETTING"]

    session = Sessions.objects.filter(id=session_id)[0]
    #set_explanations = session.explanations.all()
    exp = session.explanations.filter(type_explanation="rules", image_setting=setting, task_setting=rule_setting)
    if len(exp) > 0:
        print("data already collected")
        data = exp.last()
        print(data.explanation_list)
        return Response({"data": data.explanation_list})
    else:
        print("collect data")
        if (setting == "CORRECT_PREDICTION_ONLY"):
            result, supp_conf, unused = execute_rule_mining_pipeline(image_set_setting="CORRECT_PREDICTION_ONLY",
                                                                     session_id=session_id, rule_setting=rule_setting)
        elif (setting == "ALL_IMAGES"):
            result, supp_conf, unused = execute_rule_mining_pipeline(
                image_set_setting="ALL_IMAGES", session_id=session_id, rule_setting=rule_setting)
        else:
            result, supp_conf, unused = execute_rule_mining_pipeline(image_set_setting="WRONG_PREDICTION_ONLY",
                                                                     session_id=session_id, rule_setting=rule_setting)
        
        if rule_setting == "R_MINING":
            rules = {}
            for rule in result["rules"]:

                for key in supp_conf:
                    if key[0] == rule:
                        rules[rule] = (key[1], key[2])
                        break
            data = {}
            for rule in result["rules"]:
                for class_ in result["rules"][rule]:
                    if not class_ in data:
                        data[class_] = {}

                    for i in rules:
                        if rule == i:
                            data[class_][i] = (result["rules"][rule][class_]["percent_present"],
                                               rules[i][1],
                                               result["rules"][rule][class_]["percent_present"],
                                               result["rules"][rule][class_]["percent_correct"],
                                               result["rules"][rule][class_]["typicality"],
                                               result["rules"][rule][class_]["percent_present_antecedent"])
        #print(data)
        print("will compute more concepts")
        list_concepts, l_struct, s_stat = query_all_concepts_scores(request.data)
        if rule_setting == "STATS_S":
            # Merge previous data and new ones.
            data = result
            for class_ in l_struct:
                if class_ not in data.keys():
                    data[class_] = {}
                for concept in l_struct[class_]:
                    if concept not in data[class_].keys():
                        data[class_][concept] = l_struct[class_][concept]


            
        elif rule_setting == "R_MINING":
            
            # Also get typicality of simple concepts for each class.
            
            for concept in list_concepts:

                for consequent_name in list(set(l_struct["predicted_label"])):
                
                    if not consequent_name in list(data.keys()):
                        data[consequent_name] = {}
                    if concept not in  list(data[consequent_name].keys()):
                        supp_ant_cons = len(l_struct.loc[(l_struct[concept] == 1) & (l_struct["predicted_label"] == consequent_name)])
                        percent_present = round(supp_ant_cons / len(l_struct), 3)
                        if supp_ant_cons== 0:
                            percent_correct =0.0
                        else:
                            percent_correct =round(len(l_struct.loc[(l_struct[concept] == 1) & (l_struct["predicted_label"] == consequent_name) & (l_struct["classification_check"] == "Correctly classified")])/ supp_ant_cons, 3)
                        
                        supp_ant = len(l_struct.loc[(l_struct[concept] == 1) ])
                        supp_cons = len((l_struct.loc[l_struct["predicted_label"] == consequent_name]))
                        if supp_ant != 0:
                            confidence = round(supp_ant_cons / supp_ant , 3)
                        else:
                            confidence = 0
                        if (supp_ant != 0) and (supp_cons != 0):
                            lift = round(supp_ant_cons / (supp_ant * supp_cons) , 3)
                        else:
                            lift = 0
                        percent_present_antecedent = round(supp_ant_cons / supp_cons, 3)

                        
                        data[consequent_name][concept] = (percent_present, confidence, percent_present, percent_correct,\
                            lift, percent_present_antecedent)

        # If typicality score not significant, write "nan"

        # Save to db.
        print("session id", session_id)
        #exp = ExplanationSet(type_explanation="rules", image_setting=setting, task_setting=rule_setting, classA="", classB="")
        #print(exp.type_explanation, exp.explanation_list)
        exp = ExplanationSet(type_explanation="rules", image_setting=setting, task_setting=rule_setting, classA="", classB="", explanation_list=data)
        exp.save()
        session = Sessions.objects.filter(id=session_id)[0]
        session.explanations.add(exp)#ExplanationSet.objects.filter(type_explanation="rules", image_setting=setting, task_setting=rule_setting, classA="", classB="")[-1])
        exp1 = session.explanations.all()[0]
        
        return Response({"data": data})


@api_view(['post'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def data_specific_explanations_more_complete(request):
    """
    Retrieves specific explanations for the specified session_id.
    :param request: A HTTP POST request which contains the session id and the image setting which the user wants to
                    retrieve.
    :return: A response object with the specific explanation's data
    """
    print("data_specific_explanations_more_complete", request.data)
    session_id = request.data['session_id']
    setting = request.data["IMAGE_SET_SETTING"]
    rule_setting = request.data["RULE_SETTING"]

    if (setting == "CORRECT_PREDICTION_ONLY"):
        result, supp_conf, unused = execute_rule_mining_pipeline(image_set_setting="CORRECT_PREDICTION_ONLY",
                                                                 session_id=session_id, rule_setting=rule_setting)
    elif (setting == "ALL_IMAGES"):
        result, supp_conf, unused = execute_rule_mining_pipeline(
            image_set_setting="ALL_IMAGES", session_id=session_id, rule_setting=rule_setting)
    else:
        result, supp_conf, unused = execute_rule_mining_pipeline(image_set_setting="WRONG_PREDICTION_ONLY",
                                                                 session_id=session_id, rule_setting=rule_setting)
    
    if rule_setting == "STATS_S":
        data = result
    elif rule_setting == "R_MINING":
        rules = {}
        for rule in result["rules"]:

            for key in supp_conf:
                if key[0] == rule:
                    rules[rule] = (key[1], key[2])
                    break
        data = {}
        for rule in result["rules"]:
            for class_ in result["rules"][rule]:
                if not class_ in data:
                    data[class_] = {}

                for i in rules:
                    if rule == i:
                        data[class_][i] = (result["rules"][rule][class_]["percent_present"],
                                           rules[i][1],
                                           result["rules"][rule][class_]["percent_present"],
                                           result["rules"][rule][class_]["percent_correct"],
                                           result["rules"][rule][class_]["typicality"],
                                           result["rules"][rule][class_]["percent_present_antecedent"])

    print("will compute more concepts")
    list_concepts, l_struct, s_stat = query_all_concepts_scores(request.data)
    if rule_setting == "STATS_S":
        # Merge previous data and new ones.
        for class_ in l_struct:
            if class_ not in data.keys():
                data[class_] = {}
            for concept in l_struct[class_]:
                if concept not in data[class_].keys():
                    data[class_][concept] = l_struct[class_][concept]


        
    elif rule_setting == "R_MINING":
        
        # Also get typicality of simple concepts for each class.
        
        for concept in list_concepts:

            for consequent_name in list(set(l_struct["predicted_label"])):
            
                if not consequent_name in list(data.keys()):
                    data[consequent_name] = {}
                if concept not in  list(data[consequent_name].keys()):
                    supp_ant_cons = len(l_struct.loc[(l_struct[concept] == 1) & (l_struct["predicted_label"] == consequent_name)])
                    percent_present = round(supp_ant_cons / len(l_struct), 3)
                    if supp_ant_cons== 0:
                        percent_correct =0.0
                    else:
                        percent_correct =round(len(l_struct.loc[(l_struct[concept] == 1) & (l_struct["predicted_label"] == consequent_name) & (l_struct["classification_check"] == "Correctly classified")])/ supp_ant_cons, 3)
                    
                    supp_ant = len(l_struct.loc[(l_struct[concept] == 1) ])
                    supp_cons = len((l_struct.loc[l_struct["predicted_label"] == consequent_name]))
                    if supp_ant != 0:
                        confidence = round(supp_ant_cons / supp_ant , 3)
                    else:
                        confidence = 0
                    if (supp_ant != 0) and (supp_cons != 0):
                        lift = round(supp_ant_cons / (supp_ant * supp_cons) , 3)
                    else:
                        lift = 0
                    percent_present_antecedent = round(supp_ant_cons / supp_cons, 3)

                    
                    data[consequent_name][concept] = (percent_present, confidence, percent_present, percent_correct,\
                        lift, percent_present_antecedent)
        
    """
    list_concepts, l_s, l_struct, s_stat = query_all_concepts_scores(request.data)
    print(l_s, l_struct, s_stat)
    for concept, a, b, c in zip(list_concepts, l_s, l_struct, s_stat):
        for consequent_info in l_s:

            if not consequent_info["consequent_name"] in data:
                data[consequent_info["consequent_name"]] = {}
            if concept not in  list(data[consequent_info["consequent_name"]].keys()):

                percent_present = round(len(b.loc[(b["filter_concepts"] == 1) & (b["predicted_label"] == consequent_info["consequent_name"])]) / len(b), 3)
                if len(b.loc[(b["filter_concepts"] == 1) & (b["predicted_label"] == consequent_info["consequent_name"])]) == 0:
                    percent_correct =0.0
                else:
                    percent_correct =round(len(b.loc[(b["filter_concepts"] == 1) & (b["predicted_label"] == consequent_info["consequent_name"]) & (b["classification_check"] == "Correctly classified")])/ len(b.loc[(b["filter_concepts"] == 1) & (b["predicted_label"] == consequent_info["consequent_name"])]), 3)
                if a["ant_cons_supp"] != 0:
                    confidence = round(a["ant_cons_supp"] / a["antecedent_supp"], 3)
                else:
                    confidence = 0

                
                data[consequent_info["consequent_name"]][concept] = (percent_present, confidence, percent_present, percent_correct,\
                    round(a["lift"], 3))
    """

    # If typicality score not significant, write "nan"

    return Response({"data": data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def data_overall_explanations(request):
    """
    Returns the all info for all images in the specified session, for the request made: correct predictions, all images
    or only incorrect predictions.
    :param request: A HTTP POST request with the keys 'IMAGE_SET_SETTING' and 'session_id'
    :return: A Response object with a dict containing the key 'result', and value of all the information retrieved from
             running the rule mining pipeline for the specified session
    """
    print(request.data)
    setting = request.data["IMAGE_SET_SETTING"]
    session_id = request.data["session_id"]
    print("we are here")
    session = Sessions.objects.filter(id=session_id)[0]
    exp = session.explanations.filter(type_explanation="concepts", image_setting=setting, task_setting="all", classA="", classB="")
    if len(exp) > 0:
        print("data already collected")
        data = exp.last()
        return Response({"result": data.explanation_list})

    if (setting == "CORRECT_PREDICTION_ONLY"):
        result = execute_rule_mining_pipeline(image_set_setting="CORRECT_PREDICTION_ONLY", session_id=session_id)[0]
    elif (setting == "ALL_IMAGES"):
        result = execute_rule_mining_pipeline(image_set_setting="ALL_IMAGES", session_id=session_id)[0]
    else:
        result = execute_rule_mining_pipeline(image_set_setting="WRONG_PREDICTION_ONLY", session_id=session_id)[0]
    exp = ExplanationSet(type_explanation="concepts", image_setting=setting, task_setting="all", classA="", classB="", explanation_list=result)
    exp.save()
    session = Sessions.objects.filter(id=session_id)[0]
    session.explanations.add(exp)#ExplanationSet.objects.filter(type_explanation="rules", image_setting=setting, task_setting=rule_setting, classA="", classB="")[-1])
    return Response({"result": result})


    # classes = {}
    # data = pd.read_csv(
    #     "./data_mining_results/batch2/min_support_0/data_mining_rules_batch2_min_support_0.csv"
    # )
    # for row in data.iterrows():
    #     consequent = row[1]["consequents"].split("'")[1]
    #     classes[consequent] = []
    #
    # for row in data.iterrows():
    #     consequent = row[1]["consequents"].split("'")[1]
    #     antecedents = []
    #
    #     if len(row[1]["antecedents"].split("'")) == 3:
    #         antecedents = row[1]["antecedents"].split("'")[1]
    #     else:
    #         for i in row[1]["antecedents"].split("{")[1].split("}")[0].split("'")[1:-1][::2]:
    #             antecedents.append(i)
    #
    #     classes[consequent].append({
    #         "antecedents": antecedents,
    #         "support": row[1]["support"],
    #         "confidence": row[1]["confidence"]
    #     })
    #
    # return Response({"classes": classes})


# These are the views for the notes interface, which are differently set up for some reason
@method_decorator(csrf_exempt, name='dispatch')
class NotesView(View):
    def get(self, request):
        """
        Retrieves notes for a specified user and session.
        :param request: A HTTP GET request with the required information
        - 'session_id' -> Integer. The session id that the desired notes object is a part of
        - 'user' -> String. The username of the user that the notes object is owned by.
        :return: A Json response object with the notation data and a status code for if it was completed successfully
                 or not.
        """
        session_id = int(request.GET.get("session_id", -1))
        username = str(request.GET.get("user", ""))

        if username == "" or session_id == -1:
            return Response("no user or session id input", status=500)

        prediction = get_object_or_404(Sessions, id=session_id)
        user = User.objects.filter(username=username)[0]
        userSeca = SECAUser.objects.filter(user=user)[0]
        notes = Notes.objects.filter(user=userSeca, session=prediction)

        data = {
            "notes": notes[0].content
        }
        return JsonResponse(data)

    def post(self, request):
        """
        Saves the note object which has been given
        :param request: A HTTP POST request to create a note object. Requires the following keys:
        - 'username' -> String. The username that the notes object will be owned by
        - 'session' -> Integer. The session id that the notes object will be owned by
        - 'notes' -> String. The data that will be saved in the created note object
        :return: A Json response with only a status code, but in a python dictionary instead of as an actual status
                 code. The key for this status code is 'code'
        """
        byte_str = request.body
        dict_str = byte_str.decode("UTF-8")

        data = dict(ast.literal_eval(dict_str))
        username = data['username']
        session_id = data['session_id']
        note = data['notes']
        prediction = get_object_or_404(Sessions, id=session_id)

        user = User.objects.filter(username=username)[0]
        userSeca = SECAUser.objects.filter(user=user)[0]
        notes = Notes.objects.filter(user=userSeca, session=prediction)[0]
        notes.content = note
        notes.save()

        return JsonResponse({"code": 200})


# These last 2 methods are just kind of their own thing
def get_predictions(request):
    """
    Retrieves all the predictions. Unsure if this method is actually being used at all and should be deleted if not
    :param request: literally nothing
    :return: A Python dictionary object with all prediction objects stored in the database. The key to the prediction
             objects is 'predictions'
    """
    predictions = Sessions.objects.all()
    prediction_list = []
    for i in predictions:
        prediction = {
            "id": i.id
        }
        prediction_list.append(prediction)
    return JsonResponse({"predictions": prediction_list})


@api_view(['post'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def get_f1(request):
    """
    Retrieves all the F1 scores for all the classes in the given session
    :param request: A HTTP POST request with the following information:
    - session_id -> Integer. The id of the session that we wish to retrieve all f1 scores from
    :return: A list of all F1 scores of the classes in the specified session.

    note: The return object is a list instead of a dict object. Should check if the results are properly synced with the
          front end equivalent, and that the order that is being returned here is not being randomised/broken with
          differing data values.
    """
    try:
        session_id = request.data['session_id']

    except KeyError:
        return Response({"response": "There was no valid session id included in the request"},
                        status.HTTP_417_EXPECTATION_FAILED)

    f1_score, status = calculate_f1_scores(session_id)
    return Response(f1_score, status=status)
