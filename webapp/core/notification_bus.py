from django.utils import timezone
from .models import Notification, NotificationRead, Room, User, WebhookSubscription
from collections import defaultdict
import requests

class NotificationBus:
    """
    Kafka-inspired notification bus for publishing notifications to room topics.
    Persists notifications and allows for multi-consumer read tracking.
    Now supports dynamic observer (consumer) registration per room/topic.
    """
    # In-memory registry: {room_id: [observer_fn, ...]}
    _observers = defaultdict(list)

    @classmethod
    def register_observer(cls, room: Room, observer_fn):
        """Register a callback to be notified when a notification is published to a room."""
        cls._observers[room.id].append(observer_fn)

    @classmethod
    def publish(cls, room: Room, message: str) -> Notification:
        # Create and persist the notification
        notification = Notification.objects.create(room=room, message=message)
        # Notify all registered observers for this room
        for observer_fn in cls._observers.get(room.id, []):
            try:
                observer_fn(notification)
            except Exception as e:
                print(f"[BUS] Observer error: {e}")
        # Notify all registered webhooks for this room
        for webhook in room.webhook_subscriptions.all():
            try:
                requests.post(webhook.url, json={
                    'notification_id': str(notification.id),
                    'room': room.name,
                    'message': message,
                    'timestamp': notification.timestamp.isoformat(),
                }, timeout=5)
                print(f"[BUS] Webhook POST to {webhook.url} succeeded.")
            except Exception as e:
                print(f"[BUS] Webhook POST to {webhook.url} failed: {e}")
        print(f"[BUS] {timezone.now()} - Notification {notification.id} published to room {room.name}: {message}")
        return notification

    @staticmethod
    def mark_as_read(notification: Notification, user: User):
        NotificationRead.objects.get_or_create(notification=notification, user=user)

    @staticmethod
    def get_unread_for_user(user: User):
        rooms = Room.objects.filter(users=user)
        return Notification.objects.filter(room__in=rooms).exclude(reads__user=user)

class WebhookSubscription(models.Model):
    url = models.URLField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='webhook_subscriptions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Webhook {self.url} for Room {self.room.name}"
