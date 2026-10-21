from datetime import datetime, timedelta

from backend.database import db
from backend.models.packet_log import PacketLog
from backend.models.anomaly_log import AnomalyLog


def evaluate_packet_security(
    device,
    source_ip,
    window_seconds=5,
    burst_threshold=10
):
    detections = []
    cutoff = datetime.now() - timedelta(seconds=window_seconds)

    if source_ip != device.ip_address:
        detections.append({
            "type": "identity_mismatch",
            "score": 5.0,
            "reason": (
                f"Source IP {source_ip} does not match registered "
                f"IP {device.ip_address}."
            )
        })

    recent_count = PacketLog.query.filter(
        PacketLog.device_id == device.device_id,
        PacketLog.packet_timestamp >= cutoff
    ).count()

    if recent_count >= burst_threshold:
        detections.append({
            "type": "burst_traffic",
            "score": 5.0,
            "reason": (
                f"{recent_count} packets recorded within "
                f"{window_seconds} seconds."
            )
        })

    new_logs = 0

    for detection in detections:
        existing = AnomalyLog.query.filter(
            AnomalyLog.device_id == device.device_id,
            AnomalyLog.reason == detection["reason"],
            AnomalyLog.detected_at >= cutoff
        ).first()

        if existing:
            continue

        db.session.add(AnomalyLog(
            device_id=device.device_id,
            observed_interval=0.0,
            anomaly_score=detection["score"],
            reason=detection["reason"],
            detected_at=datetime.now()
        ))

        device.trust_score = max(
            0,
            (device.trust_score if device.trust_score is not None else 100) - 10
        )
        new_logs += 1

    if new_logs:
        db.session.commit()

    return {
        "device_id": device.device_id,
        "packets_in_window": recent_count,
        "detections": detections,
        "anomaly": bool(detections),
        "new_logs_created": new_logs,
        "trust_score": device.trust_score
    }
