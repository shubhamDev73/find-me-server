import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from algo.match import create_model, train_model, match_user

from backend.models import Profile, Access

NUM_USERS_ACCESS = 5


class Command(BaseCommand):

    help = "Creates and updates Access entries for users whose Access have expired"

    def add_arguments(self, parser):
        parser.add_argument('--id', help='id of the profile to create model for', type=int)
        parser.add_argument('--train', help='train the model', action='store_true')
        parser.add_argument('--users', help='number of users to retrieve', type=int)

    def handle(self, *args, **kwargs):
        try:
            profile = Profile.objects.get(pk=kwargs['id'])
        except Profile.DoesNotExist:
            raise CommandError(f"Profile with id {kwargs['id']} does not exist. Are you sure it's profile id and not user id?")

        model_path = os.path.join(settings.ML_DIR, f"user{profile.id}.h5")

        if kwargs['train']:
            model = create_model()
            train_model(model, filepath=model_path)
            users_to_match = NUM_USERS_ACCESS
        else:
            try:
                model = create_model(model_path)
            except OSError:
                raise CommandError(f"Model for id {kwargs['id']} does not exist. You have to train first!!")

            try:
                users_to_match = kwargs['users']
            except KeyError:
                self.stdout.write(self.style.WARNING(f"Number of users not provided. Defaulting to {NUM_USERS_ACCESS}"))
                users_to_match = NUM_USERS_ACCESS

        results = match_user(model, profile, Profile.objects.all(), users_to_match=users_to_match)
        matched_users = results.take(0, axis=1)
        for other in matched_users:
            access = Access.objects.create(me=profile, other=other)
            access.save()
