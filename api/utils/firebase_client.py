import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import Depends

def initialize_firebase():
    if not firebase_admin._apps:
        credential = credentials.Certificate("utils/cybermetrics.json")
        firebase_admin.initialize_app(credential)
    return firestore.client()

def get_firebase_database():
    return initialize_firebase()
