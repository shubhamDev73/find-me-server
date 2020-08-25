from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from algo.parameters import *

FLOAT_PRECISION = 4


class AvatarBase(models.Model):
    name = models.CharField(max_length=20)
    url = models.URLField()

    def __str__(self):
        return self.name

class Mood(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Avatar(models.Model):
    base = models.ForeignKey(AvatarBase, on_delete=models.CASCADE)
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)
    url = models.URLField()

    def __str__(self):
        return f"{str(self.base)} ({str(self.mood)})"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    expired = models.BooleanField(default=False)
    avatar = models.ForeignKey(Avatar, default=1, on_delete=models.PROTECT)
    _personality = models.CharField(max_length=120, default='0' * NUM_FACETS * FLOAT_PRECISION)

    def __str__(self):
        return str(self.user)

    def new_token(self):
        import secrets

        while True:
            try:
                token = secrets.token_hex(32)
                Profile.objects.get(token=token)
            except Profile.DoesNotExist:
                break

        self.token = token
        self.expired = False
        self.save()
        return self

    @property
    def facets(self):
        import numpy as np

        facets = [float(f"0.{self._personality[i * FLOAT_PRECISION : (i + 1) * FLOAT_PRECISION]}") for i in range(NUM_FACETS)]
        return np.array(facets, np.float)

    def get_personality(self):
        personality = self.facets.reshape((NUM_TRAITS, FACETS_PER_TRAIT)).sum(axis=1) / FACETS_PER_TRAIT
        return (personality - 0.5) * 2

    @staticmethod
    def construct_personality(personality, indices):
        return {Personality(index).name: personality[index] for index in indices}

    @property
    def personality(self):
        return Profile.construct_personality(self.get_personality(), range(NUM_TRAITS))

    @property
    def major_personality(self):
        personality = self.get_personality()
        indices = abs(personality).argsort()[NUM_TRAITS - NUM_DOMINANT_TRAITS:]
        return Profile.construct_personality(personality, indices)

    def save_facets(self, facets):
        self._personality = ''.join((f"%0.{FLOAT_PRECISION}f" % facets[i])[2:] for i in range(NUM_FACETS))
        self.save()
        return self

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        profile.new_token()

class PersonalityQuestionnaire(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    submit_time = models.DateTimeField(null=True)

    def __str__(self):
        return str(self.user)

class Interest(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f"{str(self.user)} - {str(self.interest)} : {self.amount}"

class Question(models.Model):
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return str(self.interest) + " - " + self.text

class Answer(models.Model):
    user_interest = models.ForeignKey(UserInterest, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return f"{str(self.user_interest)} - {str(self.question)} : {self.text}"

class Access(models.Model):

    class Meta:
        verbose_name_plural = "accesses"

    me = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='me')
    other = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='other')
    create_time = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    viewed = models.BooleanField(default=False)
    requested = models.BooleanField(default=False)
    connected = models.BooleanField(default=False)

    view_time = models.DateTimeField(null=True)
    request_time = models.DateTimeField(null=True)
    connect_time = models.DateTimeField(null=True)

    def __str__(self):
        return str(self.me.user) + " -> " + str(self.other.user)

class Connect(models.Model):
    user1 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='first_user')
    user2 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='second_user')
    create_time = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    retained1 = models.BooleanField(default=False)
    retained2 = models.BooleanField(default=False)

    retain1_time = models.DateTimeField(null=True)
    retain2_time = models.DateTimeField(null=True)
    retain_time = models.DateTimeField(null=True)

    def __str__(self):
        return str(self.user1.user) + " - " + str(self.user2.user)

    def retained(self):
        return self.retained1 and self.retained2
    retained.boolean = True
