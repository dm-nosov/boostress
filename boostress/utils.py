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
    hours_from_peak = (current_hour - 18) % 24
    # Time of day curve (centered at 18:00 UTC)
    time_factor = 1 / (1 + math.exp(0.5 * (hours_from_peak - 12)))

    # Decay curve based on minutes since creation
    decay_factor = 60 * math.exp(-minutes_since_creation / 25) + 1

    # Reduce time factor impact for very recent creations
    recency_weight = min(1, minutes_since_creation / 60)
    adjusted_time_factor = recency_weight * time_factor + (1 - recency_weight)

    # Combine factors and add randomness
    combined_factor = adjusted_time_factor * decay_factor / 61  # Normalize to [0, 1]
    random_factor = random.uniform(-0.05, 0.05)
    final_factor = max(0, min(1, combined_factor + random_factor))

    # Calculate final order amount
    order_amount = int(min_value + (max_value - min_value) * final_factor)
    if order_amount == min_value and min_value > 9 and max_value - min_value > 5:
        order_amount += random.randint(1, 5)
    return order_amount


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