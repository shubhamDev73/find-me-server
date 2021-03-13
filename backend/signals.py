import os
import threading
from django.utils import timezone
from django.conf import settings
from django.core.management import call_command

from .models import Profile, Connect
from .firebase import create_new_chat


def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        profile = Profile.objects.create(user=instance)
        profile.new_token()

        t = threading.Thread(target=call_command, args=("ml", ), kwargs={"id": profile.id, "train": True})
        t.setDaemon(True)
        t.start()

def delete_model(sender, instance, **kwargs):
    os.remove(os.path.join(settings.ML_DIR, f"user{instance.id}.h5"))

def delete_zero_interest(sender, instance, created, **kwargs):
    if not instance.amount:
        instance.delete()

def create_firebase_chat(sender, instance, created, **kwargs):
    if created:
        chat_id = create_new_chat(instance.id)
        instance.chat_id = chat_id
        instance.save()

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

    attrs = {'viewed': 'view_time', 'requested': 'request_time', 'connected': 'connect_time'}
    methods = {'connected': create_connect}

class UpdateConnectTime(UpdateTime):
    attrs = {'retained1': 'retain1_time', 'retained2': 'retain2_time', 'retained': 'retain_time'}

class UpdateQuestionnaireTime(UpdateTime):
    attrs = {'submitted': 'submit_time'}
