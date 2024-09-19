import logging
import random
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from boostress.utils import time_difference_min, get_order_amount, get_num_times, get_interval
from campaign_manager.models import Order, Status, ServiceTask, Provider, ProviderPlatform, LinkType, PlatformService
from provider_api.api import ProviderApi


@shared_task(bind=True)
def process_order(self, order_id):
    active_order = Order.objects.get(pk=int(order_id))
    platform = active_order.platform
    link_type = active_order.link_type
    link = active_order.link

    [ProviderApi.update_task_statuses(provider, provider.get_active_tasks()) for provider in Provider.objects.all()]

    if (timezone.now() > timedelta(
            minutes=active_order.deadline) + active_order.created):
        active_order.status = Status.COMPLETED
        active_order.save()
        active_order.tasks.update(status=Status.COMPLETED)
        return {"result": "Order {} is complete by time, please pause the task".format(active_order.id)}

    available_providers = PlatformService.objects.get_providers_by_platform(platform, link_type)

    if not available_providers:
        return {"result": "Order {}, no available providers found".format(active_order.id)}

    # All providers which potentially provide the related services
    potential_providers = []

    busy_services = ServiceTask.objects.get_busy_services(platform, link_type, link)

    for provider in available_providers:

        available_services = provider.get_available_services(platform, link_type)

        if available_services:
            difference = [item for item in available_services if item not in busy_services]
            if difference:
                potential_providers.append((provider, random.choice(difference)))

    if not potential_providers:
        return {"result": "Existing the order {}, all providers are loaded".format(active_order.id)}

    # Add a task
    provider, service_type_name = random.choice(potential_providers)

    service = PlatformService.objects.filter(provider=provider, platform=platform, service_type__name=service_type_name,
                                             link_type=link_type).order_by('?').first()

    time_diff_min = time_difference_min(active_order.created)

    qty = get_order_amount(service.min, service.max, time_diff_min)

    if qty < service.min:
        return {"result": "The task received less than a minimum qty, {}".format(qty)}

    interval = get_interval(service.pre_complete_minutes, time_diff_min)
    try:
        ext_order_id, charged = ProviderApi.create_order(provider, service, active_order.link, qty)
    except Exception as exc:
        return {"result": "Exception in provider API, result {}".format(exc)}

    active_order.spent += charged

    if abs(active_order.spent - active_order.budget) < 0.01:
        active_order.status = Status.PRE_COMPLETE

    active_order.save()

    service_task = ServiceTask.objects.create(provider=provider, platform=platform, service=service,
                                              link_type=link_type,
                                              order=active_order, link=active_order.link, ext_order_id=ext_order_id,
                                              spent=charged,
                                              extras="qty={},interval={}".format(qty, interval))
    service_task.pre_complete_minutes = service.pre_complete_minutes
    service_task.save()

    return {"result": "Existing the order {}, new service task '{}', interval: {}".format(active_order.id,
                                                                                          service.service_type.name,
                                                                                          service_task.pre_complete_minutes)}
