from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
import json

from campaign_manager.models import APIKey
from delivery_cloud.models import AgentResource

# Create your views here.


@csrf_exempt
def api_create_resource(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    key = request.headers.get('X-API-KEY') or request.META.get('HTTP_X_API_KEY')
    if not APIKey.objects.filter(pk=key, is_active=True).exists():
        return JsonResponse({'error': 'Invalid API Key'}, status=403)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    url = data.get('url')
    if not url:
        return JsonResponse({'error': '"url" is required'}, status=400)
    
    defaults = {}
    for field in ('resource_type', 'is_active', 'caption'):
        if field in data:
            defaults[field] = data[field]
    
    # Validate resource_type if provided
    if 'resource_type' in defaults:
        valid_types = [choice[0] for choice in AgentResource.RESOURCE_TYPE_CHOICES]
        if defaults['resource_type'] not in valid_types:
            return JsonResponse({'error': f'resource_type must be one of: {valid_types}'}, status=400)
    
    # Truncate caption to 255 characters if provided
    if 'caption' in defaults and defaults['caption']:
        defaults['caption'] = defaults['caption'][:255]
    
    resource = AgentResource.objects.create(url=url, **defaults)
    return JsonResponse({'id': resource.id, 'url': resource.url, 'resource_type': resource.resource_type, 'caption': resource.caption}, status=201)
