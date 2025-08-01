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
    b = 0.8
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


# ------------------------------------------------------------------
# Curve-shaping constants – change these three to fine-tune the shape
# ------------------------------------------------------------------
DECAY_MIN       = 0.018   # per-minute exponential decay
DECAY_HOUR      = 0.70    # extra decay that grows with hour_index²
VARIABILITY_P   = 0.10    # multiplicative noise ±10 %  (0.15 => ±15 %, …)
# ------------------------------------------------------------------


def get_qty(time_diff_min: int,
            total_followers: int,
            service_min: int,
            service_max: int,
            engagement_min: int,
            engagement_max: int,
            is_natural_time_cycles: bool) -> int:
    """
    Continuous, branch-free quantity generator.

    • Every call MAY return a positive value; no hard 0/1 gate is used.
    • One single exponential term makes the curve drop to ~0 after hour-4.
    • A second exponential term that depends on hour_index² separates
      hour-2, hour-3 and hour-4 clearly.
    • A ±VARIABILITY_P multiplicative noise gives additional randomness.
    """

    # ----- raw “would-be” followers touched by this minute ----------
    share_pct = random.randint(engagement_min, engagement_max)        # %
    affected  = total_followers * share_pct / 100                     # float

    # ----- optional natural engagement cycle -----------------------
    if is_natural_time_cycles:
        current_hour   = timezone.now().hour          # 0-23
        hours_from_peak = (current_hour - 18) % 24     # peak assumed at 18:00
        affected *= engagement_by_hour(hours_from_peak)

    # ----- combined exponential decay ------------------------------
    hour_idx = time_diff_min // 60                    # 0,1,2,3,4,5
    decay_factor = (
        math.exp(-DECAY_MIN  * time_diff_min) *
        math.exp(-DECAY_HOUR * hour_idx * hour_idx)
    )

    qty = service_min + (min(affected, service_max) - service_min) * decay_factor

    # ----- multiplicative noise ±VARIABILITY_P ---------------------
    noise = random.uniform(1 - VARIABILITY_P, 1 + VARIABILITY_P)
    qty = round(qty * noise)

    # ----- enforce business caps -----------------------------------
    if qty < service_min:
        return 0
    return min(qty, service_max)
