from django.conf import settings
from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
initialize_app(cred)

def create_new_chat(connect_id):
    db = firestore.client()
    doc_ref = db.collection('chats').document()
    doc_ref.set({'connectId': connect_id})
    return doc_ref.id
