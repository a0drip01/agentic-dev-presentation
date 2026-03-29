# Task: Integrate with Notification Bus Logic

## Goals
- Enhance notification bus to support tag-based routing and consumer tracking.

## Changes to NotificationBus

### 1. Add Tag Extraction
```python
@staticmethod
def extract_tags_from_notification(notification: Notification) -> dict:
    """Extract relevant tags from a notification for consumer matching"""
    room = notification.room
    tags = {
        'room': room.name,
    }
    
    # Add provider tags from assigned users
    doctors = room.users.filter(role='doctor')
    for doctor in doctors:
        tags[f'provider'] = doctor.username
    
    # Add department/other tags as needed
    return tags
```

### 2. Consumer Notification Registry
- Track which consumers should receive each notification
- Create ConsumerNotificationPending records for undelivered notifications
- Clean up delivered/acked notifications periodically

### 3. Integration Points
- Extend `publish()` method to create consumer notification records
- Add helper methods for consumer subscription matching
- Maintain backward compatibility with existing webhook system

## New Model: ConsumerNotificationPending
```python
class ConsumerNotificationPending(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    matched_tags = models.JSONField()  # Which tags caused the match
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('consumer', 'notification')
```

## Steps
1. Add tag extraction logic to notification creation
2. Implement consumer matching when notifications are published  
3. Create pending notification records for matched consumers
4. Update polling endpoint to use pending notifications
5. Clean up pending notifications after acknowledgment
6. Add management command for cleanup of old ack records

## Performance Considerations
- Batch consumer matching operations
- Index on pending notification queries
- Consider async notification delivery for high volume

## Backward Compatibility
- Keep existing webhook system functional
- Maintain current observer pattern for in-process consumers
- Don't break existing notification queries for users

## Deliverables
- Updated notification bus logic
- New pending notification model
- Consumer matching algorithms
- Cleanup management commands
- Performance optimizations
- Documentation of changes
