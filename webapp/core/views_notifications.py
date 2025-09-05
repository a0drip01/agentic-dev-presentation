from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from core.models import Room, Notification

@csrf_exempt
@require_GET
def notifications_for_room(request):
    room_name = request.GET.get('room')
    since = request.GET.get('since')  # Optional: ISO timestamp for polling since last fetch
    if not room_name:
        return JsonResponse({'error': 'room required'}, status=400)
    try:
        room = Room.objects.get(name=room_name)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    qs = Notification.objects.filter(room=room).order_by('-timestamp')
    if since:
        from django.utils.dateparse import parse_datetime
        since_dt = parse_datetime(since)
        if since_dt:
            qs = qs.filter(timestamp__gt=since_dt)
    notifications = [
        {
            'id': str(n.id),
            'room': n.room.name,
            'message': n.message,
            'timestamp': n.timestamp.isoformat(),
        }
        for n in qs
    ]
    return JsonResponse({'notifications': notifications})
