from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Room
import time

class Command(BaseCommand):
    help = 'Check all rooms and log a notification if the timer has expired. Notifies every 30 seconds after expiration.'

    def handle(self, *args, **options):
        now = timezone.now()
        for room in Room.objects.all():
            if room.timer_started_at and room.timer_seconds > 0:
                elapsed = (now - room.timer_started_at).total_seconds()
                if elapsed >= room.timer_seconds:
                    doctors = room.users.filter(role='doctor')
                    nurses = room.users.filter(role='nurse')
                    doctor_names = ', '.join([d.username for d in doctors]) or 'none'
                    nurse_names = ', '.join([n.username for n in nurses]) or 'none'
                    # Notify every 30 seconds after expiration
                    if int(elapsed - room.timer_seconds) % 30 == 0:
                        self.stdout.write(f"[NOTIFY] room {room.name} timer expired, notify doctor(s) {doctor_names} and nurse(s) {nurse_names}")
                else:
                    self.stdout.write(f"room {room.name} timer running: {int(elapsed)}/{room.timer_seconds} seconds elapsed")
            else:
                self.stdout.write(f"room {room.name} has no active timer.")
