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

import datetime, json

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
    email = mongoengine.StringField(required=True, unique=True)
    password = mongoengine.StringField(required=True)
    first_name = mongoengine.StringField(required=True, max_length=50)
    last_name = mongoengine.StringField(max_length=50)
    
    def directory_create(self,name, source_id=None):        
        source_document = None
        if source_id:            
            source_document = Directory.objects.get(id=source_id)            
            if not source_document:
                raise InvalidUsage('not exist directory with id={0}'.format(source_id))                        
        else:              
            try:           
                source_document = Directory.objects.get(source_document=None)                
            except Directory.DoesNotExist:                
                source_document = Directory(name='root', description='root directory', source_document=None, date_created=datetime.datetime.utcnow(), date_modified=datetime.datetime.utcnow(), author=self )
                source_document.save()

        documents = Document.objects(source_document = source_document.id)                
        for document in documents:            
            if str(document.name).lower() == str(name).lower():
                raise InvalidUsage('exist directory with name={0}'.format(name))                        
        
            


        return Directory(name=name, author = self, source_document=source_document, date_created=datetime.datetime.utcnow(), date_modified=datetime.datetime.utcnow())

    def get_documents(self, name_or_id):
        source_document = None
        try:           
            source_document = Document.objects.get(name=name_or_id)
        except Document.DoesNotExist:
            try:
                source_document = Document.objects.get(id=name_or_id)                                
            except:
                raise 
        
        if source_document:
            documents = Document.objects.get(source_document=source_document)                
            return documents
        
    def delete_document(self,id):
        document = Document.objects.get(id=id, author = self)
        if document:
            document[0].delete()

    def delete_documents(self, ids):
        documents = Document.objects.get(author = self)
        for document in documents:
            document.delete()


class Document(mongoengine.Document):
    name = mongoengine.StringField(required=True)    
    is_favorited = mongoengine.BooleanField(default=False)
    author = mongoengine.ReferenceField(User, required=True, reverse_delete_rule=mongoengine.CASCADE)
    date_created = mongoengine.DateTimeField()
    date_modified = mongoengine.DateTimeField()
    space_disk =  mongoengine.IntField(default=0)
    description = mongoengine.StringField()
    tags = mongoengine.ListField(mongoengine.StringField(max_length=50),default=None)    
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
def get_document(name_or_id):    
    try:
        print request
        documents = auth.user.get_documents(name_or_id)                        
        if not documents:
            abort(404)
        return jsonify({'documents': json.loads(documents.to_json(ensure_ascii=False))})
    except Exception as identifier:
        print identifier        
        InvalidUsage(identifier.message)
   

@app.route(path_default_documents, methods=['POST'])
@auth.login_required
def create_document():
    if not request.json or not 'type' in request.json:
        raise InvalidUsage('not exist type in post.')

    if request.json['type'] == 'directory':
        try:
            name= request.json.get('name')
            source_id = request.json.get('source_id')            
            description = request.json.get('description')
            is_favorited = request.json.get('is_favorited') or False
            directory = auth.user.directory_create(name=name,source_id=source_id)                                    
            directory.is_favorited = is_favorited
            directory.description = description
            directory.save()
            return jsonify({'result': json.loads(directory.to_json(ensure_ascii=False))}), 201
        except Exception as identifier:
            raise InvalidUsage(identifier.message, status_code=410)       

@app.route(path_default_documents+'<id>', methods=['PUT'])
@auth.login_required
def update_document(id_document):    
    pass
    # return jsonify({'document': document[0]})

@app.route(path_default_documents+'<id>', methods=['DELETE'])
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
    