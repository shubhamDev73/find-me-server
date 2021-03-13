from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save, post_delete


class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):
        from .signals import create_user_profile,\
                             delete_model,\
                             delete_zero_interest,\
                             UpdateAccessTime,\
                             UpdateConnectTime,\
                             create_firebase_chat,\
                             UpdateQuestionnaireTime

        post_save.connect(create_user_profile, sender='auth.User')
        post_delete.connect(delete_model, sender='backend.Profile')
        post_save.connect(delete_zero_interest, sender='backend.UserInterest')
        pre_save.connect(UpdateAccessTime.update_time, sender='backend.Access')
        pre_save.connect(UpdateConnectTime.update_time, sender='backend.Connect')
        post_save.connect(create_firebase_chat, sender='backend.Connect')
        pre_save.connect(UpdateQuestionnaireTime.update_time, sender='backend.PersonalityQuestionnaire')
