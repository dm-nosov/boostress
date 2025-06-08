import json
import re

import requests

from campaign_manager.models import Provider, PlatformService
from provider_api.abstract import ProviderAPIInterface, \
    ProviderApiException


class ProviderU1UApi(ProviderAPIInterface):

    STATUS_REQUIRES_APPROVE = "2"

    @staticmethod
    def _add_task(provider: Provider, folder_id, link, task_info) -> int:
        r = requests.post(provider.api_url, data={"api_key": provider.key, "action": "add_task", "folder_id": folder_id,
                                                  "link": link} | task_info)
        response = r.json()
        if "task_id" in response:
            return response["task_id"]
        else:
            raise ProviderApiException(
                "Error while creating a task, folder: {} (provider: {}, link: {}, task_info: {}). It is empty".format(
                    folder_id, provider.name, link, task_info))

    @staticmethod
    def _get_task(provider: Provider, folder_id) -> str:
        task_info = {
            "folder_id": folder_id,
        }
        r = requests.post(provider.api_url, data={"api_key": provider.key, "action": "get_tasks"} | task_info)

        response = r.json()
        tasks_list = response["tasks"]

        if len(tasks_list) == 0:
            raise ProviderApiException(
                "Error while searching for tasks in the folder {} (provider {}). It is empty".format(folder_id,
                                                                                                     provider.name))

        return tasks_list[0]["id"]
        # {'id': '1736676', 'name': 'Some name', 'price_rub': 1.5, 'status': 2, 'folder_id': '0', 'tarif_id': '12'}

    @staticmethod
    def _update_task_limit(provider: Provider, task_id, add_qty):
        task_info = {
            "task_id": task_id,
            "add_to_limit": add_qty
        }
        r = requests.post(provider.api_url, data={"api_key": provider.key, "action": "task_limit_add"} | task_info)
        print(r.status_code)
        print(r.json())

    @staticmethod
    def _get_folder_name_by_link(link, service_type, link_type):
        return "{}_{}_{}".format(service_type, link_type, re.sub(r"https://|/", "", link)[-15:])

    @staticmethod
    def _create_folder(provider: Provider, name):
        r = requests.post(provider.api_url, data={"api_key": provider.key,
                                                  "action": "create_folder",
                                                  "name": name
                                                  })
        response = r.json()

        if "folder_id" in response:
            return response["folder_id"]
        else:
            raise ProviderApiException("Could not create the folder: {}, provider: {}", name, provider.name)

    @staticmethod
    def _folder_id(provider: Provider, folder_name) -> int:
        r = requests.post(provider.api_url, data={"api_key": provider.key,
                                                  "action": "get_folders",
                                                  })
        folders_array = r.json()
        if "folders" not in folders_array:
            raise ProviderApiException(
                "Unable to get the folder list for the provider: {}, folder name: {}".format(provider.name,
                                                                                             folder_name))
        for folder in folders_array["folders"]:
            if folder["name"] == folder_name:
                return folder["id"]
        return 0

    @staticmethod
    def _push_task(provider: Provider, task_id: str):
        task_info = {
            "task_id": task_id,
        }
        r = requests.post(provider.api_url, data={"api_key": provider.key, "action": "task_to_top"} | task_info)
        print(r.status_code)
        print(r.json())

    @classmethod
    def update_task_statuses(cls, provider: Provider, orders_list: str):
        task_ids_list = orders_list.split(",")
        for task_id in task_ids_list:
            reports_list = cls._get_reports(provider, task_id)
            for report in reports_list:
                if report["status"] == cls.STATUS_REQUIRES_APPROVE:
                    cls._approve_report(provider, report["id"])

    @classmethod
    def create_order(cls, provider: Provider, service: PlatformService, link, qty=1):
        # Check if a task-related folder already exists, if not - create one

        folder_name = cls._get_folder_name_by_link(link, service.service_type, service.link_type)
        folder_id = cls._folder_id(provider, folder_name)

        task_info = json.loads(service.service_meta)

        # Ensure every ServiceTask created in Boostress maps to a *unique* task on the
        # provider side so that ext_order_id is not duplicated.  Even if a folder for
        # the same resource already exists we still create a *new* task instead of
        # re-using (and topping-up) the previous one.  This guarantees that
        # ServiceTask.ext_order_id stays unique per provider which prevents
        # ServiceTask.MultipleObjectsReturned errors in status-update code.

        if not folder_id:
            # First interaction with this resource – create the folder once.
            folder_id = cls._create_folder(provider, folder_name)

        # Always create a *new* task inside the folder so that we receive a new
        # provider-side task_id every time.
        task_id = cls._add_task(provider, folder_id, link, task_info)

        # Increase its limit immediately to match the requested quantity.
        cls._update_task_limit(provider, task_id, qty)

        # Optionally push the task to the top so it starts quickly.
        cls._push_task(provider, str(task_id))

        return task_id, task_info["price"] * qty

    @classmethod
    def _approve_report(cls, provider, report_id):

        report = {"report_id": report_id}

        r = requests.post(provider.api_url, data={"api_key": provider.key,
                                                  "action": "approve_report",
                                                  } | report)
        print(r.status_code)
        print(r.json())

    @classmethod
    def _get_reports(cls, provider, task_id: str) -> list[dict]:
        r = requests.post(provider.api_url, data={"api_key": provider.key,
                                                  "action": "get_reports",
                                                  })
        """
        Example:
                "reports": [{
          'id': '9764',
          'task_id': '116',
          'worker_id': '28',
          'price_rub': 2,
          'status': '6',
          'messages': [
            {
              'from_id': '12',
              'to_id': '13',
              'date': '2024-10-13 11:54:31',
              'text': 'sometext',
              'files': [
                'https://example.com/uploads/files/20241013/37il.png'
              ]
            }
          ],
          'ip': '192.168.0.1'
        }]
        """

        return r.json()["reports"]
