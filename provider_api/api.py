import logging
import time

import requests

from campaign_manager.models import Provider, ServiceTask, Status, PlatformService


class ProviderApi:
    @staticmethod
    def update_task_statuses(provider: Provider, orders_list: str):
        if not orders_list:
            return
        r = requests.post(provider.api_url, json={"key": provider.key,
                                                  "action": "status",
                                                  "orders": orders_list
                                                  })
        actual_statuses = r.json()
        for order_id in actual_statuses:
            task = ServiceTask.objects.filter(ext_order_id=order_id).first()
            task.status = Status(actual_statuses[order_id]['status'])
            task.save()

    @staticmethod
    def create_order(provider: Provider, service: PlatformService, link, qty=1, runs=0, interval=0):

        packet = {"key": provider.key,
                  "action": "add",
                  "service": service.service_id,
                  "link": link,
                  "quantity": qty,
                  }

        if runs > 0:
            extras = {
                "runs": runs,
                "interval": interval
            }
            packet = packet | extras

        # TODO: Rework to Celery chain
        time.sleep(5)

        r = requests.post(provider.api_url, json=packet)
        order_response = r.json()

        if "error" in order_response:
            logging.error("Provider: {0}, Error happened: {1}".format(provider.name, order_response["error"]))
            raise Exception(order_response["error"])

        # TODO: Rework to Celery chain
        time.sleep(5)

        r = requests.post(provider.api_url, json={"key": provider.key,
                                                  "action": "status",
                                                  "order": order_response["order"]
                                                  })
        order_status = r.json()

        if "error" in order_status:
            logging.error("Provider: {0}, Error happened: {1}".format(provider.name, order_status["error"]))
            raise Exception(order_response["error"])

        return order_response["order"], float(order_status["charge"])
