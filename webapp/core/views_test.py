"""
Test notification endpoints for demo purposes.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from core.models import Room
from core.notification_bus import NotificationBus
import json


@csrf_exempt
@require_http_methods(["POST"])
def create_test_notification(request, room_name):
    """
    Create a test notification for a specific room.
    
    POST /api/rooms/{room_name}/test-notification/
    {
        "message": "Test notification message",
        "event_type": "test" (optional)
    }
    """
    try:
        # Get the room
        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            return JsonResponse({'error': f'Room {room_name} not found'}, status=404)
        
        # Parse request data
        data = {}
        if request.body:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                pass
        
        # Get message from request or use default
        message = data.get('message', f'TEST: Demo notification for {room_name} - Generated at {timezone.now()}')
        event_type = data.get('event_type', 'test')
        
        # Create the notification
        notification = NotificationBus.publish(room, message)
        
        response_data = {
            'notification_id': str(notification.id),
            'room': room.name,
            'message': message,
            'timestamp': notification.timestamp.isoformat(),
            'event_type': event_type,
            'status': 'sent'
        }
        
        return JsonResponse(response_data, status=201)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt  
@require_http_methods(["POST"])
def trigger_timer_notification(request, room_name):
    """
    Trigger a timer expiration notification for a room.
    
    POST /api/rooms/{room_name}/timer-notification/
    {
        "reason": "Custom expiration reason" (optional)
    }
    """
    try:
        # Get the room
        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            return JsonResponse({'error': f'Room {room_name} not found'}, status=404)
        
        # Parse request data
        data = {}
        if request.body:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                pass
        
        reason = data.get('reason', f'TEST: Timer notification for {room_name}')
        
        # Trigger timer notification
        notification = room.notify_observers(event_type='expired', reason=reason)
        
        response_data = {
            'notification_id': str(notification.id),
            'room': room.name,
            'event_type': 'timer_expired',
            'reason': reason,
            'timestamp': notification.timestamp.isoformat(),
            'status': 'sent'
        }
        
        return JsonResponse(response_data, status=201)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)