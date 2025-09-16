from django.utils import timezone
from .models import Notification, NotificationRead, Room, User, Consumer, ConsumerSubscription, ConsumerNotificationPending
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

    @staticmethod
    def extract_tags_from_notification(notification: Notification) -> dict:
        """Extract relevant tags from a notification for consumer matching"""
        room = notification.room
        tags = {
            'room': room.name,
        }
        
        # Add provider tags from assigned users (doctors)
        doctors = room.users.filter(role='doctor').order_by('username')
        if doctors.exists():
            # For now, just take the first doctor alphabetically as the primary provider
            tags['provider'] = doctors.first().username
        
        # Add department/other tags as needed
        # Can be extended later for more complex tag extraction
        return tags

    @classmethod
    def find_matching_consumers(cls, tags: dict) -> list:
        """Find all active consumers that should receive this notification based on their subscriptions"""
        matching_consumers = []
        
        # Get all active consumers with subscriptions
        active_consumers = Consumer.objects.filter(status='active').prefetch_related('subscriptions')
        
        for consumer in active_consumers:
            consumer_match = False
            matched_tags = {}
            
            for subscription in consumer.subscriptions.all():
                # Check if this subscription matches any of the notification tags
                if subscription.tag_type == 'all':
                    # Special case: subscribe to all notifications
                    consumer_match = True
                    matched_tags['all'] = 'all'
                elif subscription.tag_type in tags:
                    if subscription.tag_value == tags[subscription.tag_type]:
                        consumer_match = True
                        matched_tags[subscription.tag_type] = subscription.tag_value
            
            if consumer_match:
                matching_consumers.append((consumer, matched_tags))
        
        return matching_consumers

    @classmethod
    def publish(cls, room: Room, message: str) -> Notification:
        # Create and persist the notification
        notification = Notification.objects.create(room=room, message=message)
        
        # Extract tags for consumer matching
        tags = cls.extract_tags_from_notification(notification)
        
        # Find matching consumers and create pending notifications
        matching_consumers = cls.find_matching_consumers(tags)
        
        # Create pending notification records for matched consumers
        pending_records = []
        for consumer, matched_tags in matching_consumers:
            pending_record = ConsumerNotificationPending(
                consumer=consumer,
                notification=notification,
                matched_tags=matched_tags
            )
            pending_records.append(pending_record)
        
        # Bulk create pending records for efficiency
        if pending_records:
            ConsumerNotificationPending.objects.bulk_create(pending_records, ignore_conflicts=True)
            print(f"[BUS] Created {len(pending_records)} pending notification records for consumers")
        
        # Notify all registered observers for this room (existing functionality)
        for observer_fn in cls._observers.get(room.id, []):
            try:
                observer_fn(notification)
            except Exception as e:
                print(f"[BUS] Observer error: {e}")
        
        # Notify all registered webhooks for this room (existing functionality)
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
