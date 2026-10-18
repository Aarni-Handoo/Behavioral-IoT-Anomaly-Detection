from datetime import datetime

from backend.database import db
from backend.models.anomaly_log import AnomalyLog


def detect_anomaly(device, observed_interval):
    """
    Compare an observed packet interval with the device's
    learned normal behavior and store anomalies.
    """

    if not device.learning_status:
        return {
            "anomaly": False,
            "score": 0,
            "reason": "Device has not completed learning yet."
        }

    mean_interval = device.mean_interval
    std_interval = device.std_interval

    # Avoid division by zero
    if std_interval == 0:
        std_interval = 0.01

    # Calculate deviation from normal behavior
    deviation = abs(observed_interval - mean_interval)

    anomaly_score = deviation / std_interval

    # More than 3 standard deviations = suspicious
    is_anomaly = anomaly_score > 3

    reason = (
        "Interval is significantly different from normal behavior."
        if is_anomaly
        else "Behavior is within the learned normal range."
    )

    # Store anomaly in database
    if is_anomaly:
        anomaly_log = AnomalyLog(
            device_id=device.device_id,
            observed_interval=observed_interval,
            anomaly_score=round(anomaly_score, 2),
            reason=reason,
            detected_at=datetime.now()
        )

        db.session.add(anomaly_log)

         # Reduce trust when suspicious behavior is detected
        device.trust_score = max(
            0,
            device.trust_score - 10
        )

        db.session.commit()

    return {
        "anomaly": is_anomaly,
        "score": round(anomaly_score, 2),
        "reason": reason
    }


def simulate_attack(device, abnormal_interval=None):
    """
    Simulate abnormal traffic using an interval outside
    the device's learned normal behavior.
    """

    if not device.learning_status:
        return {
            "anomaly": False,
            "score": 0,
            "reason": "Device has not completed learning yet."
        }

    mean_interval = device.mean_interval or 0
    std_interval = device.std_interval or 0.01

    # Generate an interval at least 5 standard deviations
    # above the learned mean.
    simulated_interval = mean_interval + (5 * max(std_interval, 0.01))

    result = detect_anomaly(device, simulated_interval)

    return {
        **result,
        "attack_simulated": True,
        "simulated_interval": round(simulated_interval, 4),
        "message": "Simulated abnormal traffic and evaluated it using the anomaly detector."
    }
