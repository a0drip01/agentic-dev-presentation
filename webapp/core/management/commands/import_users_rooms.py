import csv
from django.core.management.base import BaseCommand
from core.models import User, Room
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import users and rooms from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        with open(options['csv_file'], newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                room, _ = Room.objects.get_or_create(name=row['room'])
                user, created = User.objects.get_or_create(
                    username=row['username'],
                    defaults={
                        'email': row.get('email', ''),
                        'role': row['role'],
                        'assigned_room': room,
                    }
                )
                if not created:
                    user.role = row['role']
                    user.assigned_room = room
                    user.save()
        self.stdout.write(self.style.SUCCESS('Import complete.'))
