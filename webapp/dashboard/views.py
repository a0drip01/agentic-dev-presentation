from django.shortcuts import render
from core.models import Room
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
