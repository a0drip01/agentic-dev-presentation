"""
Simple test to verify our observer pattern works from Django shell.
Run with: python manage.py shell < test_observer_simple.py
"""

from core.models import Room, ObserverSubscription
from core.notification_bus import NotificationBus

print("🚀 Testing Observer Pattern Implementation")
print("=" * 50)

# Test 1: Create or get a room
room, created = Room.objects.get_or_create(name="ICU-1")
if created:
    print(f"✅ Created room: {room.name}")
else:
    print(f"✅ Using existing room: {room.name}")

# Test 2: Register an observer
observer_data = {
    "name": "iPhone App - Test",
    "observer_type": "mobile_app",
    "callback_url": "https://httpbin.org/post",
    "callback_headers": {"Authorization": "Bearer test123"},
    "metadata": {"device_id": "test_device"}
}

try:
    observer = NotificationBus.register_observer(room, observer_data)
    print(f"✅ Observer registered: {observer.name} (ID: {observer.id})")
except Exception as e:
    print(f"❌ Failed to register observer: {e}")
    exit()

# Test 3: List active observers
active_observers = NotificationBus.get_active_observers(room)
print(f"✅ Active observers for {room.name}: {active_observers.count()}")

# Test 4: Trigger a notification 
try:
    notification = NotificationBus.publish(room, "Test notification from observer pattern test")
    print(f"✅ Notification published: {notification.id}")
    print(f"   Message: {notification.message}")
except Exception as e:
    print(f"❌ Failed to publish notification: {e}")

# Test 5: Check observer status
observer.refresh_from_db()
print(f"✅ Observer status after notification:")
print(f"   Status: {observer.status}")
print(f"   Failure count: {observer.failure_count}")
print(f"   Last notified: {observer.last_notified_at}")

# Test 6: Clean up
observer.delete()
print(f"✅ Observer cleaned up")

print("=" * 50)
print("🎉 Observer Pattern Test Completed!")
print()
print("💡 The observer received a notification to: https://httpbin.org/post")
print("   You can check httpbin.org to verify the request was made.")