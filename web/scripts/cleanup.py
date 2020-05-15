import requests
import datetime
import ujson as json

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Document

import pyrebase


# todo : externalize this to an env. variable
elastic_host = 'https://site:5c360785f6ae0a10a77ab2b9a47cd356@gloin-eu-west-1.searchly.com'

es_client = Elasticsearch(hosts=[elastic_host])
es_query = Search(using=es_client).filter('range', created={'lt': 'now/d'})

firebase_config = {
    "apiKey": "AIzaSyC2m1MqHr7MWrrSJmVeV0u71WXXwUF_CsI",
    "authDomain": "catmatch-dev.firebaseapp.com",
    "databaseURL": "https://catmatch-dev.firebaseio.com",
    "storageBucket": "catmatch-dev.appspot.com",
}

firebase = pyrebase.initialize_app(firebase_config)

# Get a reference to the auth service
auth = firebase.auth()

# Log the user in
user = auth.sign_in_with_email_and_password("guillaume.patin@gmail.com", "firebase1378")

# Get a reference to the database service
db = firebase.database()

for hit in es_query.doc_type(Document).scan():
    all_users = db.child("users").get()
    for u in all_users.each():
        user_key = u.key()
        user_val = u.val()
        if user_val:
            deja_vu = user_val.get("deja_vu").split(',')
            if hit.sku in deja_vu:
                print(f"removed 'deja_vu' {hit.sku} from user {user_key}")
                deja_vu = [item for item in deja_vu if item!=hit.sku]
            tbv = user_val.get("tbv").split(',')
            if hit.sku in tbv:
                print(f"removed 'tbv' {hit.sku} from user {user_key}")
                tbv = [item for item in tbv if item!=hit.sku]
            # save user prefs
            db.child("users").child(user_key).update({
                    "deja_vu": ','.join(sorted(list(set(deja_vu)))),
                    "tbv": ','.join(sorted(list(set(tbv))))
                })
    print(f"deletion of {hit.sku}")
    hit.delete(using=es_client)

print(f"Cleanup done!")
