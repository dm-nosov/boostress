from django.conf import settings
from django.http import HttpResponse

from campaign_manager.tasks import process_order, update_task_statuses


# Create your views here.

def home(request):
    if settings.DEBUG:
        update_task_statuses.delay()
    return HttpResponse("")
