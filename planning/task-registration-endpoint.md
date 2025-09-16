# Task: Implement Consumer Registration Endpoint

## Goals
- REST API for consumers to register and subscribe with tags.

## API Specification

### Endpoint: POST /api/consumers/register/
```json
{
  "name": "iPhone App - User123",
  "consumer_type": "mobile",
  "subscriptions": [
    {"tag_type": "room", "tag_value": "room1"},
    {"tag_type": "room", "tag_value": "room2"},
    {"tag_type": "provider", "tag_value": "dr_smith"}
  ]
}
```

### Response: 201 Created
```json
{
  "consumer_id": "uuid-here",
  "name": "iPhone App - User123",
  "subscriptions": [
    {"tag_type": "room", "tag_value": "room1"},
    {"tag_type": "room", "tag_value": "room2"},
    {"tag_type": "provider", "tag_value": "dr_smith"}
  ],
  "created_at": "2025-09-16T10:30:00Z"
}
```

### Endpoint: PUT /api/consumers/{consumer_id}/subscriptions/
Update existing consumer subscriptions (replaces all)

### Endpoint: DELETE /api/consumers/{consumer_id}/
Unregister consumer

## Steps
1. Create API view in `core/views_notifications.py`
2. Validate incoming data (consumer name, tag format)
3. Create Consumer and ConsumerSubscription records
4. Add URL patterns to core/urls.py
5. Add error handling for duplicate registrations

## Error Scenarios
- Invalid tag format
- Consumer already exists (if using client-provided ID)
- Missing required fields

## Deliverables
- API endpoint code
- URL routing
- Input validation
- Error handling
- API documentation
