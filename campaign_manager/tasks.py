import logging
import random

from celery import shared_task

from boostress.utils import time_difference_min, get_order_amount, get_num_times, get_interval
from campaign_manager.models import Order, Status, ServiceTask, Provider, ProviderPlatform, LinkType, PlatformService
from provider_api.api import ProviderApi


@shared_task(bind=True)
def process_order(self, order_id):

    active_order = Order.objects.get(pk=int(order_id))
    platform = active_order.platform
    link_type = active_order.link_type
    link = active_order.link

    if active_order.status == Status.COMPLETED:
        logging.error("Order {} is complete, please pause the task {}".format(active_order.id, self.request.id))
        return

    available_providers = PlatformService.objects.get_providers_by_platform(platform, link_type)

    # All providers which potentially provide the related services
    potential_providers = []

    for provider in available_providers:

        available_services = provider.get_available_services(platform, link_type)

        if available_services:
            ProviderApi.update_task_statuses(provider, provider.get_active_tasks())
            busy_services = provider.get_busy_services(platform, link_type, link)
            difference = [item for item in available_services if item not in busy_services]
            if difference:
                potential_providers.append((provider, random.choice(difference)))

    if not potential_providers:
        logging.error("Existing the order {}, task {}, all providers are loaded".format(active_order.id, self.request.id))
        return

    # Add a task
    provider, service_type_name = random.choice(potential_providers)

    service = PlatformService.objects.filter(provider=provider, platform=platform, service_type__name=service_type_name,
                                             link_type=link_type).order_by('?').first()

    time_diff_min = time_difference_min(active_order.created)

    qty = get_order_amount(service.min, service.max, time_diff_min)
    runs = get_num_times(qty, service.comfort_value)
    interval = get_interval(service.comfort_interval, time_diff_min)

    ext_order_id, charged = ProviderApi.create_order(provider, service, active_order.link, qty, runs, interval)

    active_order.spent += charged

    if abs(active_order.spent - active_order.budget) < 0.1:
        active_order.status = Status.COMPLETED

    active_order.save()

    ServiceTask.objects.create(provider=provider, platform=platform, service=service, link_type=link_type,
                               order=active_order, link=active_order.link, ext_order_id=ext_order_id, spent=charged,
                               extras="qty={},runs={},interval={}".format(qty, runs, interval))
