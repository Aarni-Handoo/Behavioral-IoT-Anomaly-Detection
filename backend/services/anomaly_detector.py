
from datetime import datetime

from backend.database import db
from backend.models.anomaly_log import AnomalyLog
from backend.services.adaptive_detector import classify_interval


def detect_anomaly(
    device,
    observed_interval,
    observed_jitter=None,
    baseline_jitter=None
):
    """
    Evaluate an IoT device using the tuned Goal B detector.

    If jitter data is unavailable, fall back to fixed Z-score.
    Write one anomaly record and deduct trust only when flagged.
    """

    if not device.learning_status:
        return {
            "anomaly": False,
            "score": 0,
            "reason": "Device has not completed learning yet."
        }

    result = classify_interval(
        mean_interval=device.mean_interval,
        std_interval=device.std_interval,
        observed_interval=observed_interval,
        observed_jitter=observed_jitter,
        baseline_jitter=baseline_jitter
    )

    if not result["ready"]:
        return {
            "anomaly": False,
            "score": 0,
            "reason": result["reason"]
        }

    is_anomaly = result["anomaly"]
    adaptive_active = result["jitter_ratio"] is not None

    if is_anomaly:
        reason = (
            "Observed interval exceeded the adaptive behavioral threshold."
            if adaptive_active
            else "Observed interval exceeded the fixed behavioral threshold."
        )
    else:
        reason = "Behavior is within the learned threshold."

    if is_anomaly:
        anomaly_log = AnomalyLog(
            device_id=device.device_id,
            observed_interval=observed_interval,
            anomaly_score=result["score"],
            reason=reason,
            detected_at=datetime.now()
        )

        try:
            db.session.add(anomaly_log)

            current_trust = (
                device.trust_score
                if device.trust_score is not None
                else 100
            )

            device.trust_score = max(0, current_trust - 10)

            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    return {
        "anomaly": is_anomaly,
        "score": result["score"],
        "reason": reason,
        "fixed_anomaly": result["fixed_anomaly"],
        "fixed_threshold": result["fixed_threshold"],
        "adaptive_threshold": result["adaptive_threshold"],
        "jitter_ratio": result["jitter_ratio"],
        "adaptive_active": adaptive_active
    }


def simulate_attack(device, abnormal_interval=None):
    """
    Simulate an abnormal interval and use the detector.

    Without jitter parameters, the fixed Z-score fallback applies.
    """

    if not device.learning_status:
        return {
            "anomaly": False,
            "score": 0,
            "reason": "Device has not completed learning yet."
        }

    mean_interval = device.mean_interval or 0
    std_interval = device.std_interval or 0.01

    simulated_interval = (
        mean_interval + 5 * max(std_interval, 0.01)
        if abnormal_interval is None
        else abnormal_interval
    )

    result = detect_anomaly(device, simulated_interval)

    return {
        **result,
        "attack_simulated": True,
        "simulated_interval": round(simulated_interval, 4),
        "message": (
            "Simulated abnormal traffic and evaluated it "
            "using the behavioral detector."
        )
    }
