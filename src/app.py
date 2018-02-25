#!bin/python
# -*- coding: utf-8 -*-
"""
author: Andrei Bastos
organization: Labic/Ufes
data: 30/01/2018
"""

###################### Importações de Pacotes ##########################
from flask import Flask, jsonify, abort, request, url_for,  make_response, redirect, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.utils import secure_filename
import datetime, json, re, os, mongoengine


######################### Configurações ##################################
USER_FOLDER = '/home/andrei/ford/data/'
auth = HTTPBasicAuth() 
app = Flask(__name__)
app.debug = True
app.threaded=True
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024
app.config['SECRET_KEY'] = 'super-secret'
app.config['USER_FOLDER'] = USER_FOLDER

# Caminhos das rotas
route_default = "/api/"
route_default_documents = route_default + "document"
route_default_user = route_default + "user"

ALLOWED_EXTENSIONS = set(['txt', 'pdf','csv','json', 'png', 'jpg', 'jpeg', 'gif','zip'])

# Banco de dados
mongoengine.connect('ford')


####################### Criação de Classes #################################
class User(mongoengine.Document):
    email = mongoengine.EmailField(required=True, unique=True)
    password = mongoengine.StringField(required=True)
    first_name = mongoengine.StringField(required=True, max_length=60)
    last_name = mongoengine.StringField(max_length=50)
    system_path = mongoengine.StringField()
    
    

    # Criar pastas    
    def create_directory(self,name, source_document, is_favorited, description):
        try:
            field_name_folder = 'name'
            directory = Directory(name=name, author = self, source_document=source_document, description=description, is_favorited=is_favorited)            
            name_folder = directory.to_dict()[field_name_folder]
            if source_document:
                system_path = source_document.system_path
            else: 
                directory.save()
                system_path = self.system_path
                
            directory.system_path =  os.path.join(system_path,name_folder)
            
            
            try:
                if not os.path.exists(directory.system_path):
                    os.makedirs(directory.system_path) 
            except OSError as identifier:
                raise InvalidUsage(identifier.message)
            directory.save()

            return directory            
        except Exception as identifier:
            raise InvalidUsage(identifier.message)

    # Buscar documentos pelo ID de uma pasta
    def get_documents(self, id):
        source_document = None
        try:
            document = Document.objects.get(id=id, author = self)
            if isinstance(document, Directory):
                source_document = document 
                if source_document:                
                    try:
                        documents = Document.objects(source_document=source_document, author=self)
                        
                        if documents:
                            documents = [x.to_dict() for x in documents] 
                        else:
                            documents = list() 
                    except Document.DoesNotExist:                              
                        documents = list()
                    
                    return documents                                 
            if isinstance(document, File):                
                return document

        except Document.DoesNotExist:                        
            raise InvalidUsage('document not exist')
       
        
    # Deletar um documento pelo ID
    def delete_document(self,id):
        document = Document.objects.get(id=id, author = self)
        if document:
            document[0].delete()
    
    def upload_file(self, name,source_document, is_favorited, description, system_path, space_disk):
        return File(name=name, space_disk=space_disk, source_document=source_document,is_favorited=is_favorited,author=self, description=description, system_path=system_path)

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
    # author = mongoengine.ReferenceField(User, required=True)
    author = mongoengine.ReferenceField(User, required=True, reverse_delete_rule=mongoengine.CASCADE)
    date_created = mongoengine.DateTimeField(default=datetime.datetime.utcnow())
    date_modified = mongoengine.DateTimeField(default=datetime.datetime.utcnow())
    space_disk =  mongoengine.IntField(default=0)
    description = mongoengine.StringField()
    tags = mongoengine.ListField(mongoengine.StringField(max_length=50),default=None)    
    meta = {'allow_inheritance': True}
    system_path = mongoengine.StringField()

class Directory(Document):
    source_document = mongoengine.ReferenceField(Document, reverse_delete_rule=mongoengine.CASCADE )
          
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
        directory['system_path'] = self.system_path  
        if self.source_document:
            directory['source_id'] = self.source_document.to_dict()['id']         
        
        return directory

class File(Document):
    source_document = mongoengine.ReferenceField(Document, reverse_delete_rule=mongoengine.CASCADE)
    name = mongoengine.StringField(required=True, unique_with='source_document' )  

    meta = {'allow_inheritance': True}
    
    # Dicionário
    def to_dict(self):        
        file = dict()
        file['id'] = str(self.id)
        file['name'] = self.name
        file['type'] = 'file'                
        file['date_created'] = datetime_to_timestamp(self.date_created)
        file['date_modified'] =  datetime_to_timestamp(self.date_modified) 
        file['space_disk'] =  int(self.space_disk)
        file['description'] = self.description
        file['tags'] = self.tags
        file['author'] = self.author.to_dict()
        file['system_path'] = self.system_path  
        if self.source_document:
            file['source_id'] = self.source_document.to_dict()['id']
        return file

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
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

######################## Erros ###############################################
@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):    
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

######################## Rotas ###############################################
########### Documento #######################################################
# Criar Documento
@app.route(route_default_documents, methods=['POST'])
@auth.login_required
def add_document():
    
    if request.files and request.form:
        source_id = request.form.get('source_id')
        file_upload = request.files['file']
        is_favorited = request.form.get('is_favorited')
        description = request.form.get('description')
        

        if not file_upload:
            raise InvalidUsage('not file in form-data')
        
        if not source_id:
            raise InvalidUsage("not source_id in form-data")
                 
        try:
            source_document = Document.objects.get(id = source_id)
             
            if source_document:
                if file_upload and allowed_file(file_upload.filename):
                    filename = secure_filename(file_upload.filename)
                    space_disk = 0  
                    system_path = os.path.join(source_document.system_path, filename)            
                    file_uploaded = auth.user.upload_file(filename,source_document, is_favorited, description, source_document.system_path, space_disk)
                    
                    file_upload.save(system_path)
                    file_uploaded.space_disk = os.stat(system_path).st_size 
                    file_uploaded.save()

                    source_document.space_disk += file_uploaded.space_disk 
                    source_document.save()

                else:
                    raise InvalidUsage('extension is not valid or not exist file for upload')  
                return jsonify({'file_uploaded':file_uploaded.to_dict()})
            else:
                raise InvalidUsage("not exist document with id={0}".format(source_id))

        except Exception as identifier:
            raise InvalidUsage(identifier.message)  

    if  request.json:
    
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
                        source_document = Directory.objects.get(id=source_id)   
                        if not source_document:
                            raise InvalidUsage('not exist directory with id={0}'.format(source_id))

                        name_regex = re.compile(name,  re.IGNORECASE)
                        documents = Document.objects(source_document = source_document.id, name = name_regex)
                        if documents:
                            raise InvalidUsage('exist directory with name={0}'.format(name))                        
                        
                        directory = auth.user.create_directory(name,source_document, is_favorited, description) # cria a pasta
                                                                
                        return jsonify({'result': directory.to_dict()}), 201 #retorna para o usuario o diretório criado
                    except Exception as identifier:
                        raise InvalidUsage(identifier.message)
                else:
                    raise InvalidUsage('You must specify the source_id', status_code=400)
            except Exception as identifier:
                raise InvalidUsage(identifier.message)

        if request.json['type'] == 'file':
            try:
                # Pega as informações do arquivo
                name= request.json.get('name')
                source_id = request.json.get('source_id')            
                description = request.json.get('description')
                is_favorited = request.json.get('is_favorited') or False
                file_upload  = request.files
                print json.dumps(file_upload)
            except Exception as identifier:
                raise InvalidUsage(identifier.message)



# Pegar Documento
@app.route(route_default_documents, methods=['GET'])
@auth.login_required
def get_document():        
    try:
        _id = request.args.get('id', None)
        is_download = request.args.get('is_download',False).lower()=='true'

        print is_download
        if not _id:
            abort(400)
        documents = auth.user.get_documents(_id) 
        
        if isinstance(documents, File):            
            if is_download:      
                print documents.to_dict()

                return send_from_directory(documents.system_path,documents.name, as_attachment=True,attachment_filename=documents.name)

        

        return jsonify({'documents': documents})
    except Exception as identifier:
        raise InvalidUsage(identifier.message)

# Atualizar Documento
@app.route(route_default_documents+'<id>', methods=['PUT'])
@auth.login_required
def update_document(id_document):    
    pass

# Deletar Documento
@app.route(route_default_documents+'<id>', methods=['DELETE'])
@auth.login_required
def delete_document(id_document):
    pass

############################## UPLOADER ############################
# Upload file
@app.route(route_default_documents+'<id>', methods=['DELETE'])
@auth.login_required
def updload(id_document):
    pass


########### Usuário #######################################################
#Criar Usuário
@app.route(route_default_user, methods=['POST'])
def add_user():
    if not request.json or not 'email' in request.json:
        raise InvalidUsage('not exist email in post', status_code=400)
    
    try:
        # Pega as informações do post
        email = request.json.get('email')
        password = request.json.get('password')
        first_name = request.json.get('first_name')
        last_name = request.json.get('last_name')

        # criar o objeto usuário
        new_user = User(email = email, password = password, first_name=first_name, last_name=last_name)

        
        # salva o usuáro
        new_user.save()  

        
        new_user.system_path = os.path.join(app.config['USER_FOLDER'], new_user.to_dict()['first_name'] )

        if not os.path.exists(new_user.system_path):
            os.makedirs(new_user.system_path) 

        new_user.save()

        #verificar se o usuário já possui diretório root


        # criar o diretório root
        new_user.create_directory('root', None, False,'root directory') 
        
        return(jsonify({'user':new_user.to_dict()}))

    except Exception as identifier:
        raise InvalidUsage(identifier.message)

# Pegar Usuário
@app.route(route_default_user, methods=['GET'])
@auth.login_required
def get_user():
    return(jsonify({'user':auth.user.to_dict()}))


# Atualizar Usuário
@app.route(route_default_user, methods=['PUT'])
@auth.login_required
def update_user():
    if not request.json:
        raise InvalidUsage('you must insert no minimum a field to update user', status_code=400)
    
    # Pega as informações do post
    email = request.json.get('email')
    password = request.json.get('password')
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')

    if email:
        auth.user.email = email
    if password:
        auth.user.password = password
    if first_name:
        auth.user.first_name = first_name
    if last_name:
        auth.user.last_name = last_name

    auth.user.save()
    return(jsonify({'user':auth.user.to_dict()}))

# Deletar Usuário
@app.route(route_default_user, methods=['DELETE'])
@auth.login_required
def delete_user():
    global auth
    try:
        auth.user.delete()
        auth = HTTPBasicAuth() 
        return(jsonify({'sucess':1}))
    except Exception as identifier:
        raise InvalidUsage(identifier.message)

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
    if not os.path.exists(app.config['USER_FOLDER']):
        os.makedirs(app.config['USER_FOLDER'])    
    app.run(host="0.0.0.0", port = os.environ.get('port', 5000))
    