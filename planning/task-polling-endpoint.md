# Task: Implement Notification Polling Endpoint

## Goals
- REST API for consumers to poll for unacknowledged notifications.

## API Specification

### Endpoint: GET /api/consumers/{consumer_id}/notifications/
Query parameters:
- `since`: ISO timestamp (optional) - only return notifications after this time
- `limit`: integer (optional) - max number of notifications to return (default 50)

### Response: 200 OK
```json
{
  "notifications": [
    {
      "id": "notification-uuid",
      "room": "room1",
      "message": "Timer expired...",
      "timestamp": "2025-09-16T10:25:00Z",
      "tags": {
        "room": "room1",
        "provider": "dr_smith"
      }
    }
  ],
  "has_more": false,
  "next_since": "2025-09-16T10:25:00Z"
}
```

## Logic Flow
1. Validate consumer exists and is active
2. Get consumer's subscription tags
3. Query notifications that match ANY of the consumer's tags
4. Exclude notifications already acknowledged by this consumer
5. Apply time filter (since parameter)
6. Order by timestamp DESC, apply limit
7. Return formatted response

## Notification Matching Logic
- For each notification, extract relevant tags (room name, assigned providers, etc.)
- Match against consumer's subscriptions using tag_type + tag_value
- A notification matches if ANY of its tags match ANY of the consumer's subscriptions

## Steps
1. Create API view in `core/views_notifications.py`
2. Implement tag extraction from notifications
3. Implement subscription matching logic
4. Add pagination support
5. Add URL routing

## Performance Considerations
- Index on notification timestamp
- Index on consumer subscriptions
- Consider caching frequent tag queries

## Deliverables
- API endpoint code
- Tag matching logic
- URL routing
- Performance optimizations
- API documentation
