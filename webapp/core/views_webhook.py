from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from core.models import Room, WebhookSubscription

@csrf_exempt
@require_POST
def webhook_subscribe(request):
    try:
        data = json.loads(request.body)
        room_name = data.get('room_name')
        url = data.get('url')
        if not room_name or not url:
            return JsonResponse({'error': 'room_name and url required'}, status=400)
        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)
        # Prevent duplicate subscriptions
        sub, created = WebhookSubscription.objects.get_or_create(room=room, url=url)
        if created:
            return JsonResponse({'status': 'subscribed'}, status=201)
        else:
            return JsonResponse({'status': 'already subscribed'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
