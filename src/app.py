#!bin/python
# -*- coding: utf-8 -*-
"""
author: Andrei Bastos
organization: Labic/Ufes
data: 30/01/2018
"""

import bson

##requeriments
from flask import Flask, jsonify, abort, request, url_for,  make_response
from flask_httpauth import HTTPBasicAuth
import mongoengine

# my modules
from dao import DAODocument

auth = HTTPBasicAuth()
app = Flask(__name__)
app.debug = True
app.threaded=True
app.config['SECRET_KEY'] = 'super-secret'

path_default = "/api/"
path_default_documents = path_default+"documents/"
path_default_user = path_default+"user/"

mongoengine.connect('ford')

class User(mongoengine.Document):
    email = mongoengine.StringField(required=True)
    password = mongoengine.StringField(required=True)
    first_name = mongoengine.StringField(required=True, max_length=50)
    last_name = mongoengine.StringField(max_length=50)

class Document(mongoengine.Document):
    name = mongoengine.StringField(required=True)    
    is_favorited = mongoengine.BooleanField()
    author = mongoengine.ReferenceField(User, required=True, reverse_delete_rule=mongoengine.CASCADE)
    date_created = mongoengine.DateTimeField()
    date_modified = mongoengine.DateTimeField()
    space_disk =  mongoengine.IntField()
    described = mongoengine.StringField()
    tags = mongoengine.ListField(mongoengine.StringField(max_length=30))

    meta = {'allow_inheritance': True}


class Directory(Document):
    source_document = mongoengine.ReferenceField(Document, reverse_delete_rule=mongoengine.CASCADE)    
    
    
class File(Document):
    source_document = mongoengine.ReferenceField(Document, reverse_delete_rule=mongoengine.CASCADE)
    
    
class Process(Document):
    source_document = mongoengine.ReferenceField(Document, reverse_delete_rule=mongoengine.CASCADE)
    

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
    documents = []
    try:
        return jsonify({'documents': documents})        
    except Exception as identifier: 
        raise InvalidUsage(identifier.message, status_code=410)       

@app.route(path_default_documents+'<int:id_document>', methods=['GET'])
@auth.login_required
def get_document(id_document):
    document = ['andrei']
    if len(document) == 0:
        abort(404)
    return jsonify({'document': document[0]})

@app.route(path_default_documents, methods=['POST'])
@auth.login_required
def create_document():    
    def create_directory(request):    
        source_id = request.get('source_id')
        if source_id :            
            source_document = Directory.objects.get(id=source_id)
            if not source_document:
                raise InvalidUsage('not exist id={0}'.format(source_id))
        else:
            source_document = Directory(name='root', author = auth.user, source_document=None)

        print source_document.to_json()    
        source_document.save()
        
        
        return Directory( name= request['name'],            
            source_document = source_document,
            described= request.get('description'),
            is_favorited=request.get('is_favorited') or  False,
            author = auth.user
        )

    if not request.json or not 'type' in request.json:
        abort(400)       

    if request.json['type'] == 'directory':
        try:            
            directory = create_directory(request.json)                        
            directory.save()            
        except Exception as identifier:
            raise InvalidUsage(identifier.message, status_code=410)       
    
    
    return jsonify({'result': directory.to_json() }), 201

@app.route(path_default_documents+'<int:id_document>', methods=['PUT'])
@auth.login_required
def update_document(id_document):    
    pass
    # return jsonify({'document': document[0]})

@app.route(path_default_documents+'<int:id_document>', methods=['DELETE'])
@auth.login_required
def delete_document(id_document):
    pass

@auth.get_password
def get_password(email):     
    user = User.objects(email=email)
    if user:
        auth.user = user[0]        
        return user[0].password
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

if __name__ == '__main__':    
    app.run(host="0.0.0.0")
    