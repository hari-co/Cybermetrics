import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import Depends

def initialize_firebase():
    if not firebase_admin._apps:
        credential = credentials.Certificate("utils/cybermetrics-18a4d-firebase-adminsdk-fbsvc-ff92be56de.json")
        firebase_admin.initialize_app(credential)
    return firestore.client()

def get_firebase_database():
    return initialize_firebase()
