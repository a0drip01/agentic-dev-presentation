# Task: URL Routing and API Structure

## Goals
- Define URL patterns for consumer API endpoints and integrate with Django routing.

## URL Structure

### Consumer Management
```
POST   /api/consumers/register/                    # Register new consumer
PUT    /api/consumers/{consumer_id}/subscriptions/ # Update subscriptions  
DELETE /api/consumers/{consumer_id}/               # Unregister consumer
GET    /api/consumers/{consumer_id}/               # Get consumer info
```

### Notification Operations
```
GET    /api/consumers/{consumer_id}/notifications/     # Poll for notifications
POST   /api/consumers/{consumer_id}/notifications/ack/ # Acknowledge notifications
```

### Health/Status
```
GET    /api/consumers/{consumer_id}/status/        # Check consumer status
GET    /api/health/                               # API health check
```

## Implementation Steps

### 1. Create core/urls.py
```python
from django.urls import path
from . import views_notifications

app_name = 'core'

urlpatterns = [
    # Existing
    path('notifications/', views_notifications.notifications_for_room, name='notifications_for_room'),
    
    # New consumer API
    path('api/consumers/register/', views_notifications.register_consumer, name='register_consumer'),
    path('api/consumers/<uuid:consumer_id>/', views_notifications.consumer_detail, name='consumer_detail'),
    path('api/consumers/<uuid:consumer_id>/subscriptions/', views_notifications.update_subscriptions, name='update_subscriptions'),
    path('api/consumers/<uuid:consumer_id>/notifications/', views_notifications.poll_notifications, name='poll_notifications'),
    path('api/consumers/<uuid:consumer_id>/notifications/ack/', views_notifications.ack_notifications, name='ack_notifications'),
    path('api/consumers/<uuid:consumer_id>/status/', views_notifications.consumer_status, name='consumer_status'),
    path('api/health/', views_notifications.health_check, name='health_check'),
]
```

### 2. Update hospital/urls.py
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('dashboard/', include('dashboard.urls')),
]
```

## Content-Type and CORS
- All API endpoints should accept `application/json`
- Add CORS headers for mobile app access
- Add proper error responses (400, 404, 500)

## API Versioning Strategy
- Start with `/api/` prefix
- Plan for `/api/v1/` if versioning becomes needed
- Keep backward compatibility for existing endpoints

## Deliverables
- core/urls.py with all consumer endpoints
- Updated hospital/urls.py to include core URLs
- CORS configuration
- API documentation with full URL examples