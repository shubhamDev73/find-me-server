import os
import threading
from django.utils import timezone
from django.conf import settings
from django.core.management import call_command

from .models import Profile, Connect
from . import firebase


def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        profile = Profile.objects.create(user=instance)
        instance.new_token()

        t = threading.Thread(target=call_command, args=("ml", ), kwargs={"id": profile.id, "train": True})
        t.setDaemon(True)
        t.start()

def delete_model(sender, instance, **kwargs):
    os.remove(os.path.join(settings.ML_DIR, f"user{instance.id}.h5"))

def delete_zero_interest(sender, instance, created, **kwargs):
    if not instance.amount:
        instance.delete()

def on_connect_save(sender, instance, created, **kwargs):
    if created:
        chat_id = firebase.create_new_chat(instance.id)
        instance.chat_id = chat_id
        instance.save()
        firebase.create_connect_state(instance)
        firebase.send_notification(instance.user1, {'title': 'New connect!', 'body': 'You have got a new connect!'}, type='Found')
        firebase.send_notification(instance.user2, {'title': 'New connect!', 'body': 'You have got a new connect!'}, type='Found')

def on_access_pre_save(sender, instance, **kwargs):
    if instance.requested:
        in_db = sender.objects.get(pk=instance.pk)
        if not in_db.requested:
            firebase.send_notification(instance.other, {'title': 'New request!', 'body': 'You have got a new connect request!'}, type='Request')

def on_access_save(sender, instance, created, **kwargs):
    if created:
        firebase.send_notification(instance.me, {'title': 'New accesss!', 'body': 'You have got access to a new user profile!'}, type='Find')

class UpdateTime:

    attrs = {}
    methods = {}

    @classmethod
    def update_time(cls, sender, instance, **kwargs):
        present = (instance.pk != None)

        in_db = sender.objects.get(pk=instance.pk) if present else None
        for attr in cls.attrs:
            value = getattr(instance, attr)
            value_in_db = getattr(in_db, attr) if present else None
            if not isinstance(value, bool):
                value = value()
                value_in_db = value_in_db() if present else None
            if (present and value != value_in_db) or (not present and value):
                setattr(instance, cls.attrs[attr], timezone.localtime() if value else None)
                if attr in cls.methods:
                    cls.methods[attr](value, sender, instance, **kwargs)

class UpdateAccessTime(UpdateTime):

    def create_connect(value, sender, instance, **kwargs):
        if value:
            Connect.objects.create(user1=instance.me, user2=instance.other)
        else:
            try:
                connect = Connect.objects.get(active=True, user1=instance.me, user2=instance.other)
                connect.delete()
            except Connect.DoesNotExist:
                try:
                    connect = Connect.objects.get(active=True, user1=instance.other, user2=instance.me)
                    connect.delete()
                except Connect.DoesNotExist:
                    pass

    def send_request_notification(value, sender, instance, **kwargs):
        if value:
            firebase.send_notification(instance.other, {'title': 'New request!', 'body': 'You have got a new connection request!'}, type='Request')

    attrs = {'viewed': 'view_time', 'requested': 'request_time', 'connected': 'connect_time'}
    methods = {'connected': create_connect, 'requested': send_request_notification}

class UpdateConnectTime(UpdateTime):
    attrs = {'retained1': 'retain1_time', 'retained2': 'retain2_time', 'retained': 'retain_time'}
