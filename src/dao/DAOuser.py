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
collection_user = db['user']

def insert(user):
    try:        
        collection_user.insert_one(user)
    except Exception as identifier:
        raise identifier    

def update(user):
    try:
        collection_user.update_one({'id_user':user["id_user"]}, user)
    except Exception as identifier:
        raise identifier

def get(username):
    return collection_user.find_one({'username':username})

def delete(id_user):
    try:
        query = {'id_user':id_user}
        collection_user.delete_one(query)

    except Exception as identifier:
        raise identifier
    
    