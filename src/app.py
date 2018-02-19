#!bin/python
# -*- coding: utf-8 -*-
"""
author: Andrei Bastos
organization: Labic/Ufes
data: 30/01/2018
"""


from flask import Flask, jsonify, abort, request, url_for,  make_response
from flask_httpauth import HTTPBasicAuth

import bson
from dao import DAODocument

auth = HTTPBasicAuth()
app = Flask(__name__)

app.debug = True
app.threaded=True
app.config['SECRET_KEY'] = 'super-secret'

path_default = "/ford/api/v1.0/"
path_default_documents = path_default+"documents/"
path_default_user = path_default+"user/"

class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

users = [
    User(1, 'user1', 'abcxyz'),
    User(2, 'user2', 'abcxyz'),
]

users = [
    {'id_user':0, 'username':'andrei', 'password':'123'},
    {'id_user':1, 'username':'bianca', 'password':'123'},
    {'id_user':2, 'username':'roberto', 'password':'123'}   
]

def verify_user(username):    
    for user in users:
        if user.get('username') == username:
            return user['password']
    return None

def get_id_user(username):
    for user in users:
        if user.get('username') == username:
            return user['id_user']

documents = [
    {
        'id_document': 1,
        'id_user':0,
        'type':'directory',
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    }    
]

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = True
        rv['code'] = self.status_code
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route(path_default_documents, methods=['GET'])
@auth.login_required
def get_documents():        
    id_user = get_id_user(auth.username())        
    source_id = request.args.get('source_id', default = 0, type = int)
    documents = []
    try:        
        documents = DAODocument.get_documents(id_user=id_user,source_id=source_id)                        
        return jsonify({'documents': documents})
        
    except Exception as identifier: 
        raise InvalidUsage(identifier.message, status_code=410)       
        
    

@app.route(path_default_documents+'<int:id_document>', methods=['GET'])
@auth.login_required
def get_document(id_document):
    document = [document for document in documents if document['id'] == id_document]
    if len(document) == 0:
        abort(404)
    return jsonify({'document': document[0]})

@app.route(path_default_documents, methods=['POST'])
@auth.login_required
def create_document():
    id_user = get_id_user(auth.username())     
    
    def create_directory(request):        
        directory = { 
        'id_user':id_user,       
        'type':'directory', 
        'name': request['name'],
        'source_id': request.get('source_id') or  0,
        'description': request.get('description'),
        'is_favorited':request.get('is_favorited') or  False
        }
        return directory

    if not request.json or not 'type' in request.json:
        abort(400)       

    if request.json['type'] == 'directory':
        try:            
            directory = create_directory(request.json)            
            result = DAODocument.insert(directory)
        except Exception as identifier:
            raise InvalidUsage(identifier.message, status_code=410)       
        
    
    return jsonify({'result': result}), 201

@app.route(path_default_documents+'<int:id_document>', methods=['PUT'])
@auth.login_required
def update_document(id_document):
    document = [document for document in documents if document['id'] == id_document]
    if len(document) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not unicode:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    document[0]['title'] = request.json.get('title', document[0]['title'])
    document[0]['description'] = request.json.get('description', document[0]['description'])
    document[0]['done'] = request.json.get('done', document[0]['done'])
    return jsonify({'document': document[0]})

@app.route(path_default_documents+'<int:id_document>', methods=['DELETE'])
@auth.login_required
def delete_document(id_document):
    document = [document for document in documents if document['id'] == id_document]
    if len(document) == 0:
        abort(404)
    documents.remove(document[0])

def make_public_document(document):
    new_document = {}
    for field in document:
        if field == 'id':
            new_document['uri'] = url_for('get_document', id_document=document['id'], _external=True)
        else:
            new_document[field] = document[field]
    return new_document

@auth.get_password
def get_password(username):    
    password = verify_user(username)        
    return password

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

if __name__ == '__main__':    
    app.run(host="0.0.0.0")