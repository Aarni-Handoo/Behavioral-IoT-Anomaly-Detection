from flask import Blueprint, render_template, request, redirect, url_for, flash
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
    flash("IoT Simulator started successfully!", "success")
    return redirect(url_for("main.home"))


@main_bp.route("/stop-simulator")
def stop():
    stop_simulator()
    flash("IoT Simulator stopped successfully!", "success")
    return redirect(url_for("main.home"))


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

    flash(
        f"Behavioral learning completed! Devices learned: {learned}",
        "success"
    )

    return redirect(url_for("main.home"))


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

    
@main_bp.route("/simulate-burst/<int:device_id>")
def simulate_burst(device_id):
    from backend.services.attack_simulator import simulate_burst_attack

    device = Device.query.get(device_id)

    if device is None:
        return {"error": "Device not found"}, 404

    result = simulate_burst_attack(device)

    return {
        "device": device.device_name,
        **result
    }


@main_bp.route("/simulate-identity-mismatch/<int:device_id>")
def simulate_identity_mismatch_route(device_id):
    from backend.services.attack_simulator import simulate_identity_mismatch

    device = Device.query.get(device_id)

    if device is None:
        return {"error": "Device not found"}, 404

    result = simulate_identity_mismatch(device)

    return {
        "device": device.device_name,
        **result
    }


@main_bp.route("/evaluate-security/<int:device_id>/<path:source_ip>")
def evaluate_security(device_id, source_ip):
    from backend.services.security_detector import evaluate_packet_security

    device = Device.query.get(device_id)

    if device is None:
        return {"error": "Device not found"}, 404

    result = evaluate_packet_security(device, source_ip)

    return {
        "device": device.device_name,
        **result
    }


@main_bp.route("/adaptive-lab")
def adaptive_lab():
    """Read-only visual comparison; no anomaly records or trust score changes."""
    from backend.services.adaptive_detector import classify_interval, reference_jitter
    device_list = Device.query.order_by(Device.device_name).all()
    selected_id = request.args.get("device_id", type=int)
    device = db.session.get(Device, selected_id) if selected_id is not None else None
    result = None
    error = None
    observed = request.args.get("interval", type=float)
    jitter = request.args.get("jitter", type=float)
    if selected_id is not None and device is None:
        error = "Device not found."
    elif device is not None and (observed is not None or jitter is not None):
        if not device.learning_status:
            error = "This device has not completed learning."
        elif observed is None or jitter is None:
            error = "Enter valid numerical values for both interval and jitter."
        else:
            # Use a stable baseline from the first 100 recorded packet jitter samples.
            # This is a historical proxy and may include anomalous samples; see README.
            rows = (PacketLog.query.filter_by(device_id=device.device_id)
                    .order_by(PacketLog.packet_id.asc()).limit(100).all())
            baseline = reference_jitter([row.jitter for row in rows])
            result = classify_interval(device.mean_interval, device.std_interval,
                                       observed, jitter, baseline)
            result["baseline_jitter"] = baseline
    return render_template("adaptive_lab.html", devices=device_list, selected=device,
                           result=result, error=error, interval=observed, jitter=jitter)


@main_bp.route("/api/adaptive-evaluate/<int:device_id>")
def adaptive_evaluate(device_id):
    """Read-only JSON API. GET never persists findings or changes trust."""
    from backend.services.adaptive_detector import classify_interval, reference_jitter
    device = db.session.get(Device, device_id)
    if device is None:
        return {"error": "Device not found"}, 404
    if not device.learning_status:
        return {"error": "Device has not completed learning"}, 409
    interval = request.args.get("interval", type=float)
    jitter = request.args.get("jitter", type=float)
    if interval is None or jitter is None:
        return {"error": "interval and jitter numeric query parameters are required"}, 400
    rows = (PacketLog.query.filter_by(device_id=device_id)
            .order_by(PacketLog.packet_id.asc()).limit(100).all())
    baseline = reference_jitter([row.jitter for row in rows])
    result = classify_interval(device.mean_interval, device.std_interval, interval, jitter, baseline)
    return {"device_id": device_id, "baseline_jitter": baseline, **result}, 200 if result["ready"] else 422
