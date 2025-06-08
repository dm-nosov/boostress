from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
import json

from campaign_manager.tasks import update_task_statuses
from campaign_manager.models import APIKey, Order, ProviderPlatform


# Create your views here.

def home(request):
    if settings.DEBUG:
        update_task_statuses.delay()
    return HttpResponse("")


@csrf_exempt
def api_create_order(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    key = request.headers.get('X-API-KEY') or request.META.get('HTTP_X_API_KEY')
    if not APIKey.objects.filter(pk=key, is_active=True).exists():
        return JsonResponse({'error': 'Invalid API Key'}, status=403)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    link = data.get('link')
    platform = data.get('platform')
    if not link or not platform:
        return JsonResponse({'error': '"link" and "platform" are required'}, status=400)
    try:
        platform_obj = ProviderPlatform.objects.get(name=platform)
    except ProviderPlatform.DoesNotExist:
        return JsonResponse({'error': f'Platform "{platform}" not found'}, status=400)
    defaults = {}
    for field in ('name', 'link_type', 'budget', 'deadline', 'time_sensible', 'total_followers',
                  'natural_time_cycles'):
        if field in data:
            defaults[field] = data[field]
    order, created = Order.objects.get_or_create(link=link, platform=platform_obj, defaults=defaults)
    return JsonResponse({'id': order.id, 'created': created}, status=201 if created else 200)
