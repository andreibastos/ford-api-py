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

import datetime, json, re, os

# my modules
from dao import DAODocument

auth = HTTPBasicAuth()
app = Flask(__name__)
app.debug = True
app.threaded=True
app.config['SECRET_KEY'] = 'super-secret'

path_default = "/api/"
path_default_documents = path_default+"documents"
path_default_user = path_default+"user"

mongoengine.connect('ford')

class User(mongoengine.Document):
    email = mongoengine.StringField(required=True, unique=True)
    password = mongoengine.EmailField(required=True)
    first_name = mongoengine.StringField(required=True, max_length=50)
    last_name = mongoengine.StringField(max_length=50)


    # Criar pastas    
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
        
        name_regex = re.compile(name,  re.IGNORECASE)            
        documents = Document.objects(source_document = source_document.id, name = name_regex)             
        if documents:
            raise InvalidUsage('exist directory with name={0}'.format(name))                        

        return Directory(name=name, author = self, source_document=source_document, date_created=datetime.datetime.utcnow(), date_modified=datetime.datetime.utcnow())

    # Buscar documentos pelo ID
    def get_documents(self, id):
        source_document = None
        try:
            source_document = Document.objects.get(id=id, author = self)                                    
        except Document.DoesNotExist:                        
            raise InvalidUsage('directory not exist')
            

        if source_document:
            try:
                documents = Document.objects.get(source_document=source_document, author=self)                                
            except Document.DoesNotExist:            
                documents = Document()
        return documents

    # Deletar um documento pelo ID
    def delete_document(self,id):
        document = Document.objects.get(id=id, author = self)
        if document:
            document[0].delete()

    # Deletar multiplos documentos pelo ID
    def delete_documents(self, ids):
        documents = Document.objects.get(author = self)
        for document in documents:
            document.delete()
    
    def to_dict(self):
        user = dict()
        user['id'] = str(self.id)
        user['email'] = str(self.email)        
        user['first_name'] = str(self.first_name)
        user['last_name'] = str(self.last_name)
        return user



class Document(mongoengine.Document):
    name = mongoengine.StringField(required=True)    
    is_favorited = mongoengine.BooleanField(default=False)
    author = mongoengine.ReferenceField(User, required=True, reverse_delete_rule=mongoengine.CASCADE)
    date_created = mongoengine.DateTimeField(default=datetime.datetime.utcnow())
    date_modified = mongoengine.DateTimeField(default=datetime.datetime.utcnow())
    space_disk =  mongoengine.IntField(default=0)
    description = mongoengine.StringField()
    tags = mongoengine.ListField(mongoengine.StringField(max_length=50),default=None)    
    meta = {'allow_inheritance': True}

    


class Directory(Document):
    source_document = mongoengine.ReferenceField(Document, reverse_delete_rule=mongoengine.CASCADE)        
    

    def to_dict(self):        
        directory = dict()
        directory['id'] = str(self.id)
        directory['name'] = self.name
        directory['type'] = 'directory'                
        directory['date_created'] = datetime_to_timestamp(self.date_created)
        directory['date_modified'] =  datetime_to_timestamp(self.date_modified) 
        directory['space_disk'] =  int(self.space_disk)
        directory['description'] = self.description
        directory['tags'] = self.tags
        directory['author'] = self.author.to_dict()  
        if self.source_document:                         
            print self.source_document.id
            source_document =  Directory.objects.get(id=self.source_document.id).to_dict()
            
                
            directory['source_document'] = source_document
            
            
        
        return directory

    
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

def datetime_to_timestamp(dt):    
    timestamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()    
    return int(timestamp)


def create_document():
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
            return jsonify({'result': directory.to_dict()}), 201
        except Exception as identifier:
            raise InvalidUsage(identifier.message, status_code=410)       

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):    
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route(path_default_documents, methods=['GET'])
@auth.login_required
def get_document():        
    try:
        _id = request.args.get('id', '')
        if not _id:
            abort(400)


        documents = auth.user.get_documents(_id)    
            
        if len(documents)==0:
            abort(404)

        print documents

        

        return jsonify({'documents': documents})
    except Exception as identifier:          
        raise InvalidUsage(identifier.message)
    
   

@app.route(path_default_documents, methods=['POST'])
@auth.login_required
def documention():        
    if not request.json or not 'type' in request.json:
        raise InvalidUsage('not exist type in post')            
    return create_document()

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
    app.run(host="0.0.0.0", port = os.environ.get('port', 5000))
    