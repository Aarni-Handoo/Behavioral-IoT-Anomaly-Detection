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
    return render_template("index.html")


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