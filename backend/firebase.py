from django.conf import settings
from firebase_admin import credentials, firestore, initialize_app, db, messaging

from .models import Connect

cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
initialize_app(cred, {'databaseURL': 'https://findmetoo-c20a2-default-rtdb.firebaseio.com/'})

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

def get_unread_num(chat_id, me, last_read_time):
    db = firestore.client()
    messages = db.collection('chats')\
          .document(chat_id)\
          .collection('chats')\
          .where('user', '==', 3 - me)\
          .where('timestamp', '>', last_read_time)\
          .get()
    return len(messages)

def get_connect_state(connect_id, user):
    refs = Connect.objects.filter(active=True).filter(user1=user)
    for ref in refs:
        if ref.id != connect_id:
            return db.reference().child(f'{ref.id}-1').get()
    refs = Connect.objects.filter(active=True).filter(user2=user)
    for ref in refs:
        if ref.id != connect_id:
            return db.reference().child(f'{ref.id}-2').get()
    return {
        'online': False,
        'lastSeen': round(user.last_questionnaire_time.timestamp() * 1000),
        'typing': False
    }

def create_connect_state(connect):
    state = get_connect_state(connect.id, connect.user1)
    db.reference().child(f'{connect.id}-1').set({
        'online': state['online'],
        'lastSeen': state['lastSeen'],
        'typing': False,
    })

    state = get_connect_state(connect.id, connect.user2)
    db.reference().child(f'{connect.id}-2').set({
        'online': state['online'],
        'lastSeen': state['lastSeen'],
        'typing': False,
    })

def send_notification(profile, notification_dict, type):
    try:
        notification = messaging.Notification(**notification_dict)

        android_notification = messaging.AndroidNotification(**notification_dict, click_action='FLUTTER_NOTIFICATION_CLICK')
        android = messaging.AndroidConfig(notification=android_notification, data={'type': type})

        message = messaging.Message(notification=notification, android=android, data={'type': type}, token=profile.fcm_token)

        messaging.send(message)
    except:
        pass
