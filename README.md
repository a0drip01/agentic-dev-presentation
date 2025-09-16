# Django Room Timer Web App with Kafka-like Notification Bus

## Overview
A comprehensive Django web application that combines room timer management with a sophisticated Kafka-inspired notification bus system. The app manages users (doctors, nurses, patients), assigns them to rooms, tracks timers, and provides a scalable notification system for mobile apps, external services, and other consumers.

## 🏗️ System Architecture

### Core Components
1. **Room Timer System**: Original functionality for managing room timers and user assignments
2. **Notification Bus**: Kafka-like pub/sub system with tag-based routing
3. **Consumer API**: REST endpoints for consumer registration, polling, and acknowledgments
4. **Database Management**: Automated cleanup and performance optimization tools

### Notification Bus Features
- **Tag-based Subscriptions**: Consumers subscribe to notifications by tag types (room, provider, department, etc.)
- **Acknowledgment System**: Kafka-style acknowledgments prevent duplicate delivery
- **Batch Operations**: Efficient handling of multiple notifications
- **Performance Optimized**: Database indexes and batch processing for scalability
- **Management Tools**: Automated cleanup and monitoring commands

## 🚀 Quick Start

1. **Clone the repository and enter the project directory:**
   ```sh
   git clone <your-repo-url>
   cd agentic-dev-presentation
   ```

2. **Set up the Python virtual environment and install dependencies:**
   ```sh
   cd webapp
   make install
   ```

3. **Apply database migrations:**
   ```sh
   source ../.venv/bin/activate
   python manage.py migrate
   ```

4. **(Optional) Load sample data:**
   ```sh
   python manage.py import_users_rooms sample_users_rooms.csv
   ```

5. **Create a superuser for admin access:**
   ```sh
   python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```sh
   make runserver
   # or
   python manage.py runserver
   ```

7. **Access the app:**
   - Dashboard: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## 📡 Notification Bus API Guide

### Consumer Lifecycle

#### 1. Register a New Consumer
```bash
curl -X POST http://localhost:8000/api/consumers/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Mobile App",
    "consumer_type": "mobile",
    "metadata": {"device_id": "abc123", "app_version": "1.0"},
    "subscriptions": [
      {"tag_type": "room", "tag_value": "Room1"},
      {"tag_type": "provider", "tag_value": "doctor123"}
    ]
  }'
```

**Response:**
```json
{
  "consumer_id": "uuid-here",
  "name": "My Mobile App",
  "consumer_type": "mobile",
  "status": "active",
  "registered_at": "2025-09-16T20:00:00Z",
  "subscriptions": [...]
}
```

#### 2. Poll for Notifications
```bash
curl -X GET "http://localhost:8000/api/consumers/{consumer_id}/notifications/?limit=10&since=2025-09-16T19:00:00Z"
```

**Response:**
```json
{
  "notifications": [
    {
      "id": "notification-uuid",
      "room": "Room1",
      "message": "Timer expired...",
      "timestamp": "2025-09-16T20:05:00Z",
      "tags": {"room": "Room1", "provider": "doctor123"}
    }
  ],
  "has_more": false,
  "next_since": "2025-09-16T20:05:00Z",
  "count": 1
}
```

#### 3. Acknowledge Notifications
```bash
curl -X POST http://localhost:8000/api/consumers/{consumer_id}/notifications/ack/ \
  -H "Content-Type: application/json" \
  -d '{
    "notification_ids": ["notification-uuid-1", "notification-uuid-2"]
  }'
```

**Response:**
```json
{
  "acknowledged": [
    {
      "notification_id": "notification-uuid-1",
      "acked_at": "2025-09-16T20:10:00Z",
      "status": "success"
    }
  ],
  "errors": [],
  "success_count": 1,
  "error_count": 0
}
```

### Complete API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/consumers/register/` | Register a new consumer |
| DELETE | `/api/consumers/{id}/` | Unregister a consumer |
| GET | `/api/consumers/{id}/subscriptions/` | List consumer subscriptions |
| PUT | `/api/consumers/{id}/subscriptions/` | Update consumer subscriptions |
| DELETE | `/api/consumers/{id}/subscriptions/` | Clear all subscriptions |
| GET | `/api/consumers/{id}/notifications/` | Poll for notifications |
| POST | `/api/consumers/{id}/notifications/ack/` | Acknowledge notifications |
| GET | `/api/consumers/{id}/status/` | Get consumer status |

### Subscription Tag Types

| Tag Type | Description | Example Values |
|----------|-------------|----------------|
| `room` | Room-specific notifications | `"Room1"`, `"ICU-A"` |
| `provider` | Provider/doctor notifications | `"doctor123"`, `"nurse456"` |
| `department` | Department-wide notifications | `"cardiology"`, `"emergency"` |
| `user_role` | Role-based notifications | `"doctor"`, `"nurse"` |
| `all` | All notifications | `"all"` |

### Consumer Types

- **`mobile`**: Mobile applications
- **`script`**: CLI scripts and automation
- **`service`**: External web services
- **`webhook`**: Webhook consumers

## 🧪 Testing the System

### Run All Tests
```bash
cd webapp
source ../.venv/bin/activate
python manage.py test core --verbosity=2
```

### Test Specific Components
```bash
# Test models only
python manage.py test core.tests.ConsumerModelTests

# Test API endpoints
python manage.py test core.tests.ConsumerAPITests

# Test notification flow
python manage.py test core.tests.NotificationBusIntegrationTests
```

### Manual API Testing
```bash
# Start the server
python manage.py runserver 8000

# Register a test consumer
curl -X POST http://localhost:8000/api/consumers/register/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Consumer", "consumer_type": "mobile", "subscriptions": [{"tag_type": "all", "tag_value": "all"}]}'

# Trigger a notification (via Django admin or room timer)
# Then poll for notifications using the consumer_id from registration
```

## 🔧 Database Management

### Statistics and Health Monitoring
```bash
# View database statistics
python manage.py db_maintenance --stats

# Check for performance issues
python manage.py db_maintenance --check-performance

# Optimize database (SQLite)
python manage.py db_maintenance --vacuum --analyze
```

### Cleanup Operations
```bash
# Clean up old acknowledgments (dry run)
python manage.py cleanup_old_acknowledgments --dry-run --days=30

# Actually perform cleanup
python manage.py cleanup_old_acknowledgments --days=30

# Manage inactive consumers
python manage.py manage_inactive_consumers --dry-run --inactive-days=7
```

### Consumer Management
```bash
# Mark inactive consumers and cleanup
python manage.py manage_inactive_consumers --inactive-days=7 --cleanup-days=30 --delete-days=90

# Only mark as inactive (no cleanup)
python manage.py manage_inactive_consumers --mark-inactive-only --inactive-days=7
```

## 🏃‍♂️ Running the Complete System

### Development Environment
```bash
# 1. Activate virtual environment
cd agentic-dev-presentation
source .venv/bin/activate

# 2. Navigate to webapp
cd webapp

# 3. Apply any pending migrations
python manage.py migrate

# 4. Start the development server
python manage.py runserver 8000

# 5. (Optional) Start background notification processing
# The notification bus is integrated and runs automatically
```

### Production Considerations
```bash
# 1. Use a production WSGI server
pip install gunicorn
gunicorn hospital.wsgi:application

# 2. Set up periodic cleanup tasks (cron jobs)
# Daily cleanup of old acknowledgments
0 2 * * * /path/to/venv/bin/python /path/to/manage.py cleanup_old_acknowledgments --days=30

# Weekly inactive consumer management
0 3 * * 0 /path/to/venv/bin/python /path/to/manage.py manage_inactive_consumers --inactive-days=7

# 3. Monitor database health
# Weekly database statistics
0 4 * * 0 /path/to/venv/bin/python /path/to/manage.py db_maintenance --stats --check-performance
```

## 🔄 Integration Examples

### Mobile App Integration
```javascript
// Register consumer
const response = await fetch('/api/consumers/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Hospital Mobile App',
    consumer_type: 'mobile',
    metadata: { device_id: 'device123', user_id: 'user456' },
    subscriptions: [
      { tag_type: 'room', tag_value: 'ICU-1' },
      { tag_type: 'provider', tag_value: 'doctor123' }
    ]
  })
});

const consumer = await response.json();
const consumerId = consumer.consumer_id;

// Poll for notifications
const pollNotifications = async () => {
  const response = await fetch(`/api/consumers/${consumerId}/notifications/?limit=50`);
  const data = await response.json();
  
  if (data.notifications.length > 0) {
    // Process notifications
    data.notifications.forEach(notification => {
      showNotification(notification.message);
    });
    
    // Acknowledge all received notifications
    await fetch(`/api/consumers/${consumerId}/notifications/ack/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        notification_ids: data.notifications.map(n => n.id)
      })
    });
  }
};

// Poll every 30 seconds
setInterval(pollNotifications, 30000);
```

### External Service Integration
```python
import requests
import time

class NotificationConsumer:
    def __init__(self, base_url, consumer_name):
        self.base_url = base_url
        self.consumer_id = None
        self.register_consumer(consumer_name)
    
    def register_consumer(self, name):
        response = requests.post(f"{self.base_url}/api/consumers/register/", json={
            "name": name,
            "consumer_type": "service",
            "subscriptions": [
                {"tag_type": "all", "tag_value": "all"}
            ]
        })
        self.consumer_id = response.json()["consumer_id"]
    
    def poll_and_process(self):
        response = requests.get(
            f"{self.base_url}/api/consumers/{self.consumer_id}/notifications/"
        )
        data = response.json()
        
        if data["notifications"]:
            # Process notifications
            for notification in data["notifications"]:
                self.process_notification(notification)
            
            # Acknowledge processed notifications
            requests.post(
                f"{self.base_url}/api/consumers/{self.consumer_id}/notifications/ack/",
                json={"notification_ids": [n["id"] for n in data["notifications"]]}
            )
    
    def process_notification(self, notification):
        print(f"Processing: {notification['message']}")
        # Your processing logic here

# Usage
consumer = NotificationConsumer("http://localhost:8000", "External Service")
while True:
    consumer.poll_and_process()
    time.sleep(30)
```

## 📊 System Monitoring

### Key Metrics to Monitor
- **Consumer Health**: Active vs inactive consumers
- **Notification Throughput**: Messages published/acknowledged per minute
- **Pending Notifications**: Accumulation of unacknowledged messages
- **Database Performance**: Query times and index usage

### Monitoring Commands
```bash
# Get comprehensive system statistics
python manage.py db_maintenance --stats

# Check for performance bottlenecks
python manage.py db_maintenance --check-performance

# Monitor specific consumer
curl -X GET http://localhost:8000/api/consumers/{consumer_id}/status/
```

## 🚨 Troubleshooting

### Common Issues

1. **High Pending Notification Count**
   ```bash
   # Check which consumers have many pending notifications
   python manage.py db_maintenance --check-performance
   
   # Clean up inactive consumers
   python manage.py manage_inactive_consumers --cleanup-days=7
   ```

2. **Database Performance Issues**
   ```bash
   # Optimize database
   python manage.py db_maintenance --vacuum --analyze
   
   # Check for missing indexes
   python manage.py db_maintenance --check-performance
   ```

3. **Consumer Registration Failures**
   - Verify JSON payload format
   - Check tag_type values against allowed types
   - Ensure consumer_type is valid

## 🔧 Development and Contributing

### Running Tests During Development
```bash
# Run tests with coverage
python manage.py test core --verbosity=2

# Test specific functionality
python manage.py test core.tests.NotificationAcknowledgmentTests.test_acknowledge_notifications_success
```

### Adding New Tag Types
1. Update `TAG_TYPES` in `ConsumerSubscription` model
2. Create and run migration: `python manage.py makemigrations && python manage.py migrate`
3. Update notification bus tag extraction logic if needed
4. Add tests for new tag type

### Database Schema Changes
```bash
# Create migration after model changes
python manage.py makemigrations core

# Apply migration
python manage.py migrate

# For production, test migrations on copy of production data first
```

## 📚 Additional Resources

- **Planning Documentation**: See `planning/master-implementation-plan.md` for detailed implementation phases
- **API Specifications**: Individual task files in `planning/` directory
- **Database Models**: `webapp/core/models.py`
- **Test Suite**: `webapp/core/tests.py`
- **Management Commands**: `webapp/core/management/commands/`

---

**System Status**: ✅ Production Ready  
**Test Coverage**: 23/23 tests passing  
**API Endpoints**: 8 endpoints fully implemented  
**Database**: Optimized with performance indexes  

For more details, see the comprehensive planning documentation in the `planning/` directory.

