# Catalog-Item-Application

### Project Overview
>In this project, you'll work with authentication, APIs and Basic CRUD operation with Flask framework.

### Basic Functionality

  1. Login and Register
  2. Login with Google
  3. Add, Update, Delete Catalog (Authentication required)
  4. Add, Update, Delete Items in Particular Catalog(Authentication required)
  5. APIs for Add, Update, Delete Catalog with token based authentication

### How to Run?

#### PreRequisites:
  * [Python3](https://www.python.org/)
  * [Vagrant](https://www.vagrantup.com/)
  * [VirtualBox](https://www.virtualbox.org/)

#### Setup Project:
  1. Install Vagrant and VirtualBox
  2. Download or Clone [fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm) repository.
  3. Go to Catalog folder and put your project inside it. 

#### Launching the Virtual Machine:
  1. Launch the Vagrant VM inside Vagrant sub-directory in the downloaded fullstack-nanodegree-vm repository using command:
  
  ```
    $ vagrant up
  ```
  2. Then Log into this using command:
  
  ```
    $ vagrant ssh
  ```

### Run project

  1. From the vagrant directory inside the virtual machine,run application.py using:
    ```python application.py```

### APIs Usage

  1. Get All Catalogs : http://localhost:5000/api/catalog/ (Headers : authentication_token)
  2. Create Catalog  :  http://localhost:5000/api/catalog/new/ (Headers : authentication_token, Params : catalog_name)
  3. Update Catalog  :  http://localhost:5000/api/catalog/edit/ (Headers : authentication_token, Params : Params : catalog_id,catalog_name)
  4. Delete Catalog  :  http://localhost:5000/api/catalog/delete/ (Headers : authentication_token, Params : Params : catalog_id)
  5. Get All items for Catalog : http://localhost:5000/api/catalog/items/ (Headers : authentication_token, Params : Params : catalog_id,catalog_name)

  
#### Migration:

  1. ```pip install Flask-Migrate```
  2. ```export FLASK_APP="path to your application.py"```
  3. ```flask db init```
  4. ```flask db migrate```
  5. ```flask db upgrade```


