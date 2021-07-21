from django.core.management.base import CommandError

from backend.management.commands import GoogleCommand
from backend.models import Adjective, Interest, Question
from algo.parameters import Trait

class Command(GoogleCommand):

    help = "Gets content information from Google sheet and inserts in db"

    def add_arguments(self, parser):
        parser.add_argument('--model', help='model to update')
        parser.add_argument('--id', help='spreadsheet id')
        parser.add_argument('--sheet', help='spreadsheet name')

    def handle(self, *args, **kwargs):

        if kwargs['model'] == 'adjectives':

            Adjective.objects.all().delete()

            self.insert_data({'id': kwargs['id'], 'sheet': kwargs['sheet']}, Adjective,
            {
                'name': 0,
                'trait': lambda row: Trait[row[1]],
                'facet': 2,
                'pool': 3,
                'description': 4,
            }, 'name')

        elif kwargs['model'] == 'questions':

            for i in range(10):
                self.stdout.write(self.style.SUCCESS(f"Quesition #{i + 1}"))
                self.insert_data({'id': kwargs['id'], 'sheet': kwargs['sheet']}, Question,
                {
                    'interest': lambda row: Interest.objects.get_or_create(name=row[0])[0],
                    'text': i + 1,
                }, 'text')

        else:
            self.stdout.write(self.style.ERROR(f"Invalid model selected!!"))

    def insert_data(self, spreadsheet, model, indices, unique_field):

        data = self.get_data(spreadsheet['id'], spreadsheet['sheet'])

        for index, row in enumerate(data):
            if not index:
                continue

            obj_dict = {}
            for param in indices:
                index = indices[param]
                if isinstance(index, int):
                    value = row[index] if len(row) > index else ''
                else:
                    value = index(row)

                if value is not None and value != '':
                    obj_dict[param] = value

            unique_value = obj_dict.get(unique_field)

            if len(obj_dict) != len(indices):
                self.stdout.write(self.style.ERROR(f"Skipping: {unique_value}"))
                continue

            try:
                try:
                    obj = model.objects.get(**{unique_field: unique_value})
                    for field in obj_dict:
                        if field != unique_field:
                            setattr(obj, field, obj_dict[field])
                    self.stdout.write(self.style.SUCCESS(f"Updating: {unique_value}"))
                except model.DoesNotExist:
                    obj = model.objects.create(**obj_dict)
                    self.stdout.write(self.style.SUCCESS(f"Creating: {unique_value}"))

                obj.save()
            except:
                self.stdout.write(self.style.ERROR(f"Error in: {unique_value}"))
