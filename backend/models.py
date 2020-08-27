import os
import numpy as np

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from algo.parameters import *
from algo.match import *

FLOAT_PRECISION = 4
NUM_USERS_ACCESS = 5


def avatar_base_path(instance, filename):
    return f'avatars/{instance.name.lower()}/{filename}'

def avatar_path(instance, filename):
    return f'avatars/{instance.base.name.lower()}/{instance.mood.name.lower()}/{filename}'

class AvatarBase(models.Model):
    name = models.CharField(max_length=20)
    image = models.ImageField(upload_to=avatar_base_path)

    @property
    def url(self):
        return f"{settings.HOST}{self.image.url}"

    def __str__(self):
        return self.name

class Mood(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Avatar(models.Model):
    base = models.ForeignKey(AvatarBase, on_delete=models.CASCADE)
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=avatar_path)

    @property
    def url(self):
        return f"{settings.HOST}{self.image.url}"

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
        facets = [float(f"0.{self._personality[i * FLOAT_PRECISION : (i + 1) * FLOAT_PRECISION]}") for i in range(NUM_FACETS)]
        return np.array(facets, np.float)

    def get_personality(self):
        return personality_from_facets(self.facets)

    @staticmethod
    def construct_personality(personality, indices):
        return {Personality(index).name: personality[index] for index in indices}

    @property
    def personality(self):
        return Profile.construct_personality(self.get_personality(), range(NUM_TRAITS))

    @property
    def major_personality(self):
        personality = self.get_personality()
        indices = np.flip(abs(personality).argsort())[:NUM_DOMINANT_TRAITS]
        return Profile.construct_personality(personality, indices)

    def save_facets(self, facets):
        self._personality = ''.join((f"%0.{FLOAT_PRECISION}f" % facets[i])[2:] for i in range(NUM_FACETS))
        self.save()
        return self

    def get_all_interests(self, answers=True):
        return [{
            **{
                "id": user_interest.interest.id,
                "name": user_interest.interest.name,
                "amount": user_interest.amount,
            },
            **({
                "answers": [
                    {"question": answer.question.text, "answer": answer.text} for answer in Answer.objects.filter(user_interest=user_interest)
                ]
            } if answers else {})
        } for user_interest in UserInterest.objects.filter(user=self)]

    def get_interest(self, pk):
        try:
            user_interest = UserInterest.objects.get(user=self, interest=pk)
            return {
                "name": user_interest.interest.name,
                "amount": user_interest.amount,
                "answers": [{"question": answer.question.text, "answer": answer.text} for answer in Answer.objects.filter(user_interest=user_interest)]
            }
        except UserInterest.DoesNotExist:
            return {'error': 'Interest not found.', 'code': 404}

    def get_info(self, interest_answers=True):
        return {
            "nick": self.user.username,
            "avatar": self.avatar.url,
            "personality": self.personality,
            "interests": self.get_all_interests(interest_answers),
            "mood": self.avatar.mood.name,
        }

    def get_partial_info(self):
        return {
            "avatar": self.avatar.url,
            "personality": self.major_personality,
            "mood": self.avatar.mood.name,
        }

    @property
    def interests(self):
        all_interests = self.get_all_interests(answers=False)
        vector = np.zeros(Interest.objects.last().pk, dtype=float)
        for interest in all_interests:
            vector.itemset(interest['id'] - 1, interest['amount'])
        if length := np.linalg.norm(vector):
            return vector / length
        return vector

    def create_access(self, number=NUM_USERS_ACCESS):
        model_path = os.path.join(settings.ML_DIR, f"user{self.id}.h5")
        model = create_model(model_path)
        results = match_user(model, self, Profile.objects.all(), users_to_match=number)
        matched_users = results.take(0, axis=1)
        for other in matched_users:
            access = Access.objects.create(me=self, other=other)
            access.save()

class PersonalityQuestionnaire(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
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
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
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
