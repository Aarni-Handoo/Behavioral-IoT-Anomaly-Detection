
import threading
from datetime import datetime

from backend.simulator.packet_generator import generate_packet
from backend.simulator.device_generator import SMART_HOME_DEVICES
from backend.services.adaptive_detector import reference_jitter

from backend.database import db
from backend.models.device import Device
from backend.models.packet_log import PacketLog
from backend.services.anomaly_detector import detect_anomaly


# Simulator lifecycle state
_state_lock = threading.Lock()
_stop_event = threading.Event()
_threads = []
_running = False


def device_worker(app, device):
    """Generate packets while releasing database sessions each cycle."""

    while not _stop_event.is_set():
        with app.app_context():
            try:
                packet = generate_packet(device)

                db_device = Device.query.filter_by(
                    ip_address=device["ip"]
                ).first()

                if db_device is None:
                    db_device = Device(
                        device_name=device["name"],
                        device_type=device["type"],
                        ip_address=device["ip"],
                        mac_address=f"AUTO-{device['ip'].replace('.', '')}"
                    )
                    db.session.add(db_device)
                    db.session.flush()

                packet_log = PacketLog(
                    device_id=db_device.device_id,
                    packet_timestamp=datetime.now(),
                    packet_size=packet["packet_size"],
                    protocol=packet["protocol"],
                    source_ip=packet["source_ip"],
                    destination_ip=packet["destination_ip"],
                    transmission_interval=packet["interval"],
                    latency=packet["latency"],
                    jitter=packet["jitter"],
                    rssi=packet["rssi"],
                    battery_level=packet["battery"]
                )

                db.session.add(packet_log)
                db.session.commit()

                
                if db_device.learning_status:
                    historical_packets = (
                        PacketLog.query
                        .filter_by(device_id=db_device.device_id)
                        .order_by(PacketLog.packet_id.asc())
                        .limit(100)
                        .all()
                    )

                    baseline_jitter = reference_jitter(
                        [p.jitter for p in historical_packets]
                    )

                    result = detect_anomaly(
                        db_device,
                        packet["interval"],
                        observed_jitter=packet["jitter"],
                        baseline_jitter=baseline_jitter
                    )


                    if result["anomaly"]:
                        print(
                            f"ANOMALY DETECTED: "
                            f"{db_device.device_name} | "
                            f"Score: {result['score']}"
                        )

                    # Commit any trust-score or anomaly-log changes
                    # made by the detector.
                    db.session.commit()

            except Exception as exc:
                db.session.rollback()
                print(
                    f"Simulator worker error "
                    f"[{device['name']}]: {exc}"
                )

            finally:
                # Release this worker's SQLAlchemy session.
                db.session.remove()

        # Sleep without blocking a Stop Simulator request.
        if _stop_event.wait(device["interval"]):
            break


def start_simulator(app):
    """Start simulator workers unless already running."""

    global _running, _threads

    with _state_lock:
        if _running:
            return

        # Prevent overlap with previous workers that have not exited.
        if any(thread.is_alive() for thread in _threads):
            return

        _stop_event.clear()
        _running = True

        _threads = [
            threading.Thread(
                target=device_worker,
                args=(app, device),
                daemon=True,
                name=f"IoT-{device['name']}"
            )
            for device in SMART_HOME_DEVICES
        ]

        for thread in _threads:
            thread.start()


def stop_simulator():
    """Signal all simulator workers to stop."""

    global _running

    with _state_lock:
        _stop_event.set()
        _running = False
