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
                             on_connect_save,\
                             on_access_pre_save,\
                             on_access_save

        post_save.connect(create_user_profile, sender='backend.User')
        post_delete.connect(delete_model, sender='backend.Profile')
        post_save.connect(delete_zero_interest, sender='backend.UserInterest')
        pre_save.connect(UpdateAccessTime.update_time, sender='backend.Access')
        pre_save.connect(UpdateConnectTime.update_time, sender='backend.Connect')
        post_save.connect(on_connect_save, sender='backend.Connect')
        pre_save.connect(on_access_pre_save, sender='backend.Access')
        post_save.connect(on_access_save, sender='backend.Access')
