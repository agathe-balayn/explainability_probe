from rest_framework import status
from .models import Sessions, Images, Annotations, Notes
from django.core.exceptions import FieldError
from UserSECA.models import SECAUser
from django.db.models import Q
import random
import pandas as pd
import numpy as np
from pathlib import Path
import base64
import os
import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from sklearn.metrics import f1_score
from collections import Counter


def position(space, name):
    """
        A helper method for the confusion_matrix endpoint
    """
    index = 0
    for i, item in enumerate(space):
        if item == name:
            index = i
            break

    return index


def get_confusion_matrix_data(session_id):
    """
    Retrieves all information in a layout specialised for the confusion matrix on front end.
    :param session_id: Integer. The id of the session object that we will get the data from
    :return: a dict with the required data for the confusion matrix, and an appropriate status code. Not a Response
             object however.
    """
    try:
        predictions = Sessions.objects.filter(id=session_id)[0]
    except ValueError:
        return {"There was no prediction set using id ": session_id}, status.HTTP_417_EXPECTATION_FAILED

    uniques = predictions.images.all().values_list('actual_image', flat=True).distinct()
    uniques_pre = predictions.images.all().values_list('predicted_image', flat=True).distinct()

    for i in uniques_pre:
        if i not in uniques:
            uniques = np.append(uniques, i)

    abs_matrix = [[0 for i in uniques] for j in uniques]
    abs_matrix_transpose = [[0 for i in uniques] for j in uniques]
    rel_matrix = []
    rel_matrix_transpose = []

    for prediction in predictions.images.all():
        abs_matrix[position(uniques, prediction.actual_image)][position(uniques, prediction.predicted_image)] += 1
        abs_matrix_transpose[position(uniques, prediction.predicted_image)][position(uniques, prediction.actual_image)] += 1

    for row in abs_matrix:
        count = 0
        for i in row:
            count += i
        if count == 0:
            count = 1
        rel_matrix.append(np.round([100 * i / count for i in row], 2))

    for row in abs_matrix_transpose:
        count = 0
        for i in row:
            count += i
        if count == 0:
            count = 1
        rel_matrix_transpose.append(np.round([100 * i / count for i in row], 2))

    total_images = predictions.images.all().count()

    return {
               "categories": uniques,
               "matrix (absolute)": abs_matrix,
               "matrix (relative)": rel_matrix,
               "matrix (relative) transpose": rel_matrix_transpose,
               "num_images": total_images
           }, status.HTTP_200_OK


def get_matrix_images(class_A, class_B, session_id):
    """
    Retrieves all images which are predicted and/or classified under the two classes specified in the specified
    session_id.
    :param class_A: String. The name of the first class To display the images of
    :param class_B: String. The name of the second class to display the images of
    :param session_id: Integer. The session id that we will retrieve the images from
    :return: A Python dictionary object with the images from class A and B, organised into their predictions and actual
             classes - class A classified as class A, class A classified as class B, class B classified as clas A, etc.
    """
    try:
        predictions = Sessions.objects.filter(id=session_id)[0]
        # Query images for this confusion matrix, with conditions for the actual and predicted class, respectively
        images = predictions.images.filter( (Q(actual_image=class_A) & Q(predicted_image=class_B)) |
        (Q(actual_image=class_A) & Q(predicted_image=class_A)) | (Q(actual_image=class_B) & Q(predicted_image=class_A)
         | (Q(actual_image=class_B) & Q(predicted_image=class_B))))

    except IndexError:
        return "You are trying to get information from a prediction set that does not exist", \
               status.HTTP_417_EXPECTATION_FAILED

    path_images = os.path.join(
        Path(__file__).resolve().parent, "images/" + predictions.name)
    

    A_classified_as_A = {
        "images": [],
        "heatmaps": [],
        "annotations": [],
        "confidence": []
    }
    A_classified_as_B = {
        "images": [],
        "heatmaps": [],
        "annotations": [],
        "confidence": []
    }
    B_classified_as_A = {
        "images": [],
        "heatmaps": [],
        "annotations": [],
        "confidence": []
    }
    B_classified_as_B = {
        "images": [],
        "heatmaps": [],
        "annotations": [],
        "confidence": []
    }
    #print("RUN CONF", class_A, class_B)

    for row in images:
        cat = row.actual_image

        pre = row.predicted_image
        image_name = row.image_name
        confidence = row.confidence#json.loads(row.confidence) #.replace("\'", "\""))[pre]
        annotations = set(row.annotations_set.values_list('annotation'))

        if cat == class_A and pre == class_A:
            with open(os.path.join(path_images, image_name), "rb") as image:
                img = image.read()
                img = base64.b64encode(img).decode('utf-8')
                A_classified_as_A["images"].append(img)
                

            with open(os.path.join(path_images, "ppp_" + image_name), "rb") as image:
                img = image.read()
                img = base64.b64encode(img).decode('utf-8')
                A_classified_as_A["heatmaps"].append(img)
            
            A_classified_as_A["confidence"].append(confidence)
            if len(annotations) > 0:
                A_classified_as_A["annotations"].append(annotations)
            #print(annotations, type(annotations))


        elif cat == class_A and pre == class_B:
            with open(os.path.join(path_images, image_name), "rb") as image:
                img = image.read()
                img = base64.b64encode(img).decode('utf-8')
                A_classified_as_B["images"].append(img)

            with open(os.path.join(path_images, "ppp_" + image_name), "rb") as image:
                img = image.read()
                img = base64.b64encode(img).decode('utf-8')
                A_classified_as_B["heatmaps"].append(img)
            
            A_classified_as_B["confidence"].append(confidence)
            if len(annotations) > 0:
                A_classified_as_B["annotations"].append(annotations)

        elif cat == class_B and pre == class_A:
            with open(os.path.join(path_images, image_name), "rb") as image:
                img = image.read()
                img = base64.b64encode(img).decode('utf-8')
                B_classified_as_A["images"].append(img)

            with open(os.path.join(path_images, "ppp_" + image_name), "rb") as image:
                img = image.read()
                img = base64.b64encode(img).decode('utf-8')
                B_classified_as_A["heatmaps"].append(img)

            B_classified_as_A["confidence"].append(confidence)
            if len(annotations) > 0:
                B_classified_as_A["annotations"].append(annotations)

        elif cat == class_B and pre == class_B:
            with open(os.path.join(path_images, image_name), "rb") as image:
                img = image.read()
                img = base64.b64encode(img).decode('utf-8')
                B_classified_as_B["images"].append(img)

            with open(os.path.join(path_images, "ppp_" + image_name), "rb") as image:
                img = image.read()
                img = base64.b64encode(img).decode('utf-8')
                B_classified_as_B["heatmaps"].append(img)

            B_classified_as_B["confidence"].append(confidence)
            if len(annotations) > 0:
                B_classified_as_B["annotations"].append(annotations)


        ### Stop when we have 10 images of each ---otherwise too slow.
        # If we're on the diagonal, we don't need as many.
        #if class_A == class_B:
            #print(len(A_classified_as_A["images"]))
        #    if len(A_classified_as_A["images"]) > 10:
        #        break
        #else:
        #    if (len(A_classified_as_A["images"]) > 10) and (len(B_classified_as_B["images"]) > 10) and (len(A_classified_as_B["images"]) > 10) and (len(B_classified_as_A["images"]) > 10):
        #        break
     
    if class_A == class_B:
        nb_im = len(A_classified_as_A["annotations"])
        count_concepts = []
        for list_annotation in A_classified_as_A["annotations"]:
            count_concepts += list(list_annotation.copy())
        count_concepts = [item[0] for item in count_concepts]
        concept_list = ((sorted(Counter(count_concepts).items(), key=lambda item: item[1], reverse=True)))
        c_l = []
        for i in concept_list:
            c_l.append((i[0], round(i[1] / nb_im, 3)))
        return {
               f"{class_A}_classified_as_{class_A}": A_classified_as_A,
               f"counter_concepts": c_l#sorted(Counter(count_concepts).items(), key=lambda item: item[1], reverse=True)
           }, status.HTTP_200_OK
    else:      
        return {

#                B_classified_as_B["annotations"].append(annotations)
#
#    if class_A == class_B:
#        return {
#            f"{class_A}_classified_as_{class_A}": A_classified_as_A,
#            }, status.HTTP_200_OK  
#    return {
               f"{class_A}_classified_as_{class_A}": A_classified_as_A,
               f"{class_A}_classified_as_{class_B}": A_classified_as_B,
               f"{class_B}_classified_as_{class_A}": B_classified_as_A,
               f"{class_B}_classified_as_{class_B}": B_classified_as_B
           }, status.HTTP_200_OK


def calculate_f1_scores(session_id):
    """
    The method to calculate the F1 scores of all the classes in the given session id.
    :param session_id: The session that we want to get classes to calculate the F1 scores of
    :return: A list with all the specified F1 scores of the classes in the session, and an appropriate stats code. Not
             a Response object
    """
    try:
        predictions = Sessions.objects.filter(id=session_id)[0]

    except ValueError:
        return {"There is no prediction set for the session id: ": session_id}, status.HTTP_417_EXPECTATION_FAILED

    category = []
    predicted = []

    for image in predictions.images.all():
        category.append(image.actual_image)
        predicted.append(image.predicted_image)

    calculated_f1_score = f1_score(category, predicted, average=None)
    calculated_f1_score = [round(f1, 3) for f1 in calculated_f1_score]
    return calculated_f1_score, status.HTTP_200_OK
