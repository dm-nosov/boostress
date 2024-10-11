from enum import Enum
from typing import Dict, Type

from campaign_manager.models import ProviderType
from provider_api.abstract import ProviderAPIInterface
from provider_api.b11d_api import ProviderB11DApi
from provider_api.u1u_api import ProviderU1UApi


class APIFactory:
    _apis: Dict[str, Type[ProviderAPIInterface]] = {}

    @classmethod
    def register_api(cls, name: str, api_class: Type[ProviderAPIInterface]):
        cls._apis[name] = api_class

    @classmethod
    def get_api(cls, name: str) -> Type[ProviderAPIInterface]:
        return cls._apis[name]


# Register APIs
APIFactory.register_api(ProviderType.B11D, ProviderB11DApi)
APIFactory.register_api(ProviderType.U1U, ProviderU1UApi)


class APIStatus(Enum):
    COMPLETED = "Completed"
    IN_PROGRESS = "In progress"
    PENDING = "Pending"
    PARTIAL = "Partial"
    PROCESSING = "Processing"
    CANCELED = "Canceled"
