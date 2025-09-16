# Task: Implement Notification Acknowledgement Endpoint

## Goals
- REST API for consumers to acknowledge notifications (batch/list of IDs).

## API Specification

### Endpoint: POST /api/consumers/{consumer_id}/notifications/ack/
```json
{
  "notification_ids": [
    "uuid-1",
    "uuid-2", 
    "uuid-3"
  ]
}
```

### Response: 200 OK
```json
{
  "acknowledged": [
    {
      "notification_id": "uuid-1",
      "acked_at": "2025-09-16T10:30:00Z",
      "status": "success"
    },
    {
      "notification_id": "uuid-2", 
      "acked_at": "2025-09-16T10:30:00Z",
      "status": "success"
    }
  ],
  "errors": [
    {
      "notification_id": "uuid-3",
      "error": "Notification not found or already acknowledged"
    }
  ]
}
```

## Logic Flow
1. Validate consumer exists and is active
2. For each notification ID:
   - Verify notification exists
   - Check if consumer is subscribed to relevant tags for this notification
   - Check if already acknowledged by this consumer
   - Create ConsumerNotificationAck record
3. Return success/error status for each notification

## Idempotency
- Multiple ACKs of the same notification by same consumer should be idempotent
- Use get_or_create for ConsumerNotificationAck records
- Return success even if already acknowledged

## Steps
1. Create API view in `core/views_notifications.py`
2. Add batch processing logic for notification IDs
3. Add validation for consumer permissions per notification
4. Handle partial success scenarios
5. Add URL routing

## Error Scenarios
- Consumer not found/inactive
- Notification doesn't exist
- Consumer not subscribed to notification's tags
- Already acknowledged (should be success, not error)

## Deliverables
- API endpoint code
- Batch processing logic
- Permission validation
- URL routing
- Error handling
- API documentation
