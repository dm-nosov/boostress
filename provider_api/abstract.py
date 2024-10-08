from abc import ABC, abstractmethod

from campaign_manager.models import Provider, PlatformService


class ProviderAPIInterface(ABC):
    @classmethod
    @abstractmethod
    def create_order(cls, provider: Provider, service: PlatformService, link, qty=1) -> (str, int):
        pass

    @classmethod
    @abstractmethod
    def update_task_statuses(cls, provider: Provider, orders_list: str) -> None:
        pass
