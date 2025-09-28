from django.shortcuts import render
from core.models import Room, ObserverSubscription, Consumer
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
import json

# Create your views here.

def room_grid(request):
    rooms = Room.objects.prefetch_related('users').all()
    now = timezone.now()
    room_data = []
    for room in rooms:
        users = room.users.all()
        doctors = users.filter(role='doctor')
        nurses = users.filter(role='nurse')
        patients = users.filter(role='patient')
        timer = None
        percent = 0
        timer_color = '#4caf50'
        if room.timer_started_at and room.timer_seconds > 0:
            elapsed = (now - room.timer_started_at).total_seconds()
            percent = min(100, int((elapsed / room.timer_seconds) * 100))
            if percent < 50:
                timer_color = '#4caf50'
            elif percent < 85:
                timer_color = '#ff9800'
            else:
                timer_color = '#f44336'
            timer = {
                'elapsed': int(elapsed),
                'total': room.timer_seconds,
                'percent': percent,
                'color': timer_color,
            }
        room_data.append({
            'room': room,
            'doctors': doctors,
            'nurses': nurses,
            'patients': patients,
            'timer': timer,
        })
    return render(request, 'dashboard/room_grid.html', {'room_data': room_data})

@require_POST
def set_room_timer(request, room_id):
    from core.models import Room
    try:
        data = json.loads(request.body)
        seconds = int(data.get('seconds', 0))
        room = Room.objects.get(id=room_id)
        if seconds > 0:
            room.start_timer(seconds)
        else:
            room.stop_timer()
        return JsonResponse({'status': 'ok', 'timer_seconds': seconds})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


def observer_dashboard(request):
    """Dashboard showing all observer and consumer registrations with real-time status"""
    observers = ObserverSubscription.objects.select_related('room').order_by('-created_at')
    consumers = Consumer.objects.prefetch_related('subscriptions').filter(status='active').order_by('-registered_at')
    
    # Get observer statistics by room
    observer_stats = {}
    for observer in observers:
        room_name = observer.room.name
        if room_name not in observer_stats:
            observer_stats[room_name] = {
                'total': 0,
                'active': 0,
                'failed': 0
            }
        observer_stats[room_name]['total'] += 1
        if observer.status == 'active':
            observer_stats[room_name]['active'] += 1
        elif observer.status == 'failed':
            observer_stats[room_name]['failed'] += 1
    
    # Get recent observer activities
    recent_observers = observers[:10]  # Last 10 observers
    recent_consumers = consumers[:10]  # Last 10 consumers
    
    context = {
        'observers': observers,
        'consumers': consumers,
        'observer_stats': observer_stats,
        'recent_observers': recent_observers,
        'recent_consumers': recent_consumers,
        'total_observers': observers.count(),
        'active_observers': observers.filter(status='active').count(),
        'total_consumers': consumers.count(),
    }
    
    return render(request, 'dashboard/observer_dashboard.html', context)


def observer_status_api(request):
    """API endpoint for real-time observer status updates"""
    observers = ObserverSubscription.objects.select_related('room').all()
    consumers = Consumer.objects.filter(status='active').all()
    
    observer_data = []
    for observer in observers:
        observer_data.append({
            'id': str(observer.id),
            'name': observer.name,
            'type': observer.observer_type,
            'room': observer.room.name,
            'status': observer.status,
            'failure_count': observer.failure_count,
            'last_notified': observer.last_notified_at.isoformat() if observer.last_notified_at else None,
            'created_at': observer.created_at.isoformat(),
        })
    
    consumer_data = []
    for consumer in consumers:
        consumer_data.append({
            'id': str(consumer.id),
            'name': consumer.name,
            'type': consumer.consumer_type,
            'status': consumer.status,
            'last_seen': consumer.last_seen_at.isoformat() if consumer.last_seen_at else None,
            'subscriptions': [
                {'tag_type': sub.tag_type, 'tag_value': sub.tag_value}
                for sub in consumer.subscriptions.all()
            ]
        })
    
    return JsonResponse({
        'observers': observer_data,
        'consumers': consumer_data,
        'timestamp': timezone.now().isoformat(),
    })
