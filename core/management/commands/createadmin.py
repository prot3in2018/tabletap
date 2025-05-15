from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates the default admin user'

    def handle(self, *args, **kwargs):
        username = 's4661478'
        email = 'takuto.kato@student.uq.edu.au'
        password = 'infs3202'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists'))
