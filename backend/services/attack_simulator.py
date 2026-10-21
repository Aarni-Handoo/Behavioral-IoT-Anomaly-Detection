from datetime import datetime
import random

from backend.database import db
from backend.models.packet_log import PacketLog
from backend.models.anomaly_log import AnomalyLog


def _record_attack(device, observed_interval, score, reason):
    anomaly = AnomalyLog(
        device_id=device.device_id,
        observed_interval=observed_interval,
        anomaly_score=round(score, 2),
        reason=reason,
        detected_at=datetime.now()
    )

    device.trust_score = max(
        0,
        (device.trust_score if device.trust_score is not None else 100) - 10
    )

    db.session.add(anomaly)


def simulate_burst_attack(device, packet_count=10):
    normal_interval = max(float(device.mean_interval or 1.0), 0.01)
    burst_interval = max(normal_interval * 0.1, 0.01)

    std_interval = max(float(device.std_interval or 0.01), 0.01)
    score = abs(normal_interval - burst_interval) / std_interval

    reason = (
        f"Simulated burst traffic: {packet_count} packets "
        f"generated with unusually short intervals."
    )

    try:
        for _ in range(packet_count):
            packet = PacketLog(
                device_id=device.device_id,
                packet_timestamp=datetime.now(),
                packet_size=random.randint(64, 1500),
                protocol=random.choice(["TCP", "UDP", "MQTT", "HTTP"]),
                source_ip=device.ip_address,
                destination_ip="192.168.1.1",
                transmission_interval=burst_interval,
                latency=round(random.uniform(5, 30), 2),
                jitter=round(random.uniform(0.1, 2), 2),
                rssi=round(random.uniform(-70, -30), 2),
                battery_level=round(random.uniform(20, 100), 2)
            )
            db.session.add(packet)

        _record_attack(device, burst_interval, score, reason)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return {
        "attack_simulated": True,
        "attack_type": "burst_traffic",
        "anomaly": True,
        "packets_generated": packet_count,
        "simulated_interval": round(burst_interval, 4),
        "score": round(score, 2),
        "reason": reason,
        "trust_score": device.trust_score
    }


def simulate_identity_mismatch(device):
    registered_ip = device.ip_address
    simulated_ip = "192.168.1.250"

    if simulated_ip == registered_ip:
        simulated_ip = "192.168.1.251"

    observed_interval = float(device.mean_interval or 1.0)
    reason = (
        f"Simulated device identity mismatch: packet source IP "
        f"{simulated_ip} does not match registered IP {registered_ip}."
    )

    try:
        packet = PacketLog(
            device_id=device.device_id,
            packet_timestamp=datetime.now(),
            packet_size=random.randint(64, 1500),
            protocol=random.choice(["TCP", "UDP", "MQTT", "HTTP"]),
            source_ip=simulated_ip,
            destination_ip="192.168.1.1",
            transmission_interval=observed_interval,
            latency=round(random.uniform(5, 30), 2),
            jitter=round(random.uniform(0.1, 2), 2),
            rssi=round(random.uniform(-70, -30), 2),
            battery_level=round(random.uniform(20, 100), 2)
        )

        db.session.add(packet)
        _record_attack(device, observed_interval, 5.0, reason)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return {
        "attack_simulated": True,
        "attack_type": "identity_mismatch",
        "anomaly": True,
        "registered_ip": registered_ip,
        "simulated_source_ip": simulated_ip,
        "reason": reason,
        "trust_score": device.trust_score
    }
