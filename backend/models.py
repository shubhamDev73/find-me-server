from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    expired = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def new_token(self, length=100):
        import hashlib
        import random
        import string

        random_string = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=length))
        present = True
        while present:
            try:
                token = hashlib.sha256(random_string.encode('utf-8')).hexdigest()
                Profile.objects.get(token=token)
            except Profile.DoesNotExist:
                present = False

        self.token = token
        self.expired = False
        self.save()
        return self

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        profile.new_token()
