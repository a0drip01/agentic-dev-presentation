from django.shortcuts import render
from core.models import Room, ObserverSubscription, Consumer, Notification, ConsumerNotificationAck, ConsumerNotificationPending
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q, Count, Prefetch
from datetime import datetime, timedelta
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


def notifications_dashboard(request):
    """
    Display a comprehensive dashboard of all notifications with acknowledgment status and filtering.
    """
    # Get filter parameters
    room_filter = request.GET.get('room', '')
    status_filter = request.GET.get('status', '')  # all, acked, pending, expired
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    consumer_type = request.GET.get('consumer_type', '')
    search = request.GET.get('search', '')

    # Base queryset with related data
    notifications = Notification.objects.select_related().prefetch_related(
        Prefetch('consumer_acknowledgments', queryset=ConsumerNotificationAck.objects.select_related('consumer')),
        Prefetch('pending_for_consumers', queryset=ConsumerNotificationPending.objects.select_related('consumer'))
    ).annotate(
        ack_count=Count('consumer_acknowledgments'),
        pending_count=Count('pending_for_consumers')
    ).order_by('-timestamp')

    # Apply filters
    if room_filter:
        notifications = notifications.filter(
            Q(room__name__icontains=room_filter) | Q(message__icontains=room_filter)
        )
    
    if search:
        notifications = notifications.filter(
            Q(message__icontains=search) | 
            Q(room__name__icontains=search)
        )
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            notifications = notifications.filter(timestamp__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            notifications = notifications.filter(timestamp__lt=to_date)
        except ValueError:
            pass

    # Process notification data with acknowledgment details
    notification_data = []
    for notification in notifications:
        # Get acknowledgments and pending status
        acks = notification.consumer_acknowledgments.all()
        pending = notification.pending_for_consumers.all()
        
        # Calculate status
        total_consumers = Consumer.objects.filter(status='active').count()
        ack_count = acks.count()
        pending_count = pending.count()
        
        if ack_count == 0 and pending_count == 0:
            status = 'no_consumers'
        elif ack_count == total_consumers and pending_count == 0:
            status = 'fully_acked'
        elif pending_count > 0:
            status = 'pending'
        else:
            status = 'partial_ack'
        
        # Check if expired (older than 1 hour and still pending)
        is_expired = (
            timezone.now() - notification.timestamp > timedelta(hours=1) and 
            pending_count > 0
        )
        
        if is_expired:
            status = 'expired'
        
        # Apply status filter
        if status_filter:
            if status_filter == 'acked' and status not in ['fully_acked', 'partial_ack']:
                continue
            elif status_filter == 'pending' and status != 'pending':
                continue
            elif status_filter == 'expired' and status != 'expired':
                continue
            elif status_filter == status_filter and status != status_filter:
                continue
        
        # Apply consumer type filter
        if consumer_type:
            relevant_acks = [ack for ack in acks if ack.consumer.consumer_type == consumer_type]
            relevant_pending = [p for p in pending if p.consumer.consumer_type == consumer_type]
            if not relevant_acks and not relevant_pending:
                continue
        
        notification_data.append({
            'notification': notification,
            'status': status,
            'ack_count': ack_count,
            'pending_count': pending_count,
            'total_consumers': total_consumers,
            'is_expired': is_expired,
            'acknowledgments': [
                {
                    'consumer': ack.consumer,
                    'acknowledged_at': ack.acknowledged_at
                } for ack in acks
            ],
            'pending_consumers': [
                {
                    'consumer': p.consumer,
                    'matched_tags': p.matched_tags,
                    'created_at': p.created_at
                } for p in pending
            ]
        })
    
    # Get context data for filters
    rooms = Room.objects.all()
    consumer_types = Consumer.CONSUMER_TYPES
    
    # Summary statistics
    total_notifications = len(notification_data)
    fully_acked = len([n for n in notification_data if n['status'] == 'fully_acked'])
    pending = len([n for n in notification_data if n['status'] == 'pending'])
    expired = len([n for n in notification_data if n['status'] == 'expired'])
    
    context = {
        'notification_data': notification_data,
        'rooms': rooms,
        'consumer_types': consumer_types,
        'filters': {
            'room': room_filter,
            'status': status_filter,
            'date_from': date_from,
            'date_to': date_to,
            'consumer_type': consumer_type,
            'search': search,
        },
        'stats': {
            'total': total_notifications,
            'fully_acked': fully_acked,
            'pending': pending,
            'expired': expired,
        }
    }
    
    return render(request, 'dashboard/notifications_dashboard.html', context)
