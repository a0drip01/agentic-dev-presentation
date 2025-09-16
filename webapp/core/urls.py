"""
URL configuration for consumer API endpoints.
Implements the Kafka-like notification bus REST API.
"""
from django.urls import path
from . import views

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
]