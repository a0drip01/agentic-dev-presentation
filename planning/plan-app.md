# Planning: iPhone App Support for Notification Bus

## Objective
Implement server-side support for an iPhone app to consume notifications via the existing notification bus. Ensure all registered consumers (e.g., scripts, mobile apps) are tracked, and notification acknowledgements are managed per consumer.

---

## Key Considerations

- **Notification Bus Backbone:**  
  Use `core/notification_bus.py` as the central system for notification delivery and tracking, following the observer pattern for consumer subscription.

- **Consumer Registration:**  
  Consumers register by subscribing to the notification bus, specifying notification tags (e.g., provider, room number) relevant to their interests.

- **Acknowledgement Tracking:**  
  Consumers notify the server (via a callback/REST endpoint) when they have received specific notifications. The server tracks which notification IDs have been seen by each consumer.

- **Missed Notifications:**  
  The server maintains a record of which notifications have been acknowledged by each consumer. On polling, the server returns any unseen notifications for that consumer.

---

## Implementation Steps

### 1. Consumer Registration

- Consumers subscribe to the notification bus using tags (provider, room number, etc.).
- Registration is handled via the observer pattern in `notification_bus.py`.
- Store consumer info and subscription tags in the database.

### 2. Notification Delivery

- Implement a REST API endpoint for consumers (including the iPhone app) to poll for notifications.
- Endpoint returns notifications matching the consumer's subscription tags that have not yet been acknowledged.

### 3. Acknowledgement Mechanism

- Implement a REST API endpoint for consumers to acknowledge receipt of notifications.
- Store notification ID, consumer ID, and timestamp for each acknowledgement.
- On each poll, compare notification IDs to determine which notifications are new for the consumer.

### 4. Tracking Missed Notifications

- On each poll, return all notifications matching the consumer's tags that have not been acknowledged.
- Keep the database up to date with acknowledgements to avoid missed notifications.
- Handle potential failures in acknowledgement by allowing consumers to re-acknowledge notifications if needed.

### 5. Security & Privacy

- Defer authentication implementation for now; focus on core functionality.
- Ensure notification data is only returned to consumers subscribed to relevant tags.

---

## Next Steps

- Design/update models to store consumer subscriptions and notification acknowledgements.
- Draft REST API endpoints for:
  - Consumer registration/subscription
  - Polling for notifications
  - Acknowledging notifications
- Review `core/notification_bus.py` and related models/views in `webapp/core/` to align implementation.
- Plan for handling edge cases (e.g., failed ACKs, duplicate notifications).

---

## Questions

## Answers to Planning Questions

- **Should consumer subscription info be stored in a new model, or can it be added to an existing one?**  
  Yes, a new model should be created to track consumer subscriptions and their tags, as there is no existing model for this purpose.

- **Are there existing endpoints in `views_notifications.py` or elsewhere that can be extended for this functionality?**  
  No, there are currently no endpoints for consumer registration or subscription management. New endpoints will need to be implemented for registration, polling, and acknowledgement.

- **Should notification tags support complex queries (e.g., multiple providers/rooms per consumer)?**  
  No, each consumer will provide their own set of tags. Complex queries are not required; notifications will be filtered according to the consumer's tags.

- **Is there a preferred format for the acknowledgement payload (single/multiple notification IDs)?**  
  Yes, a list of notification IDs should be used for acknowledgement, allowing for both batch and single ACKs.

---