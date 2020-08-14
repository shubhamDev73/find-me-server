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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        profile.new_token()

class Interest(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user) + " - " + str(self.interest) + ": " + str(self.amount)

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
        return str(self.user_interest) + " - " + str(self.question) + ": " + self.text

class Connect(models.Model):
    user1 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='first_user')
    user2 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='second_user')

    retained1 = models.BooleanField(default=False)
    retained2 = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user1.user) + " - " + str(self.user2.user)
