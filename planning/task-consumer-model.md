# Task: Design Consumer Subscription Model

## Goals
- Create Django models to track consumers, their subscription tags, and notification acknowledgments.

## Models Needed

### 1. Consumer Model
```python
class Consumer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)  # Human-readable name
    consumer_type = models.CharField(max_length=50, default='mobile')  # mobile, script, service
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
```

### 2. ConsumerSubscription Model
```python
class ConsumerSubscription(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='subscriptions')
    tag_type = models.CharField(max_length=50)  # 'room', 'provider', 'department'
    tag_value = models.CharField(max_length=100)  # 'room1', 'dr_smith', 'icu'
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('consumer', 'tag_type', 'tag_value')
```

### 3. ConsumerNotificationAck Model
```python
class ConsumerNotificationAck(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='acknowledgments')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='consumer_acks')
    acked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('consumer', 'notification')
```

## Steps
1. Add models to `core/models.py`
2. Create and run migrations
3. Update admin.py to include new models
4. Add helper methods for tag matching logic

## Deliverables
- Model code in `core/models.py`
- Migration files
- Admin interface updates
- Documentation of tag system design
