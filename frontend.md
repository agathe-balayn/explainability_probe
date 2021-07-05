# Frontend
The frontend contains multiple components. We will discuss them in detail and in the same logical order as a user would encounter them.

### Welcome 

The first page the user would see is the welcome page. The user can choose to either log in with an already existing account or register if they are new to the application.

### Register

The register page is very standard. The user is asked to give a username that is unique to the application and a password. The user should also choose a role that they will fulfill which can either be developer or expert. If any of the inputs would be invalid a message will appear to inform the user what is wrong with it. Once you register correctly you will be redirected to the login page.

### Login

The login page is rather basic. The user has to give their credentials to be able to log in. If there is anything wrong, appropriate messages will be shown to the user. Once logged in the user is directed to the user profile page.

### User Profile

The user page will be the first page that the user will visit. The user can see the subscribed to projects. Before they are allowed to visit any other page, they should select a project for which the explainability tool will be used. If the user does not have any projects, they can add one using the submit data page. Users are allowed to change their selection whenever they prefer. After selecting a project, they will be redirected to the dashboard page.


### submit data

This page allows users to add new projects. They should give a unique name and submit a csv file with predictions of the following format: 

| image_name | category | predicted |
| :---: | :---: | :---: | 
| picture1.jpg | class1 | class2 |
| picture2.jpg | class3 | class3 |


The project requires an annotations file which is a json file consisting of an array of object of the following format:


    {
        "pid": [int],
        "category_id": [int],
        "object1_label": [string],
        "object1_bbox": [String],
        "object1_score":[int],
        "object2_label": [string],
        "object2_bbox": [string],
        "object2_score": [int],
        "relation_label": [string],
        "relation_score": [int],
        "weight": [int],
        "session_id": [int],
        "valid": [boolean],
        "is_typical": [boolean],
        "reason": [string],
        "is_annotated": [boolean],
        "is_chosen": [boolean],
        "image_name": [string],
        "heatmap_name": [string]
    }
  

Then the user should submit all the images for the project in jpg format. 
Finally there is an option to subscribe other users to the project. Know that the application assigns the user creating the project automatically so the user should not add themselves in this section. Once the user has submitted all the necessary information, they can click the button and the project will be added as an option in the user profile page.

### Dashboard

The dashboard is a combination of the confusion matrix and the query page. For more information, consult the documentation for these pages. 

### About 

The about page is first in line of all the interfaces as it gives an introduction about the application. Some of the useful pages are explained along with a link to the respected interfaces to make the user’s experience more efficient. 

### SECA

The SECA page informs the user about SECA itself and gives some more information about concepts with which the user might be unacquainted.

### Confusion Matrix

A confusion matrix presents the proportion of wrong and correct predictions throughout the entire project. One cell has the percentage of images that are classified as the class corresponding to the column but that are actually part of the class corresponding to the row. Above every class, the user can find their f1 score. 

The user can click on a particular cell, which would bring them to a new page where concepts and rules will be shown along with their statistics. These can be ordered as the user prefers. charts about the proportions between all the classes and only the two classes are included with the images that are part of the either classes 
### Explore

In the explore page the user can search for concepts and their statistics like typicality and  correct and wrong prediction rates. they  can select to search in all the images, only images with correct predictions or only images with incorrect predictions. Be aware that retrieving these statistics might take a few seconds of time. The concepts can be sorted based on a category given by the user. This does not require the user to search again, the sorting will be done instantly. 

In the same page, there is a section where users can examine class specific explanations. The principle is the same for the overall class explanations, the user selects to search in all the images, only images with correct predictions or only images with incorrect predictions and after a few seconds the concepts are shown for every class in the project that the user had previously selected in the user profile page. There are additional options like sorting, filtering based on support and confidence and score display when hovering over a certain concept, which all will be done instantly. 


### Query

The query page allows the user to search for the presence of specified concepts or relations between given concepts in the respected project. The user can give a concepts and choose to make their query more specific by adding another concept and by selecting the function it has on the query (and, or, not). The user can choose the preferred options and select the categorization. By clicking either the confusion matrix button or the typicality score button, the correct results will be shown.    

Querying for images works mainly in the same way. 

### Wiki

The wiki page is divided into three sections.
In the first section, the user can search for images and receive more information about the class, the general description and the expected concepts.
The user can add additional images with their information to the data set in the second section.
In the last section, there is the possibility to ask questions specific to the project the user is working on. These questions are visible for everyone that is subscribed to the project.     


### Info

The info page presents a video with more explanation of the entire application.

## API
The `API.js` file contains  all the URLs used throughout the code, and in all files they are imported from this file. In case of any changes, this makes changing the API easier, eg. if the project gets hosted on a different domain
## CSS folder
The project uses `.less` for style and all the `.less` files are stored in this folder
## Components folder
This folder contains all the various components. The files mostly correspond to each interface or to specific components of the page, eg. the `Header.js` file contains the tabs layout. The components will now be briefly described here.
