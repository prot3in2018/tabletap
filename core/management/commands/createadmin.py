from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Force create superuser'

    def handle(self, *args, **kwargs):
        username = 's4661478'
        email = 'takuto.kato@student.uq.edu.au'
        password = 'infs3202'

        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.email = email
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated superuser: {username}'))
        except User.DoesNotExist:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Created new superuser: {username}'))
