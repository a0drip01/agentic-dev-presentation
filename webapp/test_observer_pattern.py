#!/usr/bin/env python3
"""
Test script for the improved observer pattern implementation.
Tests iPhone app observer registration and notification delivery.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
ROOM_NAME = "ICU-1"

def test_observer_registration():
    """Test registering an iPhone app as an observer."""
    print("🔄 Testing observer registration...")
    
    # Register an observer (iPhone app)
    observer_data = {
        "name": "iPhone App - Dr. Smith",
        "observer_type": "mobile_app",
        "room_name": ROOM_NAME,
        "callback_url": "https://httpbin.org/post",  # Using httpbin for testing
        "callback_method": "POST",
        "callback_headers": {
            "Authorization": "Bearer test_token_123",
            "X-App-Version": "1.0.0"
        },
        "timeout_seconds": 10,
        "retry_count": 2,
        "metadata": {
            "device_id": "iPhone_123",
            "user_id": "dr_smith",
            "app_version": "1.0.0",
            "os_version": "iOS 17.0"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/observers/register/",
            json=observer_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            observer = response.json()
            print(f"✅ Observer registered successfully!")
            print(f"   Observer ID: {observer['observer_id']}")
            print(f"   Name: {observer['name']}")
            print(f"   Room: {observer['room']}")
            return observer['observer_id']
        else:
            print(f"❌ Failed to register observer: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during registration: {e}")
        return None


def test_observer_status(observer_id):
    """Test getting observer status."""
    print(f"🔄 Testing observer status for {observer_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/observers/{observer_id}/status/")
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Observer status retrieved successfully!")
            print(f"   Status: {status['status']}")
            print(f"   Failure Count: {status['failure_count']}")
            print(f"   Is Active: {status['is_active']}")
            return True
        else:
            print(f"❌ Failed to get observer status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error getting status: {e}")
        return False


def test_list_room_observers():
    """Test listing all observers for a room."""
    print(f"🔄 Testing list observers for room {ROOM_NAME}...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/rooms/{ROOM_NAME}/observers/")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Room observers listed successfully!")
            print(f"   Total observers: {data['total_observers']}")
            print(f"   Active observers: {data['active_observers']}")
            for observer in data['observers']:
                print(f"   - {observer['name']} ({observer['status']})")
            return True
        else:
            print(f"❌ Failed to list room observers: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error listing observers: {e}")
        return False


def trigger_notification():
    """Trigger a notification to test observer notification."""
    print(f"🔄 Triggering a notification for room {ROOM_NAME}...")
    
    # This would normally be triggered by the timer system, 
    # but for testing we can simulate it using Django shell or admin interface
    print("   (This would be triggered by the timer system in normal operation)")
    print("   You can trigger a notification by:")
    print("   1. Using Django admin to start a timer on the room")
    print("   2. Running: python manage.py shell")
    print("   3. Then: from core.models import Room; Room.objects.get(name='ICU-1').notify_observers()")
    

def test_observer_unregistration(observer_id):
    """Test unregistering an observer."""
    print(f"🔄 Testing observer unregistration for {observer_id}...")
    
    try:
        response = requests.delete(f"{BASE_URL}/api/observers/{observer_id}/")
        
        if response.status_code == 200:
            print(f"✅ Observer unregistered successfully!")
            return True
        else:
            print(f"❌ Failed to unregister observer: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during unregistration: {e}")
        return False


def main():
    """Run all observer pattern tests."""
    print("🚀 Starting Observer Pattern Tests")
    print("=" * 50)
    
    # Test 1: Register observer
    observer_id = test_observer_registration()
    if not observer_id:
        print("❌ Cannot continue tests without observer registration")
        return
    
    print()
    
    # Test 2: Check observer status
    test_observer_status(observer_id)
    print()
    
    # Test 3: List room observers
    test_list_room_observers()
    print()
    
    # Test 4: Explain notification triggering
    trigger_notification()
    print()
    
    # Test 5: Unregister observer
    test_observer_unregistration(observer_id)
    
    print()
    print("=" * 50)
    print("🎉 Observer Pattern Tests Completed!")
    print()
    print("💡 To test actual notifications:")
    print("   1. Keep the observer registered")
    print("   2. Go to Django admin (http://localhost:8001/admin/)")
    print("   3. Find or create a room named 'ICU-1'")
    print("   4. Start a timer on the room")
    print("   5. Wait for the timer to expire")
    print("   6. Check httpbin.org to see if the notification was delivered")


if __name__ == "__main__":
    main()