#!/user/bin/env python3
import datetime
from flask import Flask, render_template, url_for, request, redirect, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Item, Users
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from flask import jsonify
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/catalog/catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

engine = create_engine('postgresql://catalog:catalog@localhost/catalog')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Route for login page
# Create anti-forgery state token
@app.route('/catalog/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Route for logout status page
@app.route('/catalog/logout')
def logout():
    flash("You are now logged out of the Catalog Application")
    return render_template('logout.html')


# Route to validate login credentials
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/catalog/catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already\
            connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists in the db otherwise add new user to the local db
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome! '
    output += login_session['username']
    output += '!</h1>'
    flash("you are now logged in to the Catalog application")
    print ("done!")
    return output


# User Helper Functions
def createUser(login_session):
    newUser = Users(name=login_session['username'], email=login_session
                    ['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(Users).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(Users).filter(Users.id == user_id).one()
    #user = session.query(Users).filter(Users.id.ilike(user_id)).one()
    return user


def getUserID(email):
    try:
        user = session.query(Users).filter(Users.email == email).one()
        #user = session.query(Users).filter(Users.email.ilike(email)).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login session.
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print ('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %\
          login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print ('result is ')
    print (result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('logout'))
    else:
        response = make_response(json.dumps('Failed to revoke token for \
            given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Category Information
@app.route('/catalog/<cat_name>/item/JSON')
def categoryItemJSON(cat_name):
    cats = session.query(Category).all()
    category = session.query(Category).filter(Category.name == cat_name).one()
    #category = session.query(Category).filter(Category.name.ilike(cat_name)).one()
    items = session.query(Item).filter_by(cat_id=category.id).all()
    return jsonify(CategoryItems=[i.serialize for i in items])


# Route for main catalog page
@app.route('/')
@app.route('/catalog/')
def categoryList():
    last_item = []
    cats = session.query(Category).all()
    for elem in cats:
        last_item.append(session.query(Item).filter(Item.cat_id == elem.id).
                         order_by(desc(Item.dateadded)).first())
    return render_template('category.html', cats=cats, last_item=last_item)


# Route for specific category item list
@app.route('/catalog/<cat_name>/')
def catItemList(cat_name):
    cats = session.query(Category).all()
    category = session.query(Category).filter(Category.name == cat_name).one()
    #category = session.query(Category).filter(Category.name.ilike(cat_name)).one()
    items = session.query(Item).filter_by(cat_id=category.id)
    count = items.count()
    return render_template('items.html', cats=cats, category=category,
                           items=items, count=count)


# Route for an item list description
@app.route('/catalog/<cat_name>/<item_name>/')
def itemDescription(cat_name, item_name):
    cat = session.query(Category).filter(Category.name == cat_name).one()
    #cat = session.query(Category).filter(Category.name.ilike(cat_name)).one()
    item = session.query(Item).filter(Item.name == item_name).one()
    #item = session.query(Item).filter(Item.name.ilike(item_name)).one()
    creator = getUserInfo(item.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('public_descriptions.html', cat=cat,
                               item=item, creator=creator)
    else:
        return render_template('descriptions.html', cat=cat, item=item,
                               creator=creator)


# Route to add a new item to a category
@app.route('/catalog/<cat_name>/new/', methods=['GET', 'POST'])
def newCatItem(cat_name):
    if 'username' not in login_session:
        return redirect('/catalog/login')
    cat = session.query(Category).filter(Category.name == cat_name).one()
    #cat = session.query(Category).filter(Category.name.ilike(cat_name)).one()
    if request.method == "POST":
        newItem = Item(name=request.form['name'], user_id=login_session
                       ['user_id'], dateadded=datetime.date.today(),
                       desc=request.form['desc'], cat_id=cat.id)
        session.add(newItem)
        session.commit()
        # Update latest item added to category
        categoryList()
        flash("A new catalog item (%s) has been created in the %s category" %
              (newItem.name, cat_name))
        return redirect(url_for('catItemList', cat_name=cat.name))
    else:
        return render_template("newcatitem.html", cat=cat, cat_id=cat.id)


# Route to delete an item from a category
@app.route('/catalog/<cat_name>/<item_name>/delete/', methods=['GET', 'POST'])
def deleteItem(cat_name, item_name):
    if 'username' not in login_session:
        return redirect('/catalog/login')
    itemToDelete = session.query(Item).filter(Item.name == item_name).one()
    #itemToDelete = session.query(Item).filter(Item.name.ilike(item_name)).one()
    if itemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to\
                delete this category item.  Please create your own category\
                item in order to delete.');}</script><body onload='myFunction()\
                ''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("%s has been removed from the %s item list!" % (item_name,
              cat_name))
        return redirect(url_for('catItemList', cat_name=cat_name))
    else:
        return render_template('delete_item.html', cat_name=cat_name,
                               item=itemToDelete)


# Route to edit an existing category item
@app.route('/catalog/<cat_name>/<item_name>/edit/', methods=['GET', 'POST'])
def editItem(cat_name, item_name):
    if 'username' not in login_session:
        return redirect('/catalog/login')
    editedItem = session.query(Item).filter(Item.name == item_name).one()
    #editedItem = session.query(Item).filter(Item.name.ilike(item_name)).one()
    if editedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('Your are not authorized\
        to edit this category item.  Please create your own category item in\
        order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['desc']:
            editedItem.desc = request.form['desc']
        session.add(editedItem)
        session.commit()
        flash("%s has been successfully edited!" % item_name)
        return redirect(url_for('catItemList', cat_name=cat_name))
    else:
        return render_template('edit_item.html', cat_name=cat_name,
                               item_name=item_name, item=editedItem)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
