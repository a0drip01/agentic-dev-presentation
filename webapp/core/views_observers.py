from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from django.shortcuts import get_object_or_404
from core.models import Room, ObserverSubscription
from core.notification_bus import NotificationBus
import json
import uuid

@csrf_exempt
@require_http_methods(["POST"])
def register_observer(request):
    """
    Register a new observer (iPhone app) for room notifications.
    
    POST /api/observers/register/
    {
        "name": "iPhone App - Dr. Smith",
        "observer_type": "mobile_app",
        "room_name": "ICU-1",
        "callback_url": "https://your-app-server.com/notifications",
        "callback_method": "POST",
        "callback_headers": {"Authorization": "Bearer token123"},
        "timeout_seconds": 10,
        "retry_count": 3,
        "metadata": {"device_id": "iPhone123", "user_id": "drsmith"}
    }
    """
    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ['name', 'room_name', 'callback_url']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'{field} is required'}, status=400)
        
        # Get the room
        try:
            room = Room.objects.get(name=data['room_name'])
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)
        
        # Prepare observer data
        observer_data = {
            'name': data['name'],
            'observer_type': data.get('observer_type', 'mobile_app'),
            'callback_url': data['callback_url'],
            'callback_method': data.get('callback_method', 'POST'),
            'callback_headers': data.get('callback_headers', {}),
            'timeout_seconds': data.get('timeout_seconds', 10),
            'retry_count': data.get('retry_count', 3),
            'metadata': data.get('metadata', {})
        }
        
        # Register the observer
        observer = NotificationBus.register_observer(room, observer_data)
        
        # Return the created observer info
        response_data = {
            'observer_id': str(observer.id),
            'name': observer.name,
            'observer_type': observer.observer_type,
            'room': observer.room.name,
            'callback_url': observer.callback_url,
            'status': observer.status,
            'created_at': observer.created_at.isoformat(),
            'metadata': observer.metadata
        }
        
        return JsonResponse(response_data, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def unregister_observer(request, observer_id):
    """
    Unregister an observer.
    
    DELETE /api/observers/{observer_id}/
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(observer_id)
        except ValueError:
            return JsonResponse({'error': 'Invalid observer ID format'}, status=400)
        
        # Attempt to unregister
        success = NotificationBus.unregister_observer(observer_id)
        
        if success:
            return JsonResponse({'status': 'unregistered'}, status=200)
        else:
            return JsonResponse({'error': 'Observer not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_GET
def get_observer_status(request, observer_id):
    """
    Get observer status and statistics.
    
    GET /api/observers/{observer_id}/status/
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(observer_id)
        except ValueError:
            return JsonResponse({'error': 'Invalid observer ID format'}, status=400)
        
        # Wrap the database query in a try-catch for UUID threading issues
        try:
            observer = get_object_or_404(ObserverSubscription, id=observer_id)
        except AttributeError as e:
            if "'UUID' object has no attribute 'replace'" in str(e):
                # Retry with a fresh database connection
                from django.db import connection
                connection.close()
                observer = get_object_or_404(ObserverSubscription, id=observer_id)
            else:
                raise e
        
        response_data = {
            'observer_id': str(observer.id),
            'name': observer.name,
            'observer_type': observer.observer_type,
            'room': observer.room.name,
            'status': observer.status,
            'created_at': observer.created_at.isoformat(),
            'last_notified_at': observer.last_notified_at.isoformat() if observer.last_notified_at else None,
            'last_success_at': observer.last_success_at.isoformat() if observer.last_success_at else None,
            'failure_count': observer.failure_count,
            'max_failures': observer.max_failures,
            'is_active': observer.is_active(),
            'callback_url': observer.callback_url,
            'metadata': observer.metadata
        }
        
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        error_msg = str(e)
        if "'UUID' object has no attribute 'replace'" in error_msg:
            # Handle the UUID threading error specifically
            try:
                # Force a new database connection and retry
                from django.db import connections
                for conn in connections.all():
                    conn.close()
                observer = ObserverSubscription.objects.get(id=observer_id)
                
                response_data = {
                    'observer_id': str(observer.id),
                    'name': observer.name,
                    'observer_type': observer.observer_type,
                    'room': observer.room.name,
                    'status': observer.status,
                    'created_at': observer.created_at.isoformat(),
                    'last_notified_at': observer.last_notified_at.isoformat() if observer.last_notified_at else None,
                    'last_success_at': observer.last_success_at.isoformat() if observer.last_success_at else None,
                    'failure_count': observer.failure_count,
                    'max_failures': observer.max_failures,
                    'is_active': observer.is_active(),
                    'callback_url': observer.callback_url,
                    'metadata': observer.metadata
                }
                
                return JsonResponse(response_data, status=200)
                
            except Exception as retry_error:
                return JsonResponse({'error': f'Database connection issue: {str(retry_error)}'}, status=500)
        
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_observer(request, observer_id):
    """
    Update observer configuration.
    
    PUT /api/observers/{observer_id}/
    {
        "name": "Updated Name",
        "callback_url": "https://new-url.com/notifications",
        "callback_headers": {"Authorization": "Bearer newtoken"},
        "metadata": {"device_id": "newdevice"}
    }
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(observer_id)
        except ValueError:
            return JsonResponse({'error': 'Invalid observer ID format'}, status=400)
        
        observer = get_object_or_404(ObserverSubscription, id=observer_id)
        data = json.loads(request.body)
        
        # Update allowed fields
        if 'name' in data:
            observer.name = data['name']
        if 'callback_url' in data:
            observer.callback_url = data['callback_url']
        if 'callback_headers' in data:
            observer.callback_headers = data['callback_headers']
        if 'timeout_seconds' in data:
            observer.timeout_seconds = data['timeout_seconds']
        if 'retry_count' in data:
            observer.retry_count = data['retry_count']
        if 'metadata' in data:
            observer.metadata = data['metadata']
        
        # Reset failure count if reactivating
        if 'status' in data and data['status'] == 'active' and observer.status == 'failed':
            observer.failure_count = 0
            
        if 'status' in data:
            observer.status = data['status']
        
        observer.save()
        
        response_data = {
            'observer_id': str(observer.id),
            'name': observer.name,
            'observer_type': observer.observer_type,
            'room': observer.room.name,
            'callback_url': observer.callback_url,
            'status': observer.status,
            'updated_at': observer.created_at.isoformat(),  # Django doesn't have updated_at by default
            'metadata': observer.metadata
        }
        
        return JsonResponse(response_data, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def list_room_observers(request, room_name):
    """
    List all observers for a specific room.
    
    GET /api/rooms/{room_name}/observers/
    """
    try:
        room = get_object_or_404(Room, name=room_name)
        
        observers = ObserverSubscription.objects.filter(room=room).order_by('-created_at')
        
        observers_data = []
        for observer in observers:
            observers_data.append({
                'observer_id': str(observer.id),
                'name': observer.name,
                'observer_type': observer.observer_type,
                'status': observer.status,
                'created_at': observer.created_at.isoformat(),
                'last_notified_at': observer.last_notified_at.isoformat() if observer.last_notified_at else None,
                'failure_count': observer.failure_count,
                'is_active': observer.is_active(),
                'metadata': observer.metadata
            })
        
        return JsonResponse({
            'room': room_name,
            'observers': observers_data,
            'total_observers': len(observers_data),
            'active_observers': len([o for o in observers_data if o['is_active']])
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)