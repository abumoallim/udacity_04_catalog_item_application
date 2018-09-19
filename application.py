from flask import Flask, session, render_template
from flask import request, redirect, jsonify, url_for, make_response
from database_setup import db, Catalog, CatalogItem, User
from flask_login import LoginManager, current_user
from flask_login import login_required, login_user, logout_user
from flask import g
from flask import flash
from requests_oauthlib import OAuth2Session
import os
import datetime
import jwt
from flask_migrate import Migrate
import json
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemcatalog.db'
db.init_app(app)
Migrate(app, db, render_as_batch=True)
app.secret_key = "H7DPWNMQOVKSYUAmufrySUYYUS"

# oauthlib - oauth2 must utilize https workaround
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


# initiate login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class Auth:
    """Google Project Credentials"""
    CLIENT_ID = ('747601484914-urhn3gji4cjahmgqllcnajnbs44oi3p2'
                 '.apps.googleusercontent.com')
    CLIENT_SECRET = 'Byc6YxroZYbPN4kRNOhtSXgZ'
    REDIRECT_URI = 'http://localhost:5000/gCallback'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']


# Loads Users
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# This will call before each to see if current_user is not None
@app.before_request
def before_request():
    g.user = current_user


# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    if username and password and email:
        user = User()
        user.email = request.form['email']
        user.password = request.form['password']
        user.username = request.form['username']
        db.session.add(user)
        db.session.commit()
        flash('User successfully registered')
        return redirect(url_for('login'))
    else:
        flash('Please fill all the fields to register')
        return redirect(url_for('register'))


# User Normal login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        google = get_google_auth()
        auth_url, state = google.authorization_url(
            Auth.AUTH_URI, access_type='offline')
        session['oauth_state'] = state
        return render_template('login.html', auth_url=auth_url)
    username = request.form['username']
    password = request.form['password']
    registered_user = User.query.filter_by(
        username=username, password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid', 'error')
        return redirect(url_for('login'))
    login_user(registered_user)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))


# User Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# User Google Login
def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            state=state,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth


# Google sign in callback
@app.route('/gCallback')
def callback():
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('index'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        google = get_google_auth(state=session['oauth_state'])
        try:
            token = google.fetch_token(
                Auth.TOKEN_URI,
                client_secret=Auth.CLIENT_SECRET,
                authorization_response=request.url)
        except Exception:
            return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        resp = google.get(Auth.USER_INFO)
        print(resp)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            user = User.query.filter_by(email=email).first()
            print(user)
            if user is None:
                user = User()
                user.email = email
            user.username = user_data['email']
            print(token)
            user.social_auth_token = json.dumps(token)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
        return 'Could not fetch your information.'


# Show all catalogs
@app.route('/')
@app.route('/catalog/')
def index():
    catalogs = Catalog.query.all()
    catalogItems = CatalogItem.query.order_by(CatalogItem.id.desc()).all()
    return render_template('index.html',
                           catalogs=catalogs,
                           catalogItems=catalogItems)


# Create a new Catalog
@app.route('/catalog/new/', methods=['GET', 'POST'])
@login_required
def addCatalog():
    if request.method == 'POST':
        newCatalog = Catalog(name=request.form['catalog'],
                             created_by=current_user)
        db.session.add(newCatalog)
        db.session.commit()
        flash('Catalog Added Succesfully')
        return redirect(url_for('index'))
    else:
        return render_template('add_catalog.html', method="ADD")


# Updating catalog
@app.route('/catalog/new/<int:catalog_id>/edit', methods=['GET', 'POST'])
@login_required
def updateCatalog(catalog_id):
    catalog = Catalog.query.filter_by(id=catalog_id).first()
    if request.method == 'POST':
        if catalog.created_by == current_user:
            if request.form['catalog']:
                catalog.name = request.form['catalog']
                db.session.add(catalog)
                db.session.commit()
                flash('Catalog Updated Succesfully')
                return redirect(url_for('index'))
        else:
            flash('Only creator of this category can update')
            return render_template('add_catalog.html',
                                   catalog=catalog,
                                   method="UPDATE")
    else:
        return render_template('add_catalog.html',
                               catalog=catalog,
                               method="UPDATE")


# Deleting catalog
@app.route('/catalog/<int:catalog_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCatalog(catalog_id):
    catalog = Catalog.query.filter_by(id=catalog_id).first()
    catalogItems = CatalogItem.query.filter_by(catalog_id=catalog_id).all()
    if request.method == "POST":
        if catalog.created_by == current_user:
            for items in catalogItems:
                db.session.delete(items)
            db.session.delete(catalog)
            db.session.commit()
            flash('Catalog Deleted Succesfully')
            return redirect(url_for('index'))
        else:
            flash('Only creator of this category can delete')
            return render_template('delete.html',
                                   catalog=catalog,
                                   delete_type="catalog")
    else:
        return render_template('delete.html',
                               catalog=catalog,
                               delete_type="catalog")


# Showing items for particular Catalog
@app.route('/catalog/<int:catalog_id>/items/')
def catalogDetails(catalog_id):
    catalog = Catalog.query.filter_by(id=catalog_id).first()
    catalogItems = CatalogItem.query.filter_by(catalog_id=catalog_id).all()
    return render_template('catalog_item.html',
                           catalog=catalog,
                           catalogItems=catalogItems)


# Creating new item in catalog
@app.route('/catalog/<int:catalog_id>/item/new', methods=['GET', 'POST'])
@login_required
def addItem(catalog_id):
    if request.method == 'POST':
        catalog = Catalog.query.filter_by(id=catalog_id).first()
        if catalog.created_by == current_user:
            newItem = CatalogItem(name=request.form['item_name'],
                                  description=request.form['item_description'],
                                  catalog_id=request.form['catalog_select'])
            db.session.add(newItem)
            db.session.commit()
            flash('Item Added Succesfully')
            return redirect(url_for('catalogDetails',
                            catalog_id=newItem.catalog_id))
        else:
            flash('Only creator of this category can add the item')
            catalog = Catalog.query.filter_by(id=catalog_id).first()
            items = CatalogItem.query.filter_by(catalog_id=catalog_id).all()
            return render_template('catalog_item.html',
                                   catalog=catalog,
                                   catalogItems=items)
    else:
        catalogs = Catalog.query.all()
        catalog = Catalog.query.filter_by(id=catalog_id).first()
        return render_template('add_item.html',
                               catalogs=catalogs,
                               catalog=catalog,
                               method="ADD")


# Updating item
@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/edit/',
           methods=['GET', 'POST'])
@login_required
def updateItem(catalog_id, item_id):
    catalogItem = CatalogItem.query.filter_by(id=item_id).first()
    if request.method == 'POST':
        selectedCatalog = request.form['catalog_select']
        catalog = Catalog.query.filter_by(id=catalog_id).first()
        select = Catalog.query.filter_by(id=selectedCatalog).first()
        user = current_user
        if catalog.created_by == user and select.created_by == user:
            if request.form['item_name']:
                catalogItem.name = request.form['item_name']
            if request.form['item_description']:
                catalogItem.description = request.form['item_description']
            if selectedCatalog:
                catalogItem.catalog_id = selectedCatalog
            db.session.add(catalogItem)
            db.session.commit()
            flash('Item Updated Succesfully')

            return redirect(url_for('catalogDetails',
                            catalog_id=catalogItem.catalog_id))
        else:
            if catalog.created_by != current_user:
                flash('Only creator of this category can edit the item')
            else:
                flash('Catalog you selected is not owned by you')
            catalog = Catalog.query.filter_by(id=catalog_id).first()
            items = CatalogItem.query.filter_by(catalog_id=catalog_id).all()
            return render_template('catalog_item.html',
                                   catalog=catalog,
                                   catalogItems=items)

    else:
        catalogs = Catalog.query.all()
        catalog = Catalog.query.filter_by(id=catalog_id).first()
        return render_template('add_item.html',
                               catalogs=catalogs,
                               catalog=catalog,
                               catalogItem=catalogItem,
                               method="UPDATE")


# Deleting item
@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/delete/',
           methods=['GET', 'POST'])
@login_required
def deleteItem(catalog_id, item_id):
    catalogItem = CatalogItem.query.filter_by(id=item_id).first()
    if request.method == 'POST':
        catalog = Catalog.query.filter_by(id=catalog_id).first()
        if catalog.created_by == current_user:
            db.session.delete(catalogItem)
            db.session.commit()
            flash('Item Deleted Succesfully')

            return redirect(url_for('catalogDetails',
                            catalog_id=catalogItem.catalog_id))
        else:
            flash('Only creator of this category can delete the item')
            catalog = Catalog.query.filter_by(id=catalog_id).first()
            items = CatalogItem.query.filter_by(catalog_id=catalog_id).all()
            return render_template('catalog_item.html',
                                   catalog=catalog,
                                   catalogItems=items)
    else:
        return render_template('delete.html',
                               catalog_id=catalog_id,
                               catalogItem=catalogItem,
                               delete_type="item")


# Showing item details
@app.route('/catalog/<int:catalog_id>/item/<item_id>/')
@login_required
def itemDetails(catalog_id, item_id):
    catalog = Catalog.query.filter_by(id=catalog_id).first()
    catalogItem = CatalogItem.query.filter_by(id=item_id).first()
    return render_template('item_display.html',
                           catalogItem=catalogItem,
                           catalog=catalog)


# APIs
# Custom Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'authorization_token' in request.headers:
            token = request.headers['authorization_token']
        if not token:
            return jsonify({'message': 'Login Required!'}), 401
        try:
            data = jwt.decode(token, app.secret_key)
            current_user = User.query.filter_by(id=data['id']).first()
        except Exception:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# Login
@app.route('/api/login', methods=['POST'])
def restLogin():
    username = request.args.get('username')
    password = request.args.get('password')

    if not username or not password:
        return make_response('Params not found', 401)

    user = User.query.filter_by(username=username).first()

    if not user:
        return make_response('Could not verify', 401)

    registered_user = User.query.filter_by(
        username=username, password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid', 'error')
        return redirect(url_for('login'))
    token = jwt.encode({'id': user.id}, app.secret_key)
    return jsonify({'token': token.decode('UTF-8')})


# Get Catalogs
@app.route('/catalog/JSON/')
def catalogs_json():
    catalogs = Catalog.query.all()
    return jsonify([c.serialize for c in catalogs])


# Get Particular Category
@app.route('/catalog/<int:catalog_id>/JSON/')
def catalog_json(catalog_id):
    catalog = Catalog.query.filter_by(id=catalog_id).first()
    return jsonify(catalog.serialize)


# Get Particular Item
@app.route('/item/<int:item_id>/JSON/')
def items_json(item_id):
    catalogItem = CatalogItem.query.filter_by(id=item_id).first()
    return jsonify(catalogItem.serialize)


# Create a new Catalog
@app.route('/api/catalog/new/', methods=['POST'])
@token_required
def addCatalogAPI(current_user):
        catalog_name = request.args.get('catalog_name')
        newCatalog = Catalog(name=catalog_name,
                             created_by=current_user)
        db.session.add(newCatalog)
        db.session.commit()
        return jsonify(id=newCatalog.id, name=newCatalog.name)


# Updating catalog
@app.route('/api/catalog/edit/', methods=['POST'])
@token_required
def updateCatalogAPI(current_user):
    catalog_id = request.args.get('catalog_id')
    updateCatalog = Catalog.query.filter_by(id=catalog_id).first()
    if request.method == 'POST':
        if updateCatalog.created_by == current_user:
            if request.args.get('catalog_name'):
                updateCatalog.name = request.args.get('catalog_name')
                db.session.add(updateCatalog)
                db.session.commit()
                return jsonify(id=updateCatalog.id, name=updateCatalog.name)
        else:
            return jsonify({'message': 'You are not ' +
                            'authorized to update this catalog!'}), 401


# Deleting catalog
@app.route('/api/catalog/delete/', methods=['POST'])
@token_required
def deleteCatalogAPI(current_user):
    catalog_id = request.args.get('catalog_id')
    catalog = Catalog.query.filter_by(id=catalog_id).first()
    catalogItems = CatalogItem.query.filter_by(catalog_id=catalog_id).all()
    if request.method == "POST":
        if catalog.created_by == current_user:
            for items in catalogItems:
                db.session.delete(items)
            db.session.delete(catalog)
            db.session.commit()
            return jsonify('Catalog Deleted Succesfully')
        else:
            return jsonify({'message': 'You are not ' +
                            'authorized to delete this catalog!'}), 401


# Showing items for particular Catalog
@app.route('/api/catalog/items/', methods=['GET', 'POST'])
@token_required
def catalogDetailsAPI(current_user):
    catalog_id = request.args.get('catalog_id')
    catalogItems = CatalogItem.query.filter_by(catalog_id=catalog_id).all()
    return jsonify([c.serialize for c in catalogItems])


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
