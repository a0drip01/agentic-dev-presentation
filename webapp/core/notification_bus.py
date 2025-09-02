from django.utils import timezone
from .models import Notification, NotificationRead, Room, User

class NotificationBus:
    """
    Kafka-inspired notification bus for publishing notifications to room topics.
    Persists notifications and allows for multi-consumer read tracking.
    """
    @staticmethod
    def publish(room: Room, message: str) -> Notification:
        # Create and persist the notification
        notification = Notification.objects.create(room=room, message=message)
        # Optionally, notify all assigned doctors and nurses (observers)
        observers = room.users.filter(role__in=['doctor', 'nurse'])
        for user in observers:
            # NotificationRead is not created until user reads, but you could pre-create if needed
            pass
        # Log for now (simulate bus delivery)
        print(f"[BUS] {timezone.now()} - Notification {notification.id} published to room {room.name}: {message}")
        return notification

    @staticmethod
    def mark_as_read(notification: Notification, user: User):
        NotificationRead.objects.get_or_create(notification=notification, user=user)

    @staticmethod
    def get_unread_for_user(user: User):
        # Return all notifications for user's room(s) that user hasn't read
        rooms = Room.objects.filter(users=user)
        return Notification.objects.filter(room__in=rooms).exclude(reads__user=user)
