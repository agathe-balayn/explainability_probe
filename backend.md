# Backend
## Important background information
The backend code resides in the backend directory, and its entire structure is based on Django web framework principles. The backend directory inside the backend directory is the main Django application that has the settings.py folder along with the urls.py folder. 

## Running the backend server
To run the backend server, the system requires an installation of python. The application has been developed with Python 3.9.5 however, it has been successfully executed with Python 3.8.3 as well. Therefore any versions between these two will work. 
Next, a set-up virtual environment is required. The following is how this can be achieved:


1. Run `pip install virtualenv` to install virtual environment manager dependency 
2. Change directory into the backend folder, and then execute `virtualenv venv`
3. Activate the environment with `source venv/bin/activate` if on Mac OS, or `venv\Scripts\activate` for Windows
4. Make sure that you are in the backend directory where the _requirements.txt_ file can be found. Execute `pip install -r requirements.txt` to install all the required dependencies to run the server. 
5. Execute `python manage.py makemigrations` followed with `python manage.py migrate` to setup the database. 
6. Finally, execute `python manage.py runserver` to run the server

If `pip install -r requirements.txt` is not working, the issue could lie with your python version. Version 3.8.3 is known to be able to install everything properly.

After the first time setup, simply activating the virtual environment and starting the server is sufficient:
1. First activate the virtual environment with `venv\Scripts\activate`
2. Then from inside the virtual environment start the server with the command `python manage.py runserver`

## The database and updating it
Currently the database that is being used is the one that comes by default with any Django application, namely a **sqlite** database. It is entirely possible to link the existing application with an online database, following the documentation found on Django's website.

Sqlite is not an in-memory database, and therefore, whenever it is updated, the changes are persisted even after the server is shut down. 

Django makes it very easy to update the database. Adding a new database table is done by adding a new class (that has the same name as the database table) in a models.py file (of any Django application). 
 
If an existing table is updated, often the developer will need to provide a new default value for all the previous existing entries, or can choose to let them be null. 

Important: After making changes to the database schema (ie. adding new classes to a models.py file, or modifying existing ones) execute `python manage.py makemigrations` followed by `python manage.py migrate` to let Django make its updates. 

## General Procedure to follow when making changes
##### In general:
In general making changes is very easy as they are instantly applied upon saving (even while the server is running), but it's recommended to make changes whilst the server is shut down. The reason is quite simple, after making changes, execute `python manage.py test` to run all tests and ensure that none of the previously implemented functionalities have been altered. 

##### Database changes
If the changes are about databases, or if database changes are included, then please first always execute `python manage.py makemigrations` followed by `python manage.py migrate`. 

##### Adding/altering endpoints
If the changes include adding a new endpoint to an application, please make certain that the endpoint is paired to a path defined in the urls.py file of that application. 
Testing endpoints can be done in various ways. One can: 

- Write mock tests
- Test it in the browser (as we are using the Django-rest-framework, its endpoints by default provide GUI  in the browser when called to; note that this only applicable if debug mode is set to true in the settings.py file), here the user can give POST data and easily see responses
- Test it via third-party application such as Postman

##### Adding conceptually new functionality 
If the added functionality is conceptually different to the existing applications (see below), then it's advised to create a new Django application for it. Details can be found on official Django documentation, however, in short, the new application will need to be registered in the settings.py folder. 

## General backend workflow 

1. HTTP request comes to an existing endpoint
2. Request is handled in some specific manner:
    - This can include simply querying the database
    - Can be a lot more complex, and can use methods such as _execute_rule_mining_pipeline_ 
3. Data returned via HTTP response 

## Applications in the backend
##### SECAAlgo
The heart of the backend, it includes the two largest features - the rule mining pipeline and the query functionality. Many endpoints make use of _execute_rule_mining_pipeline_ in some way.


The ‘Rule mining pipeline’ is a full 6 step process which results in the rule mining algorithm being properly set up and run with all the specified inputs.

1. The inputs revolve around several parameters which then change what is displayed in the output. What each input does specifically is explained in the documentation of the method.

2. Before doing anything else, it verifies that the input parameters are valid. If so, it begins with the 6 step pipeline:
    - Retrieving all the images that are in the correct session
    - Creating a tabular representation with all the retrieved images from the db
    - Performing rule mining on the resulting tabular representation set. Concept related filters are applied here.
    - Recreates the tabular representation to include the new rules
    - Computes statistical tests with the newly made tabular representation
    - Creates a structured response, displaying the resulting rules and classes as a structured output. The class related     filters are applied here.
3. Changes to db will affect the pipeline as it uses Images, Annotations, and Sessions table.

Adding and changing features in the rule mining pipeline should be done carefully, as it can be quite fickle. Make sure to add sufficient tests to ensure that the functionality is implemented correctly, and to ensure the other methods still function as intended. 

If it is felt that the current level of testing is not sufficient, more tests are always welcome.

The Query methods are methods which are made to simplify front end communication with other methods in the back end.
1. Query classes is a simple method which is used to look at Images, Annotations and Sessions in the database (but is quite outdated and needs to be updated if it is to be used).
2. Query rules allow for better communication with the rule mining pipeline. A list of all the inputs is visible in the documentation for the method. All the inputs to the query rules method are processed appropriately and fed into the pipeline.
3. Uquery is a method that allows for multiple queries to utilise the same endpoint if so desired.

Small TODO: Add proper outlines for other large methods in SECAAlgo


##### UserSECA
The UserSECA application defines the database for the User, and also manages authentication. Currently, authentication is done using Django-Rest-Framework TokenAuthentication; the framework handles creating and managing tokens for users. 

The User as of right now is quite simple, it extends the Django User model and adds only one new field, _is_developer_ (a boolean). 

In the near future, if Developer and Expert users are to be distinguished further, and more fields are required this can be quite easily. 


##### Wiki_SECA
The Wiki_SECA application is responsible for the wiki related endpoints and database interactions. It handles all the data related to Wiki pages. 

##### expert_questions_SECA
This application handles the endpoints for communication between the Experts and Developers, and the Wiki entries made by the Experts.

## All current endpoints (API)
The following are all the endpoints of the API exposed from the backend. For each of them, the URL is given, and the appropriate HTTP Request Method it listens to. To find out more about an endpoint, please look at the views.py file for the respective Django Application the endpoint is part of to find full documentation.

**SECAAlgo endpoints**
| URL                                             | Request Methods     |
|-------------------------------------------------|---------------------|
| api/SECAAlgo/Images/allImages/                  | GET                 |
| api/SECAAlgo/Matrix/matrix                      | GET                 |
| api/SECAAlgo/Matrix/images                      | GET                 |
| api/SECAAlgo/Explore/data_all_images            | GET                 |
| api/SECAAlgo/Explore/data_overall_explanations  | POST                |
| api/SECAAlgo/Explore/data_specific_explanations | POST                |
| api/SECAAlgo/Query/query/                       | POST                |
| api/SECAAlgo/Query/query_rules/                 | POST                |
| api/SECAAlgo/Query/uquery/                      | POST                |
| api/SECAAlgo/Query/query_specific/              | POST                |
| api/SECAAlgo/notes/                             | GET/POST/PUT/DELETE |
| api/SECAAlgo/UserProfile/predictions/           | GET                 |
| api/SECAAlgo/add_data/                          | POST                |
| api/SECAAlgo/add_image/                         | POST                |
| api/SECAAlgo/f1_scores/                         | POST                |

**UserSECA endpoints**
| URL                       | Request Method         |
|---------------------------|------------------------|
| api/UserSECA/get_sessions | POST                   |
| api/UserSECA/users        | GET, POST, PUT, DELETE |

**Wiki_SECA endpoints**
| URL                        | Request Method |
|----------------------------|----------------|
| api/Wiki/remove_wiki/      | DELETE         |
| api/Wiki/add_wiki/         | POST           |
| api/Wiki/expertBackground/ | GET            |
| api/Wiki/updateTitleIntro/ | PUT            |

**expert_questions_SECA endpoints**
|                   URL | Request Method         |
|----------------------:|------------------------|
| api/Expert/questions/ | GET, POST, DELETE, PUT |

**Misc endpoints**
| URL    | Request Method |
|--------|----------------|
| auth/  | POST           |
| admin/ | POST           |
