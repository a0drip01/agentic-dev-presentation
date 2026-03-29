from django.utils import timezone
from .models import Notification, NotificationRead, Room, User, Consumer, ConsumerSubscription, ConsumerNotificationPending, ObserverSubscription
from collections import defaultdict
import requests
import json

class NotificationBus:
    """
    Kafka-inspired notification bus for publishing notifications to room topics.
    Persists notifications and allows for multi-consumer read tracking.
    Now supports database-persisted observer (observer pattern) registration per room/topic.
    """

    @classmethod
    def register_observer(cls, room: Room, observer_data: dict) -> ObserverSubscription:
        """
        Register a database-persisted observer to be notified when notifications are published to a room.
        
        Args:
            room: The room to observe
            observer_data: Dictionary containing observer configuration:
                - name: Human-readable name
                - observer_type: Type of observer (mobile_app, webhook, etc.)
                - callback_url: URL to POST notifications to
                - callback_method: HTTP method (default: POST)
                - callback_headers: Additional headers (optional)
                - timeout_seconds: Request timeout (default: 10)
                - retry_count: Number of retries (default: 3)
                - metadata: Additional observer metadata (optional)
        
        Returns:
            ObserverSubscription: The created observer subscription
        """
        observer = ObserverSubscription.objects.create(
            room=room,
            name=observer_data.get('name', 'Unnamed Observer'),
            observer_type=observer_data.get('observer_type', 'mobile_app'),
            callback_url=observer_data['callback_url'],
            callback_method=observer_data.get('callback_method', 'POST'),
            callback_headers=observer_data.get('callback_headers', {}),
            timeout_seconds=observer_data.get('timeout_seconds', 10),
            retry_count=observer_data.get('retry_count', 3),
            metadata=observer_data.get('metadata', {})
        )
        print(f"[BUS] Registered observer {observer.name} for room {room.name}")
        return observer

    @classmethod
    def unregister_observer(cls, observer_id: str) -> bool:
        """
        Unregister an observer by ID.
        
        Args:
            observer_id: UUID of the observer to remove
            
        Returns:
            bool: True if observer was found and removed, False otherwise
        """
        try:
            observer = ObserverSubscription.objects.get(id=observer_id)
            observer_name = observer.name
            room_name = observer.room.name
            observer.delete()
            print(f"[BUS] Unregistered observer {observer_name} from room {room_name}")
            return True
        except ObserverSubscription.DoesNotExist:
            print(f"[BUS] Observer {observer_id} not found for unregistration")
            return False

    @classmethod
    def get_active_observers(cls, room: Room):
        """Get all active observers for a room."""
        return ObserverSubscription.objects.filter(room=room, status='active')

    @classmethod
    def notify_observers(cls, room: Room, notification: Notification):
        """
        Notify all active observers for a room about a new notification.
        Uses database-persisted observer subscriptions with proper error handling.
        """
        active_observers = cls.get_active_observers(room)
        
        if not active_observers.exists():
            print(f"[BUS] No active observers for room {room.name}")
            return

        successful_notifications = 0
        failed_notifications = 0

        for observer in active_observers:
            success = cls._notify_single_observer(observer, notification)
            if success:
                successful_notifications += 1
            else:
                failed_notifications += 1

        print(f"[BUS] Notified {successful_notifications} observers successfully, {failed_notifications} failed for room {room.name}")

    @classmethod
    def _notify_single_observer(cls, observer: ObserverSubscription, notification: Notification) -> bool:
        """
        Notify a single observer with retry logic and error handling.
        
        Returns:
            bool: True if notification was successful, False otherwise
        """
        if not observer.is_active():
            return False

        # Prepare notification payload
        payload = {
            'observer_id': str(observer.id),
            'notification_id': str(notification.id),
            'room': notification.room.name,
            'message': notification.message,
            'timestamp': notification.timestamp.isoformat(),
            'room_id': notification.room.id,
        }

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Hospital-NotificationBus/1.0',
            **observer.callback_headers
        }

        # Attempt notification with retries
        for attempt in range(observer.retry_count + 1):
            try:
                response = requests.request(
                    method=observer.callback_method,
                    url=observer.callback_url,
                    json=payload,
                    headers=headers,
                    timeout=observer.timeout_seconds
                )
                
                if 200 <= response.status_code < 300:
                    observer.mark_success()
                    observer.update_last_notified()
                    print(f"[BUS] Successfully notified observer {observer.name} (attempt {attempt + 1})")
                    return True
                else:
                    print(f"[BUS] Observer {observer.name} returned status {response.status_code} (attempt {attempt + 1})")
                    
            except requests.exceptions.RequestException as e:
                print(f"[BUS] Failed to notify observer {observer.name} (attempt {attempt + 1}): {e}")
                
            # Don't sleep on the last attempt
            if attempt < observer.retry_count:
                import time
                time.sleep(1)  # Wait 1 second before retry

        # All attempts failed
        observer.mark_failure()
        observer.update_last_notified()
        print(f"[BUS] All attempts failed for observer {observer.name}, failure count: {observer.failure_count}")
        return False

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
        
        # Notify all database-persisted observers for this room (NEW observer pattern)
        cls.notify_observers(room, notification)
        
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
