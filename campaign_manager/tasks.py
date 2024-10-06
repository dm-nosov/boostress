import logging
import math
import random
import traceback
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

from boostress.utils import time_difference_min, time_decay, \
    time_based_probability
from campaign_manager.models import Order, Status, ServiceTask, Provider, PlatformService, \
    EngagementConfig
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


def get_qty(time_diff_min, total_followers, service_min, service_max, engagement_min, engagement_max):
    share = random.randint(engagement_min, engagement_max )
    affected_followers = math.floor(total_followers * share * time_decay(time_diff_min) / 100)
    if affected_followers < service_min:
        return 0

    if affected_followers == service_min and service_max - service_min < 5:
        affected_followers += random.randint(1, 5)

    if affected_followers > service_max:
        affected_followers = service_max

    if time_based_probability(time_diff_min):
        return affected_followers

    return 0


@shared_task(bind=True)
def process_order(self, order_id):
    try:
        with transaction.atomic():
            active_order = Order.objects.select_for_update().get(pk=int(order_id))
    except Order.DoesNotExist as exc:
        trace = traceback.format_exc()
        return {"result": "Order with ID: '{}', type {} was not found, traceback: {}".format(order_id, type(order_id),
                                                                                             trace)}
    platform = active_order.platform
    link_type = active_order.link_type
    link = active_order.link

    self.periodic_task_name = "Order {}".format(active_order.id, timezone.now())

    if active_order.status == Status.COMPLETED:
        active_order.tasks.update(status=Status.COMPLETED)
        return {"result": "Order {} is completed".format(active_order.id)}

    available_providers = PlatformService.objects.get_providers_by_platform(platform, link_type)

    if not available_providers:
        return {"result": "Order {}, no available providers found".format(active_order.id)}

    busy_services = ServiceTask.objects.get_busy_services(platform, link_type, link)

    potential_providers = get_potential_providers(available_providers, platform, link_type, busy_services)

    if not potential_providers:
        return {"result": "Exiting  the order {}, all providers are loaded".format(active_order.id)}

    # Add a task
    provider, service_type_name = random.choice(potential_providers)

    service = PlatformService.objects.filter(provider=provider, platform=platform, service_type__name=service_type_name,
                                             link_type=link_type, is_enabled=True).order_by('?').first()

    engagement_min, engagement_max = EngagementConfig.objects.get_config(link_type=link_type,
                                                                         service_type=service_type_name,
                                                                         platform_name=platform.name)

    time_difference = time_difference_min(active_order.created)

    if active_order.time_sensible:
        qty = get_qty(time_difference, active_order.total_followers, service.min, service.max, engagement_min,
                      engagement_max)
    else:
        qty = get_qty(0, active_order.total_followers, service.min, service.max, engagement_min,
                      engagement_max)

    if qty < service.min:
        return {
            "result": "Order {}, qty is {}, attempted the service {}, the QTY is less than {}".format(active_order.id,
                                                                                                      qty,
                                                                                                      service.service_id,
                                                                                                      service.min)}

    try:
        ext_order_id, charged = ProviderApi.create_order(provider, service, active_order.link, qty)
    except Exception as exc:
        return {"result": "Exception in provider API, order {}, service: {}, Exception: {}".format(active_order.id,
                                                                                                   service.service_id,
                                                                                                   exc)}

    active_order.spent += charged

    if active_order.budget - active_order.spent < 0.01:
        active_order.status = Status.COMPLETED

    active_order.save()

    service_task = ServiceTask.objects.create(provider=provider, platform=platform, service=service,
                                              link_type=link_type,
                                              order=active_order, link=active_order.link, ext_order_id=ext_order_id,
                                              spent=charged,
                                              extras="qty={}".format(qty),
                                              force_complete_after_min=service.force_complete_after_min,
                                              pre_complete_minutes=service.pre_complete_minutes)

    return {"result": "Existing the order {}, new service task '{}', interval: {}, QTY: {}".format(active_order.id,
                                                                                                   service.service_type.name,
                                                                                                   service_task.pre_complete_minutes,
                                                                                                   qty)}


@shared_task(bind=True)
def update_task_statuses(self):
    [provider.force_complete_tasks() for provider in Provider.objects.all()]
    [ProviderApi.update_task_statuses(provider, provider.get_active_tasks()) for provider in Provider.objects.all()]


@shared_task
def cleanup_expired_periodic_tasks():
    return PeriodicTask.objects.filter(expires__lt=timezone.now()).delete()


@shared_task(bind=True)
def update_order_statuses(self):
    active_orders = Order.objects.get_active_orders()

    completed_orders_ids = []

    for order in active_orders:
        if (timezone.now() > timedelta(
                minutes=order.deadline) + order.created):
            order.status = Status.COMPLETED
            order.save()
            order.tasks.update(status=Status.COMPLETED)
            completed_orders_ids.append(order.id)

    return {"result": "Orders {} are completed by time".format(completed_orders_ids)}
