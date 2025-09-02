import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Room

class Command(BaseCommand):
    help = 'Continuously check rooms and log notifications for expired timers.'

    def handle(self, *args, **options):
        notified = {}  # room_id -> last_notification_time (in 30s intervals)
        print('Starting notification loop. Press Ctrl+C to stop.')
        try:
            while True:
                now = timezone.now()
                for room in Room.objects.all():
                    if room.timer_started_at and room.timer_seconds > 0:
                        elapsed = (now - room.timer_started_at).total_seconds()
                        if elapsed >= room.timer_seconds:
                            intervals = int((elapsed - room.timer_seconds) // 30)
                            last = notified.get(room.id, -1)
                            # Notify immediately when timer expires
                            if last == -1:
                                doctors = room.users.filter(role='doctor')
                                nurses = room.users.filter(role='nurse')
                                doctor_names = ', '.join([d.username for d in doctors]) or 'none'
                                nurse_names = ', '.join([n.username for n in nurses]) or 'none'
                                print(f"[NOTIFY] {timezone.now()} - room {room.name} timer EXPIRED, notify doctor(s) {doctor_names} and nurse(s) {nurse_names}")
                                notified[room.id] = 0
                            # Notify every 30 seconds after expiration
                            elif intervals > last:
                                doctors = room.users.filter(role='doctor')
                                nurses = room.users.filter(role='nurse')
                                doctor_names = ', '.join([d.username for d in doctors]) or 'none'
                                nurse_names = ', '.join([n.username for n in nurses]) or 'none'
                                print(f"[NOTIFY] {timezone.now()} - room {room.name} timer expired, notify doctor(s) {doctor_names} and nurse(s) {nurse_names}")
                                notified[room.id] = intervals
                        else:
                            notified[room.id] = -1  # Reset notification if timer is reset
                time.sleep(1)
        except KeyboardInterrupt:
            print('Notification loop stopped.')
