from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('patient', 'Patient'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    assigned_room = models.ForeignKey('Room', null=True, blank=True, on_delete=models.SET_NULL, related_name='users')

class Room(models.Model):
    name = models.CharField(max_length=50)
    timer_seconds = models.PositiveIntegerField(default=0)
    timer_started_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    def start_timer(self, seconds):
        self.timer_seconds = seconds
        self.timer_started_at = timezone.now()
        self.save()

    def stop_timer(self):
        self.timer_seconds = 0
        self.timer_started_at = None
        self.save()

    def timer_expired(self):
        if self.timer_started_at and self.timer_seconds > 0:
            elapsed = (timezone.now() - self.timer_started_at).total_seconds()
            return elapsed >= self.timer_seconds
        return False

    def notify_observers(self, event_type='expired', reason=None):
        from .notification_bus import NotificationBus
        doctors = self.users.filter(role='doctor')
        nurses = self.users.filter(role='nurse')
        patients = self.users.filter(role='patient')
        doctor_names = ', '.join([d.username for d in doctors]) or 'none'
        nurse_names = ', '.join([n.username for n in nurses]) or 'none'
        patient_names = ', '.join([p.username for p in patients]) or 'none'
        if not reason:
            if event_type == 'expired':
                reason = 'Timer expired'
            else:
                reason = 'Timer interval notification'
        message = (
            f"Room: {self.name}\n"
            f"Doctor(s): {doctor_names}\n"
            f"Nurse(s): {nurse_names}\n"
            f"Patient(s): {patient_names}\n"
            f"Reason: {reason}"
        )
        notification = NotificationBus.publish(self, message)
        return notification

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification {self.id} for Room {self.room.name} at {self.timestamp}"

class NotificationRead(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_reads')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('notification', 'user')

    def __str__(self):
        return f"{self.user.username} read {self.notification.id} at {self.read_at}"

class WebhookSubscription(models.Model):
    url = models.URLField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='webhook_subscriptions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Webhook {self.url} for Room {self.room.name}"


class Consumer(models.Model):
    """
    Generic consumer that can subscribe to notifications.
    Used by mobile apps, external services, scripts, etc.
    """
    CONSUMER_TYPES = [
        ('mobile', 'Mobile App'),
        ('script', 'Script/CLI'),
        ('service', 'External Service'),
        ('webhook', 'Webhook Consumer'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Human-readable name for this consumer")
    consumer_type = models.CharField(max_length=20, choices=CONSUMER_TYPES, default='mobile')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    registered_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional consumer metadata (device info, etc.)")
    
    class Meta:
        ordering = ['-registered_at']
    
    def __str__(self):
        return f"{self.name} ({self.consumer_type})"
    
    def is_active(self):
        return self.status == 'active'


class ConsumerSubscription(models.Model):
    """
    Tag-based subscription system for consumers.
    Allows filtering notifications by tag_type and tag_value.
    """
    TAG_TYPES = [
        ('room', 'Room-based notifications'),
        ('provider', 'Provider-based notifications'),
        ('department', 'Department-based notifications'),
        ('user_role', 'User role-based notifications'),
        ('all', 'All notifications'),
    ]
    
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='subscriptions')
    tag_type = models.CharField(max_length=20, choices=TAG_TYPES)
    tag_value = models.CharField(max_length=100, help_text="Value to match (room name, provider ID, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('consumer', 'tag_type', 'tag_value')
        ordering = ['tag_type', 'tag_value']
    
    def __str__(self):
        return f"{self.consumer.name}: {self.tag_type}={self.tag_value}"


class ConsumerNotificationAck(models.Model):
    """
    Tracks which notifications have been acknowledged by which consumers.
    Part of the Kafka-like acknowledgment system.
    """
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='acknowledgments')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='consumer_acknowledgments')
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('consumer', 'notification')
        ordering = ['-acknowledged_at']
    
    def __str__(self):
        return f"{self.consumer.name} acked {self.notification.id}"


class ConsumerNotificationPending(models.Model):
    """
    Tracks notifications that are pending for specific consumers.
    Created when a notification is published and matches a consumer's subscriptions.
    Deleted when the notification is acknowledged.
    """
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='pending_notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='pending_for_consumers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('consumer', 'notification')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pending: {self.consumer.name} <- {self.notification.id}"
