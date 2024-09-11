import random

from django.core.management.utils import get_random_secret_key
from django.utils import timezone
from datetime import datetime
import math


def time_difference_min(initial_moment: datetime):
    now = timezone.now()
    time_difference = now - initial_moment
    difference_in_minutes = time_difference.total_seconds() / 60
    return int(difference_in_minutes)


def get_order_amount(min_value, max_value, minutes_since_creation):
    random.seed()

    current_hour = int(timezone.now().strftime('%H'))

    normalized_hour = ((current_hour - 18 + 24) % 24) / 24
    distance_from_peak = min(normalized_hour, 1 - normalized_hour) * 2
    curve_value = math.pow(1 - math.pow(distance_from_peak, 2), 3)

    random_factor = 0.15
    random_value = random.random() * random_factor - (random_factor / 2)

    final_value = max(0, min(1, curve_value + random_value))

    scaling_factor = 1 - (distance_from_peak * 0.5)
    final_value *= scaling_factor

    decay_factor = math.exp(-minutes_since_creation / 60)

    final_value *= decay_factor

    return int(math.ceil(min_value + (max_value - min_value) * final_value))


def get_num_times(amount, convenient_amount):
    if convenient_amount == 0:
        return 0
    if amount > convenient_amount:
        return math.floor(amount / convenient_amount)


def get_interval(initial_interval, difference_in_minutes):
    return initial_interval + math.floor(math.log2(1 + difference_in_minutes)) * 7 * (max(0, difference_in_minutes > 60))


def get_persistent_secret_key(file):
    if file.exists():
        with open(file, 'r') as f:
            return f.read().strip()

    # If SECRET_KEY doesn't exist, generate it and save to a file
    secret_key = get_random_secret_key()
    with open(file, 'w') as f:
        f.write(secret_key)
    return secret_key