import logging
import time
from datetime import timedelta

import requests
from django.utils import timezone

from campaign_manager.models import Provider, ServiceTask, Status, PlatformService
from provider_api.abstract import ProviderAPIInterface


class ProviderB11DApi(ProviderAPIInterface):
    @classmethod
    def update_task_statuses(cls, provider: Provider, orders_list: str):
        if not orders_list:
            return
        r = requests.post(provider.api_url, json={"key": provider.key,
                                                  "action": "status",
                                                  "orders": orders_list
                                                  })
        actual_statuses = r.json()
        for order_id in actual_statuses:
            new_status = Status(actual_statuses[order_id]['status'])

            # scope to the current provider to avoid duplicate ext_order_id across providers
            qs = ServiceTask.objects.filter(provider=provider, ext_order_id=order_id)

            if not qs.exists():
                continue  # nothing to update

            # apply PRE_COMPLETE window logic for completed tasks
            if new_status == Status.COMPLETED:
                now = timezone.now()
                pre_complete_minutes = qs.first().pre_complete_minutes
                if now < qs.first().created + timedelta(minutes=pre_complete_minutes):
                    new_status = Status.PRE_COMPLETE

            qs.update(status=new_status)

    @classmethod
    def create_order(cls, provider: Provider, service: PlatformService, link, qty=1):

        packet = {"key": provider.key,
                  "action": "add",
                  "service": service.service_id,
                  "link": link,
                  "quantity": qty,
                  }

        r = requests.post(provider.api_url, json=packet)
        order_response = r.json()

        if "order" not in order_response:
            logging.error("Provider: {0}, Error happened: {1}".format(provider.name, order_response))
            raise Exception(order_response)

        # TODO: Rework to Celery chain
        time.sleep(5)

        r = requests.post(provider.api_url, json={"key": provider.key,
                                                  "action": "status",
                                                  "order": order_response["order"]
                                                  })
        order_status = r.json()

        if "status" not in order_status:
            raise Exception(order_response)

        return order_response["order"], float(order_status["charge"])
