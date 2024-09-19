from django.conf import settings
from django.http import HttpResponse

from campaign_manager.tasks import process_order


# Create your views here.

def home(request):
    if settings.DEBUG:
        process_order.delay(5)
    return HttpResponse("")
