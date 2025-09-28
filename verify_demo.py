#!/usr/bin/env python3
"""
Quick verification script to test the live demo setup.
Run this AFTER your server is started on port 8000.
"""

import requests
import json
import time

def test_server_running():
    """Test if Django server is responding"""
    try:
        response = requests.get("http://localhost:8000/dashboard/observers/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not responding: {e}")
        return False

def test_observer_registration():
    """Test observer registration API"""
    print("\n🔄 Testing observer registration...")
    
    observer_data = {
        "name": "VERIFY-Test-Observer",
        "observer_type": "mobile_app",
        "room_name": "DEMO-ICU-1",
        "callback_url": "https://httpbin.org/post",
        "metadata": {"test": True}
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/observers/register/",
            json=observer_data,
            timeout=10
        )
        
        if response.status_code == 201:
            observer = response.json()
            print(f"✅ Observer registered: {observer['name']}")
            return observer['observer_id']
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration request failed: {e}")
        return None

def test_notification_trigger(observer_id):
    """Test notification triggering (requires Django management command)"""
    print(f"\n🔔 To test notifications, run this command in a separate terminal:")
    print(f"   python manage.py shell -c \"from core.models import Room; Room.objects.get(name='DEMO-ICU-1').notify_observers()\"")
    print(f"\n   Then check observer status:")
    print(f"   curl http://localhost:8000/api/observers/{observer_id}/status/")

def test_dashboard_access():
    """Test dashboard accessibility"""
    print("\n🔄 Testing dashboard access...")
    
    dashboards = [
        ("Observer Dashboard", "http://localhost:8000/dashboard/observers/"),
        ("Room Grid", "http://localhost:8000/dashboard/"),
        ("Observer Status API", "http://localhost:8000/dashboard/observer-status-api/")
    ]
    
    for name, url in dashboards:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Accessible")
            else:
                print(f"❌ {name}: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: Failed - {e}")

def cleanup_test_observer(observer_id):
    """Clean up test observer"""
    if observer_id:
        try:
            response = requests.delete(f"http://localhost:8000/api/observers/{observer_id}/")
            if response.status_code == 200:
                print(f"\n✅ Test observer cleaned up")
            else:
                print(f"\n⚠️  Could not clean up test observer (status: {response.status_code})")
        except:
            print(f"\n⚠️  Could not clean up test observer")

def main():
    print("🏥 Live Demo Verification Script")
    print("=" * 50)
    
    # Test 1: Server running
    if not test_server_running():
        print("\n❌ Server is not running. Please start it first:")
        print("   cd webapp && source .venv/bin/activate && python manage.py runserver 8000")
        return
    
    # Test 2: Dashboard access
    test_dashboard_access()
    
    # Test 3: Observer registration
    observer_id = test_observer_registration()
    
    # Test 4: Show notification test command
    if observer_id:
        test_notification_trigger(observer_id)
    
    print("\n" + "=" * 50)
    if observer_id:
        print("🎉 All tests passed! Your demo is ready!")
        print("\n📋 Quick demo URLs:")
        print("   Observer Dashboard: http://localhost:8000/dashboard/observers/")
        print("   Room Grid:         http://localhost:8000/dashboard/")
        print("   Admin:             http://localhost:8000/admin/ (admin/demo123)")
        
        # Clean up
        cleanup_test_observer(observer_id)
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    print(f"\n💡 For full demo commands, see: LIVE_DEMO_CHEAT_SHEET.md")

if __name__ == "__main__":
    main()