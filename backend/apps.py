from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save


class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):
        from .signals import create_user_profile, delete_zero_interest, UpdateAccessTime, UpdateConnectTime, UpdateQuestionnaireTime

        post_save.connect(create_user_profile, sender='auth.User')
        post_save.connect(delete_zero_interest, sender='backend.UserInterest')
        pre_save.connect(UpdateAccessTime.update_time, sender='backend.Access')
        pre_save.connect(UpdateConnectTime.update_time, sender='backend.Connect')
        pre_save.connect(UpdateQuestionnaireTime.update_time, sender='backend.PersonalityQuestionnaire')
