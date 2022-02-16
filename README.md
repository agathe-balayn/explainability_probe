# Initial explanation

In order to view the project, you need to run both the backend and the frontend. The following explains how to set up both. 

## Setting up the backend

### Installation
in the backend directory, you can run:

#### `virtualenv env`  
(For windows) `env\Scripts\activate`\
(For OS/Linux) `source env\bin\activate`, 
#### `pip install -r requirements.txt`

To set up a virtual environment called env, activate it, and install all 
the necessary requirements for the backend to run properly.

If you want to deactivate the virtual environment, from inside it simply enter `deactivate` into the terminal.

### Activating the virtual environment
From a backend directory with a virtual environment named environment, you can start it
by running \
`environment\Scripts\activate` for windows \
`source env\Scripts\activate` for OS/Linux

and deactivate it by entering `deactivate`

### Before starting the server

You will only need to do this step once, or if you make changes to the database (by changing the models.py files)

`python manage.py makemigrations` \
`python manage.py migrate`

#### Troubleshooting
In case of an error white running `makemigrations` or `migrate`, try deleting the migration files, which can be found in
`/backend/<AppName>/migrations`. You can delete all files there except `__init.py__`. `<AppName>` is for example `SECAAlgo` After removing the files run the commands above again.

### Starting the server
From inside an active virtual environment with the requirements installed, run:
`python manage.py runserver`

to start the server. To stop the server from running, simply press ctrl + c.
### Django docs
In case you want more information about django, which is the framework used for the backend, you can consult the [Django Documentation](https://www.djangoproject.com/)

## Setting up the frontend

### Setup the dependencies

Before you can run the frontend, you first need to install the dependencies with:\
`npm install`

### Starting the frontend

To run the app in development mode you can use:\
`npm start`
which opens [http://localhost:3000](http://localhost:3000) in the browser, or you can go to the address manually if it doesn't open automatically.

The page will reload if you make edits.\
You will also see any errors in the console.

### React and ant.design docs

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app) and 
for the design [Ant Design](https://ant.design/) was used. To learn more about React, check out the [React documentation](https://reactjs.org/) or [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

### More information about project

More detailed explanations of the frontend and backend can be found in `./frontend.md` and `./backend.md`
