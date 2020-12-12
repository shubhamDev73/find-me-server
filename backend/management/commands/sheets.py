from django.core.management.base import CommandError
from django.conf import settings

from backend.management.commands import GoogleCommand
from backend.models import Adjective
from algo.parameters import Trait

SPREADSHEET_ID = '1JwOD04q5fXNfYs6xtodxPS794Nqmk9uAuHSm5OxejLg'
SPREADSHEET_NAME = 'Adjectives'


class Command(GoogleCommand):

    help = "Gets content information from Google sheet and inserts in db"

    def handle(self, *args, **kwargs):

        self.insert_data({
            'name': 0,
            'trait': lambda row: Trait[row[1]],
            'facet': 2,
            'pool': 3,
            'description': 4,
        }, 'name')

    def insert_data(self, indices, unique_field):

        data = self.get_data(SPREADSHEET_ID, SPREADSHEET_NAME)

        for index, row in enumerate(data):
            if not index:
                continue

            obj_dict = {}
            for param in indices:
                index = indices[param]
                if isinstance(index, int):
                    obj_dict[param] = row[index] if len(row) > index else ''
                else:
                    obj_dict[param] = index(row)

            unique_value = obj_dict.get(unique_field)

            try:
                try:
                    obj = Adjective.objects.get(**{unique_field: unique_value})
                    for field in obj_dict:
                        setattr(obj, field, obj_dict[field])
                    self.stdout.write(self.style.SUCCESS(f"Updating: {unique_value}"))
                except Adjective.DoesNotExist:
                    obj = Adjective.objects.create(**obj_dict)
                    self.stdout.write(self.style.SUCCESS(f"Creating: {unique_value}"))

                obj.save()
            except:
                self.stdout.write(self.style.ERROR(f"Error in: {unique_value}"))
