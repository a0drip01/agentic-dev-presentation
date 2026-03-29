#!/usr/bin/env python
"""
Script to set up test data for Phase 5 polling endpoint testing.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital.settings')
django.setup()

from core.models import Consumer, ConsumerSubscription, Room, User, Notification
from core.notification_bus import NotificationBus
from django.contrib.auth import get_user_model

def setup_test_data():
    print("Setting up test data...")
    
    # Create rooms
    room1, _ = Room.objects.get_or_create(name="Room1", defaults={'timer_seconds': 300})
    room2, _ = Room.objects.get_or_create(name="Room2", defaults={'timer_seconds': 600})
    
    # Create users
    User = get_user_model()
    doctor1, _ = User.objects.get_or_create(
        username="dr_smith", 
        defaults={'role': 'doctor', 'assigned_room': room1}
    )
    doctor2, _ = User.objects.get_or_create(
        username="dr_jones", 
        defaults={'role': 'doctor', 'assigned_room': room2}
    )
    nurse1, _ = User.objects.get_or_create(
        username="nurse_alice", 
        defaults={'role': 'nurse', 'assigned_room': room1}
    )
    
    # Assign users to rooms
    room1.users.add(doctor1, nurse1)
    room2.users.add(doctor2)
    
    # Create consumers
    consumer1, _ = Consumer.objects.get_or_create(
        name="Mobile App Test 1",
        defaults={
            'consumer_type': 'mobile',
            'status': 'active',
            'metadata': {'device_id': 'test_device_1', 'app_version': '1.0'}
        }
    )
    
    consumer2, _ = Consumer.objects.get_or_create(
        name="Mobile App Test 2", 
        defaults={
            'consumer_type': 'mobile',
            'status': 'active',
            'metadata': {'device_id': 'test_device_2', 'app_version': '1.0'}
        }
    )
    
    # Create subscriptions
    # Consumer 1 subscribes to Room1 and all providers
    ConsumerSubscription.objects.get_or_create(
        consumer=consumer1,
        tag_type='room',
        tag_value='Room1'
    )
    ConsumerSubscription.objects.get_or_create(
        consumer=consumer1,
        tag_type='provider',
        tag_value='dr_smith'
    )
    
    # Consumer 2 subscribes to all notifications
    ConsumerSubscription.objects.get_or_create(
        consumer=consumer2,
        tag_type='all',
        tag_value='all'
    )
    
    print(f"Consumer 1 ID: {consumer1.id}")
    print(f"Consumer 2 ID: {consumer2.id}")
    
    # Create some notifications via the notification bus
    print("Creating test notifications...")
    
    # Notification from Room1 - should match consumer1 (room subscription) and consumer2 (all subscription)
    notification1 = NotificationBus.publish(room1, "Timer expired in Room1 - urgent attention needed")
    
    # Notification from Room2 - should only match consumer2 (all subscription)
    notification2 = NotificationBus.publish(room2, "Patient alert in Room2")
    
    # Another notification from Room1 - should match both consumers
    notification3 = NotificationBus.publish(room1, "Medication reminder for Room1")
    
    print(f"Created notifications: {notification1.id}, {notification2.id}, {notification3.id}")
    
    # Check pending notifications
    pending1 = consumer1.pending_notifications.count()
    pending2 = consumer2.pending_notifications.count()
    
    print(f"Consumer 1 has {pending1} pending notifications")
    print(f"Consumer 2 has {pending2} pending notifications")
    
    print("\nTest data setup complete!")
    print(f"Use these consumer IDs to test the polling endpoint:")
    print(f"Consumer 1: {consumer1.id}")
    print(f"Consumer 2: {consumer2.id}")

if __name__ == "__main__":
    setup_test_data()