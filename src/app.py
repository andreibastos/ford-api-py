#!bin/python
# -*- coding: utf-8 -*-
"""
author: Andrei Bastos
organization: Labic/Ufes
data: 30/01/2018
"""

###################### Importações de Pacotes ##########################
from flask import Flask, jsonify, abort, request, url_for,  make_response
from flask_httpauth import HTTPBasicAuth
import datetime, json, re, os, mongoengine


######################### Configurações ##################################
auth = HTTPBasicAuth() 
app = Flask(__name__)
app.debug = True
app.threaded=True
app.config['SECRET_KEY'] = 'super-secret'

# Caminhos das rotas
path_default = "/api/"
path_default_documents = path_default + "document"
path_default_user = path_default + "user"

# Banco de dados
mongoengine.connect('ford')


####################### Criação de Classes #################################
class User(mongoengine.Document):
    email = mongoengine.StringField(required=True, unique=True)
    password = mongoengine.EmailField(required=True)
    first_name = mongoengine.StringField(required=True, max_length=50)
    last_name = mongoengine.StringField(max_length=50)

    # Criar pastas    
    def create_directory(self,name, source_id):
        try:
            source_document = Directory.objects.get(id=source_id)   
            if not source_document:
                raise InvalidUsage('not exist directory with id={0}'.format(source_id))
            
            name_regex = re.compile(name,  re.IGNORECASE)
            documents = Document.objects(source_document = source_document.id, name = name_regex)
            if documents:
                raise InvalidUsage('exist directory with name={0}'.format(name))                        

            return Directory(name=name, author = self, source_document=source_document, date_created=datetime.datetime.utcnow(), date_modified=datetime.datetime.utcnow())

        except Exception as identifier:
            raise InvalidUsage(identifier.message)

    # Buscar documentos pelo ID de uma pasta
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
    
    # Dicionário
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
    meta = {'allow_inheritance': True}

    # Dicionário
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
            directory['source_document'] = self.source_document.to_dict()
            
            
        
        return directory

class File(Document):
    source_document = mongoengine.ReferenceField(Document, reverse_delete_rule=mongoengine.CASCADE)
    meta = {'allow_inheritance': True}

class Process(Document):
    source_document = mongoengine.ReferenceField(Document, reverse_delete_rule=mongoengine.CASCADE)
    meta = {'allow_inheritance': True}

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

####################### Funções comuns #######################################
def datetime_to_timestamp(dt):    
    timestamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()    
    return int(timestamp)


######################## Erros ###############################################
@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):    
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

######################## Rotas ###############################################
################# Documentos #################################################
# Criar Documentos
@app.route(path_default_documents, methods=['POST'])
@auth.login_required
def add_document():        
    if not request.json or not 'type' in request.json:
        raise InvalidUsage('not exist type in post')

    # Criação de Pasta
    if request.json['type'] == 'directory':
        try:
            # Pega as informações do post
            name= request.json.get('name')
            source_id = request.json.get('source_id')            
            description = request.json.get('description')
            is_favorited = request.json.get('is_favorited') or False
            
            # verifica se tem source_id 
            if source_id:
                try:                    
                    directory = auth.user.create_directory(name=name,source_id=source_id) # cria a pasta
                    # atribute o resto das informações
                    directory.is_favorited = is_favorited 
                    directory.description = description
                    directory.save() # salva no banco de dados                        
                    return jsonify({'result': directory.to_dict()}), 201 #retorna para o usuario o diretório criado
                except Exception as identifier:
                    raise InvalidUsage(identifier.message)
            else:
                raise InvalidUsage('You must specify the source_id', status_code=400)
        except Exception as identifier:
            raise InvalidUsage(identifier.message, status_code=410)

# Pegar Documentos
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

# Editar Documentos
@app.route(path_default_documents+'<id>', methods=['PUT'])
@auth.login_required
def update_document(id_document):    
    pass
    # return jsonify({'document': document[0]})

# Deletar Documentos
@app.route(path_default_documents+'<id>', methods=['DELETE'])
@auth.login_required
def delete_document(id_document):
    pass


######################### Autenticação ##########################################
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


######################## Função Principal ######################################
if __name__ == '__main__':    
    app.run(host="0.0.0.0", port = os.environ.get('port', 5000))
    