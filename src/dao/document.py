#!bin/python
# -*- coding: utf-8 -*-
"""
author: Andrei Bastos
organization: Labic/Ufes
data: 30/01/2018
"""

import pymongo
import datetime

client = pymongo.MongoClient()
db = client['ford']
collection_document = db['document']
collection_user = db['user']

def insert(document):
    try:
        document["date_created"] = datetime.datetime.utcnow()
        document["date_modified"] = document["date_created"] 
        collection_document.insert_one(document)
    except Exception as identifier:
        raise identifier    

def update(document):
    try:
        collection_document.update_one({'document_id':document["document_id"]}, document)
    except Exception as identifier:
        raise identifier

def get_documents(id_user,source_document_id=0):
    try:
        query = {'id_user':id_user, 'source_document_id':source_document_id}        
        result = [x for x in collection_document.find(query)]
        return result
    except Exception as identifier:
        raise identifier

def delete(document_id):
    try:
        query = {'document_id':document_id}
        collection_document.delete_one(query)

    except Exception as identifier:
        raise identifier
    