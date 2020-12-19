import os
import numpy as np

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

from algo.parameters import *

FLOAT_PRECISION = 4


def avatar_base_path(instance, filename):
    return f'avatars/{instance.name.lower()}/{filename}'

def avatar_path(instance, filename):
    return f'avatars/{instance.base.name.lower()}/{instance.mood.name.lower()}/{filename}'

class AvatarBase(models.Model):
    name = models.CharField(max_length=20)
    image = models.ImageField(upload_to=avatar_base_path)

    @property
    def url(self):
        return f"http://{settings.HOST}{self.image.url}"

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
        return f"http://{settings.HOST}{self.image.url}"

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

    def personality_representation(self, personality, indices):
        elements = Personality.objects.order_by('trait')
        return {elements[int(index)].display_name: personality[int(index)] for index in indices}

    @property
    def facets(self):
        facets = [float(f"0.{self._personality[i * FLOAT_PRECISION : (i + 1) * FLOAT_PRECISION]}") for i in range(NUM_FACETS)]
        return np.array(facets, np.float)

    def get_personality(self):
        return personality_from_facets(self.facets)

    @property
    def personality(self):
        return self.personality_representation(self.get_personality(), range(NUM_TRAITS))

    @property
    def major_personality(self):
        personality = self.get_personality()
        indices = np.flip(abs(personality).argsort())[:NUM_DOMINANT_TRAITS]
        return self.personality_representation(personality, indices)

    def save_facets(self, facets):
        self._personality = ''.join((f"%0.{FLOAT_PRECISION}f" % facets[i])[2:] if facets[i] < 1 else "9" * FLOAT_PRECISION for i in range(NUM_FACETS))
        self.save()
        return self

    def get_all_interests(self, questions=True, blank=True):
        def get_answer(user_interest, question):
            try:
                return Answer.objects.get(user_interest=user_interest, question=question).text
            except Answer.DoesNotExist:
                return ''

        return [{
            **{
                "id": user_interest.interest.id,
                "name": user_interest.interest.name,
                "amount": user_interest.amount,
            },
            **({
                "questions": sorted(filter(lambda question: blank or question['answer'] != '', [
                    {"id": question.id, "question": question.text, "answer": get_answer(user_interest, question)} for question in Question.objects.filter(interest=user_interest.interest)
                ]), key=lambda question : len(question['answer']), reverse=True)
            } if questions else {})
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

    def get_info(self, interest_questions=True):
        return {
            "nick": self.user.username,
            "avatar": self.avatar.url,
            "personality": self.personality,
            "interests": self.get_all_interests(interest_questions),
            "mood": self.avatar.mood.name,
        }

    def get_basic_info(self):
        return {
            "nick": self.user.username,
            "avatar": self.avatar.url,
        }

    def get_partial_info(self):
        return {
            "avatar": self.avatar.url,
            "personality": self.major_personality,
            "mood": self.avatar.mood.name,
        }

    @property
    def interests(self):
        all_interests = self.get_all_interests(questions=False)
        vector = np.zeros(Interest.objects.last().pk, dtype=float)
        for interest in all_interests:
            vector.itemset(interest['id'] - 1, interest['amount'])
        if length := np.linalg.norm(vector):
            return vector / length
        return vector

    @property
    def traits(self):
        import random

        facets = self.facets
        traits = {}

        def find_index(element, array):
            for index, value in enumerate(array):
                if value > element:
                    return index
            return -1

        for i in range(NUM_TRAITS):
            trait = Personality.objects.get(trait=i)
            adjs = Adjective.objects.filter(trait=i)
            adjectives = list()
            pool = FACET_POOLS[Trait(i)]
            trait_value = 0
            for j in range(FACETS_PER_TRAIT):
                facet_value = facets[i * FACETS_PER_TRAIT + j]
                trait_value += facet_value
                index = find_index(facet_value, pool[j + 1])
                facet_adjs = adjs.filter(facet=j+1).filter(pool=index)
                try:
                    adjectives.extend(random.choices(facet_adjs))
                except:
                    pass
            traits[trait.display_name] = {
                "value": trait_value / FACETS_PER_TRAIT,
                "description": trait.description,
                "adjectives": [{"name": adjective.name, "description": adjective.description} for adjective in adjectives]
            }
        return traits

class Personality(models.Model):

    class Meta:
        verbose_name_plural = "personalities"

    TraitChoices = [
        (Trait.E.value, 'E'),
        (Trait.N.value, 'N'),
        (Trait.A.value, 'A'),
        (Trait.C.value, 'C'),
        (Trait.O.value, 'O'),
    ]

    trait = models.IntegerField(unique=True, choices=TraitChoices)
    display_name = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.display_name

class Adjective(models.Model):

    TraitChoices = [
        (Trait.E.value, 'E'),
        (Trait.N.value, 'N'),
        (Trait.A.value, 'A'),
        (Trait.C.value, 'C'),
        (Trait.O.value, 'O'),
    ]

    name = models.CharField(max_length=40)
    trait = models.IntegerField(choices=TraitChoices)
    facet = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    pool = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

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
