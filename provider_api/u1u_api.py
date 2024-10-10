import json
import re

import requests

from campaign_manager.models import Provider, PlatformService
from provider_api.abstract import ProviderAPIInterface, \
    ProviderApiException


class ProviderU1UApi(ProviderAPIInterface):

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

    @classmethod
    def update_task_statuses(cls, provider: Provider, orders_list: str):
        pass

    @classmethod
    def create_order(cls, provider: Provider, service: PlatformService, link, qty=1):
        # Check if a task-related folder already exists, if not - create one

        folder_name = ProviderU1UApi._get_folder_name_by_link(link, service.service_type, service.link_type)
        folder_id = ProviderU1UApi._folder_id(provider, folder_name)

        task_info = json.loads(service.service_meta)

        if folder_id:
            task_id = ProviderU1UApi._get_task(provider, folder_id)
            ProviderU1UApi._update_task_limit(provider, task_id, qty)
        else:
            folder_id = ProviderU1UApi._create_folder(provider, folder_name)
            task_id = ProviderU1UApi._add_task(provider, folder_id, link, task_info)
            ProviderU1UApi._update_task_limit(provider, task_id, qty)

        return task_id, task_info["price"] * qty
