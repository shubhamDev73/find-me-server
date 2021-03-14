from django.conf import settings
from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
initialize_app(cred)

def create_new_chat(connect_id):
    db = firestore.client()
    doc_ref = db.collection('chats').document()
    doc_ref.set({'connectId': connect_id})
    return doc_ref.id

def get_last_message(chat_id):
    db = firestore.client()
    messages = db.collection('chats')\
             .document(chat_id)\
             .collection('chats')\
             .order_by('timestamp', direction=firestore.Query.DESCENDING)\
             .limit(1).get()

    if not messages:
        return None

    message = messages[0]
    return {"id": message.id, **message.to_dict()}
