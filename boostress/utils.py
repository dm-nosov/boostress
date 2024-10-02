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
    return max(1 - minutes_passed / (60 * 18), 0)


def time_based_probability(minutes_from_start):
    # Convert minutes to hours
    hours = minutes_from_start / 60

    # Calculate probability: starts at 1 and halves every hour
    # Using 2^(-hours) to halve the probability every hour
    current_probability = math.pow(2, -hours)

    # Return 1 with current_probability, 0 otherwise
    return 1 if random.random() < current_probability else 0


def get_persistent_secret_key(file):
    if file.exists():
        with open(file, 'r') as f:
            return f.read().strip()

    # If SECRET_KEY doesn't exist, generate it and save to a file
    secret_key = get_random_secret_key()
    with open(file, 'w') as f:
        f.write(secret_key)
    return secret_key
