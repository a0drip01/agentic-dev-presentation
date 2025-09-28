"""
URL configuration for consumer API endpoints and observer pattern API.
Implements the Kafka-like notification bus REST API and database-persisted observer pattern.
"""
from django.urls import path
from . import views, views_observers

# Consumer management endpoints
urlpatterns = [
    # Consumer registration and management
    path('api/consumers/register/', views.register_consumer, name='register_consumer'),
    path('api/consumers/<uuid:consumer_id>/', views.unregister_consumer, name='unregister_consumer'),
    
    # Consumer subscription management  
    path('api/consumers/<uuid:consumer_id>/subscriptions/', views.manage_subscriptions, name='manage_subscriptions'),
    
    # Notification polling and retrieval
    path('api/consumers/<uuid:consumer_id>/notifications/', views.poll_notifications, name='poll_notifications'),
    
    # Notification acknowledgment
    path('api/consumers/<uuid:consumer_id>/notifications/ack/', views.acknowledge_notifications, name='acknowledge_notifications'),
    
    # Consumer status and health check
    path('api/consumers/<uuid:consumer_id>/status/', views.consumer_status, name='consumer_status'),
    
    # Observer pattern API endpoints (for iPhone app and other observers)
    path('api/observers/register/', views_observers.register_observer, name='register_observer'),
    path('api/observers/<uuid:observer_id>/', views_observers.unregister_observer, name='unregister_observer'),
    path('api/observers/<uuid:observer_id>/status/', views_observers.get_observer_status, name='get_observer_status'),
    path('api/observers/<uuid:observer_id>/update/', views_observers.update_observer, name='update_observer'),
    path('api/rooms/<str:room_name>/observers/', views_observers.list_room_observers, name='list_room_observers'),
]