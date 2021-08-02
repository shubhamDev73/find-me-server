import os
import numpy as np

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator,  get_available_image_extensions, FileExtensionValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from algo.parameters import *

FLOAT_PRECISION = 4

def unique_name(name):
    full_name = os.path.join(settings.MEDIA_ROOT, name)
    if os.path.exists(full_name):
        os.remove(full_name)
    return name

def avatar_base_path(instance, filename):
    base_name = instance.name.lower()
    return unique_name(f'avatars/{base_name}/{base_name}.{filename.rsplit(".", 1)[1]}')

def avatar_path(instance, filename, variant='v1'):
    base_name = instance.base.name.lower()
    mood_name = instance.mood.name.lower()
    return unique_name(f'avatars/{base_name}/{mood_name}/{base_name}_{mood_name}_{variant}.{filename.rsplit(".", 1)[1]}')

def avatar_path_v1(instance, filename):
    return avatar_path(instance, filename, 'v1')

def avatar_path_v2(instance, filename):
    return avatar_path(instance, filename, 'v2')

def mood_weather_path(instance, filename):
    name = instance.name.lower()
    return unique_name(f'moods/{name}_weather.{filename.rsplit(".", 1)[1]}')

def mood_icon_path(instance, filename):
    name = instance.name.lower()
    return unique_name(f'moods/{name}_icon.{filename.rsplit(".", 1)[1]}')

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
    weather = models.ImageField(upload_to=mood_weather_path)
    icon = models.FileField(upload_to=mood_icon_path, validators=[FileExtensionValidator(allowed_extensions=get_available_image_extensions() + ["svg"])])

    def get_url(self, type='weather'):
        try:
            url = f"http://{settings.HOST}{getattr(self, type).url}"
        except:
            url = ""
        return url

    @property
    def url(self):
        return {type: self.get_url(type) for type in ["weather", "icon"]}

    def __str__(self):
        return self.name

class Avatar(models.Model):
    base = models.ForeignKey(AvatarBase, on_delete=models.CASCADE)
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)
    v1 = models.ImageField(upload_to=avatar_path_v1)
    v2 = models.ImageField(upload_to=avatar_path_v2)

    def get_url(self, variant='v1'):
        try:
            url = f"http://{settings.HOST}{getattr(self, variant).url}"
        except:
            url = ""
        return url

    @property
    def url(self):
        return {variant: self.get_url(variant) for variant in ["v1", "v2"]}

    def __str__(self):
        return f"{str(self.base)} ({str(self.mood)})"

class User(AbstractUser):
    token = models.CharField(max_length=64, blank=True)
    expired = models.BooleanField(default=False)
    external_ids = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    otp = models.CharField(max_length=100, blank=True)
    verified = models.BooleanField(default=False)
    fcm_token = models.CharField(max_length=200, blank=True)
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="backend_user_set",
        related_query_name="backend_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="backend_user_set",
        related_query_name="backend_user",
    )

    def new_token(self):
        import secrets

        while True:
            try:
                token = secrets.token_hex(32)
                User.objects.get(token=token)
            except User.DoesNotExist:
                break

        self.token = token
        self.expired = False
        self.save()
        return self

    def fill_details(self, username=None, email=None, phone=None):
        if username is not None:
            self.username = username
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        self.save()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ForeignKey(Avatar, default=1, on_delete=models.PROTECT)
    _personality = models.CharField(max_length=NUM_FACETS * FLOAT_PRECISION, default='0' * NUM_FACETS * FLOAT_PRECISION)
    last_questionnaire_time = models.DateTimeField(null=True)

    def __str__(self):
        return str(self.user)

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
        self.last_questionnaire_time = timezone.now()
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
                "timestamp": user_interest.last_change,
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

    def get_info(self, interest_questions=True, empty_questions=False):
        return {
            "nick": self.user.username,
            "base_avatar": self.avatar.base.name,
            "avatar": self.avatar.url,
            "personality": self.traits,
            "interests": self.get_all_interests(questions=interest_questions, blank=empty_questions),
            "mood": self.avatar.mood.name,
            "avatar_timeline": self.avatar_timeline
        }

    def get_basic_info(self):
        return {
            "nick": self.user.username,
            "avatar": self.avatar.url,
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
            return len(array)

        for i in range(NUM_TRAITS):
            personality = self.personality
            trait = Personality.objects.get(trait=i)
            adjs = Adjective.objects.filter(trait=i)
            adjectives = list()
            pool = FACET_POOLS[Trait(i)]
            trait_value = 0
            for j in range(FACETS_PER_TRAIT):
                facet_value = facets[i * FACETS_PER_TRAIT + j]
                trait_value += facet_value
                index = find_index(facet_value, pool[j + 1])
                facet_adjs = adjs.filter(facet=j+1).filter(pool=index+1)
                adjectives.append(facet_adjs)
            traits[trait.display_name] = {
                "value": personality[trait.display_name],
                "description": trait.description,
                "url": trait.get_urls(),
                "adjectives": [[{"name": adjective.name, "description": adjective.description} for adjective in trait_adjs] for trait_adjs in adjectives]
            }
        return traits

    @property
    def avatar_timeline(self):
        timelines = AvatarTimeline.objects.filter(user=self).order_by('timestamp')
        return [{"timestamp": timeline.timestamp, "mood": timeline.avatar.mood.name, "base_avatar": timeline.avatar.base.name} for timeline in timelines]

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
    url = models.TextField(blank=True)

    def __str__(self):
        return self.display_name

    def get_urls(self):
        return self.url.replace(' ', '').split(',')

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
    url = models.CharField(max_length=40)
    initial = models.BooleanField(default=False)

    def __str__(self):
        return str(self.url)

class Interest(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class UserInterest(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    last_change = models.DateTimeField(auto_now=True)

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

class AvatarTimeline(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    avatar = models.ForeignKey(Avatar, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{str(self.user)} - {str(self.avatar)} : {self.timestamp}"

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
    chat_id = models.CharField(max_length=30)
    last_read_time1 = models.DateTimeField(auto_now_add=True)
    last_read_time2 = models.DateTimeField(auto_now_add=True)
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
