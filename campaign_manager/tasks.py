import logging
import math
import random
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from boostress.utils import time_difference_min, get_order_amount, get_num_times, get_interval
from campaign_manager.models import Order, Status, ServiceTask, Provider, ProviderPlatform, LinkType, PlatformService
from provider_api.api import ProviderApi


def get_potential_providers(available_providers, platform, link_type, busy_services):
    tmp_providers = []
    for provider in available_providers:

        available_services = provider.get_available_services(platform, link_type)

        if available_services:
            difference = [item for item in available_services if item not in busy_services]
            if difference:
                tmp_providers.append((provider, random.choice(difference)))
    return tmp_providers


def get_qty(order_created, total_followers, service_min, service_max):
    time_diff_min = time_difference_min(order_created)
    share = random.randint(18, 23)
    affected_followers = math.floor(total_followers * share / 100)
    if affected_followers < service_min:
        return 0

    if affected_followers > service_max:
        affected_followers = service_max

    return get_order_amount(service_min, affected_followers, time_diff_min)


@shared_task(bind=True)
def process_order(self, order_id):


    active_order = Order.objects.get(pk=int(order_id))
    platform = active_order.platform
    link_type = active_order.link_type
    link = active_order.link

    self.name = "Order-{}-{}".format(active_order.id, timezone.now())


    if active_order.status == Status.COMPLETED:
        active_order.tasks.update(status=Status.COMPLETED)
        return {"result": "Order {} is completed".format(active_order.id)}

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

    busy_services = ServiceTask.objects.get_busy_services(platform, link_type, link)

    potential_providers = get_potential_providers(available_providers, platform, link_type, busy_services)

    if not potential_providers:
        return {"result": "Existing the order {}, all providers are loaded".format(active_order.id)}

    # Add a task
    provider, service_type_name = random.choice(potential_providers)

    service = PlatformService.objects.filter(provider=provider, platform=platform, service_type__name=service_type_name,
                                             link_type=link_type).order_by('?').first()

    self.name = "Order-{}-S{}-{}".format(active_order.id, service.service_id, timezone.now())

    if active_order.time_sensible:
        qty = get_qty(active_order.created, active_order.total_followers, service.min, service.max)
    else:
        qty = get_qty(timezone.now(), active_order.total_followers, service.min, service.max)

    if qty == 0:
        return {"result": "Order {}, qty is {}}, attempted the service {}, stopping the processing".format(active_order.id, qty, service.service_id)}

    try:
        ext_order_id, charged = ProviderApi.create_order(provider, service, active_order.link, qty)
    except Exception as exc:
        return {"result": "Exception in provider API, result {}".format(exc)}

    active_order.spent += charged

    if active_order.budget - active_order.spent < 0.01:
        active_order.status = Status.PRE_COMPLETE

    active_order.save()

    service_task = ServiceTask.objects.create(provider=provider, platform=platform, service=service,
                                              link_type=link_type,
                                              order=active_order, link=active_order.link, ext_order_id=ext_order_id,
                                              spent=charged,
                                              extras="qty={}".format(qty))
    service_task.pre_complete_minutes = service.pre_complete_minutes
    service_task.save()

    return {"result": "Existing the order {}, new service task '{}', interval: {}".format(active_order.id,
                                                                                          service.service_type.name,
                                                                                          service_task.pre_complete_minutes)}
