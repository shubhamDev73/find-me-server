import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.management import call_command

from backend.models import Access

TIME_TO_REFRESH = datetime.timedelta(days=1, hours=0, minutes=0, seconds=0)


class Command(BaseCommand):

    help = "Creates and updates Access entries for users whose Access have expired"

    def handle(self, *args, **kwargs):
        expire_time = timezone.localtime() - TIME_TO_REFRESH
        objects = Access.objects.filter(active=True).filter(create_time__lt=expire_time)
        users = [access.me for access in objects]

        if users:
            count_users = {user: users.count(user) for user in users}
            for me in count_users:
                self.stdout.write(f"Creating {count_users[me]} new entries for user: {me.id} - {me}")
                call_command("ml", id=me.id, train=False, users=count_users[me])
            self.stdout.write(f"Expiring {len(objects)} old entries")
            objects.update(active=False)
        else:
            self.stdout.write("Nothing to do")
