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


def time_decay(minutes_passed):
    a = 0.1
    b = 0.5
    current_probability = 1 / (1 + a * (minutes_passed ** b))
    random_factor = random.uniform(-0.07, 0.07)
    return max(current_probability + random_factor, 0)


def engagement_by_hour(hour_diff_to_peak):
    return (hour_diff_to_peak + 1) / (1 + (hour_diff_to_peak + 1) * math.log2(hour_diff_to_peak + 1))


def time_based_probability(minutes_from_start):

    # Return 1 with current_probability, 0 otherwise
    return 1 if random.random() < time_decay(minutes_from_start) else 0


def get_persistent_secret_key(file):
    if file.exists():
        with open(file, 'r') as f:
            return f.read().strip()

    # If SECRET_KEY doesn't exist, generate it and save to a file
    secret_key = get_random_secret_key()
    with open(file, 'w') as f:
        f.write(secret_key)
    return secret_key
