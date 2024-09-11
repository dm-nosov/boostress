from django.http import HttpResponse

from campaign_manager.tasks import process_order


# Create your views here.

def home(request):
    process_order.delay(4)
    return HttpResponse("")
