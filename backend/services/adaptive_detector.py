"""Jitter-adaptive interval anomaly detector.

Tuned research heuristic:
    z = abs(observed_interval - mean_interval) / max(std_interval, 0.01)

    T = 3 + min(0.5, 0.5 * max(0, observed_jitter / baseline_jitter - 1))

An anomaly is reported when z > T.

The threshold ranges from 3.0 to 3.5.
This module does not write to the database.
"""

import math
from statistics import median


def classify_interval(
    mean_interval,
    std_interval,
    observed_interval,
    observed_jitter=None,
    baseline_jitter=None
):
    """Compare fixed and adaptive anomaly decisions without database writes."""

    if mean_interval is None or observed_interval is None:
        return {
            "ready": False,
            "reason": "Missing behavioral baseline or observation",
            "anomaly": False
        }

    values = (mean_interval, observed_interval)

    if any(
        not isinstance(v, (int, float))
        or not math.isfinite(v)
        or v < 0
        for v in values
    ):
        return {
            "ready": False,
            "reason": "Invalid interval value",
            "anomaly": False
        }

    if (
        std_interval is None
        or not isinstance(std_interval, (int, float))
        or not math.isfinite(std_interval)
    ):
        std_interval = 0.01

    sigma = max(float(std_interval), 0.01)

    score = round(
        abs(observed_interval - mean_interval) / sigma,
        10
    )

    fixed_threshold = 3.0
    adjusted_threshold = fixed_threshold
    jitter_ratio = None

    if (
        observed_jitter is not None
        and baseline_jitter is not None
        and all(
            isinstance(v, (int, float))
            and math.isfinite(v)
            and v >= 0
            for v in (observed_jitter, baseline_jitter)
        )
        and baseline_jitter > 0
    ):
        jitter_ratio = observed_jitter / baseline_jitter

        adjusted_threshold += min(
            0.5,
            0.5 * max(0.0, jitter_ratio - 1.0)
        )

    adjusted_threshold = round(adjusted_threshold, 10)

    return {
        "ready": True,
        "score": round(score, 2),
        "fixed_anomaly": score > fixed_threshold,
        "anomaly": score > adjusted_threshold,
        "fixed_threshold": fixed_threshold,
        "adaptive_threshold": adjusted_threshold,
        "jitter_ratio": (
            round(jitter_ratio, 3)
            if jitter_ratio is not None
            else None
        ),
        "reason": (
            "Adaptive threshold exceeded"
            if score > adjusted_threshold
            else "Within adaptive threshold"
        )
    }


def reference_jitter(packet_jitters):
    """Calculate median baseline jitter from valid historical samples."""

    values = [
        float(v)
        for v in packet_jitters
        if isinstance(v, (int, float))
        and math.isfinite(v)
        and v >= 0
    ]

    return median(values) if values else None
