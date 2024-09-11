from enum import Enum


class APIStatus(Enum):
    COMPLETED = "Completed"
    IN_PROGRESS = "In progress"
    PENDING = "Pending"
    PARTIAL = "Partial"
    PROCESSING = "Processing"
    CANCELED = "Canceled"