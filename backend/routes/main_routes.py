from flask import Blueprint, render_template, request, redirect
from backend.models.packet_log import PacketLog
from backend.database import db
from backend.models.device import Device
from flask import current_app
from backend.services.statistics import get_packet_statistics
from backend.simulator.traffic_generator import (
    start_simulator,
    stop_simulator
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    from backend.models.anomaly_log import AnomalyLog

    devices = Device.query.order_by(Device.device_id.desc()).all()

    total_devices = Device.query.count()
    total_packets = PacketLog.query.count()
    total_anomalies = AnomalyLog.query.count()

    recent_anomalies = (
        AnomalyLog.query
        .order_by(AnomalyLog.detected_at.desc())
        .limit(5)
        .all()
    )

    recent_packets = (
        PacketLog.query
        .order_by(PacketLog.packet_timestamp.desc())
        .limit(5)
        .all()
    )

    stats = get_packet_statistics()

    return render_template(
        "index.html",
        devices=devices,
        total_devices=total_devices,
        total_packets=total_packets,
        total_anomalies=total_anomalies,
        recent_anomalies=recent_anomalies,
        recent_packets=recent_packets,
        stats=stats
    )


@main_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        device = Device(
            device_name=request.form["device_name"],
            device_type=request.form["device_type"],
            ip_address=request.form["ip_address"],
            mac_address=request.form["mac_address"]
        )

        db.session.add(device)
        db.session.commit()

        return redirect("/devices")

    # THIS MUST BE INSIDE register(), BUT OUTSIDE THE if BLOCK
    return render_template("register_device.html")


@main_bp.route("/devices")
def devices():

    all_devices = Device.query.all()

    return render_template(
        "devices.html",
        devices=all_devices
    )

@main_bp.route("/start-simulator")
def start():

    start_simulator(current_app._get_current_object())

    return "IoT Simulator Started Successfully!"


@main_bp.route("/stop-simulator")
def stop():

    stop_simulator()

    return "IoT Simulator Stopped Successfully!"

@main_bp.route("/packets")
def packets():

    packet_logs = (
        PacketLog.query
        .order_by(PacketLog.packet_timestamp.desc())
        .limit(100)
        .all()
    )

    return render_template(
        "packets.html",
        packets=packet_logs
    )

@main_bp.route("/statistics")
def statistics():

    return get_packet_statistics()

@main_bp.route("/learn")
def learn():
    from backend.services.learning_engine import learn_all_devices

    learned = learn_all_devices()

    return {
        "message": "Behavioral learning completed",
        "devices_learned": learned
    }

@main_bp.route("/test-anomaly/<int:device_id>/<float:interval>")
def test_anomaly(device_id, interval):

    from backend.services.anomaly_detector import detect_anomaly

    device = Device.query.get(device_id)

    if device is None:
        return {
            "error": "Device not found"
        }, 404

    result = detect_anomaly(device, interval)

    return {
        "device": device.device_name,
        "observed_interval": interval,
        **result
    }

@main_bp.route("/simulate-attack/<int:device_id>/<float:interval>")
def simulate_attack_route(device_id, interval):

    from backend.services.anomaly_detector import simulate_attack

    device = Device.query.get(device_id)

    if device is None:
        return {
            "error": "Device not found"
        }, 404

    result = simulate_attack(device, interval)

    return {
        "device": device.device_name,
        "observed_interval": interval,
        **result
    }

@main_bp.route("/anomalies")
def anomalies():

    from backend.models.anomaly_log import AnomalyLog

    all_anomalies = (
        AnomalyLog.query
        .order_by(AnomalyLog.detected_at.desc())
        .all()
    )

    return {
        "total_anomalies": len(all_anomalies),
        "anomalies": [
            {
                "anomaly_id": anomaly.anomaly_id,
                "device_id": anomaly.device_id,
                "observed_interval": anomaly.observed_interval,
                "anomaly_score": anomaly.anomaly_score,
                "reason": anomaly.reason,
                "detected_at": anomaly.detected_at.isoformat()
            }
            for anomaly in all_anomalies
        ]
    }