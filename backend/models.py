from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        profile.token = create_token()
        profile.save()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.token = create_token()
    instance.profile.save()

def create_token(length=100):
    import hashlib
    import random
    import string

    random_string = ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
    present = True
    while present:
        try:
            token = hashlib.sha256(random_string.encode('utf-8')).hexdigest()
            Profile.objects.get(token=token)
        except Profile.DoesNotExist:
            present = False
    return token
