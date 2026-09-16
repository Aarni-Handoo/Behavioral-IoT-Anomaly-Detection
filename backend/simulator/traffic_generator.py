import threading
import time
from datetime import datetime

from backend.simulator.packet_generator import generate_packet
from backend.simulator.device_generator import SMART_HOME_DEVICES

from backend.database import db
from backend.models.device import Device
from backend.models.packet_log import PacketLog

running = False


def device_worker(app, device):

    global running

    with app.app_context():

        while running:

            packet = generate_packet(device)

            print(packet)

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
                db.session.commit()

            if db_device:

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

            time.sleep(device["interval"])


def start_simulator(app):

    global running

    if running:
        return

    running = True

    for device in SMART_HOME_DEVICES:

        threading.Thread(
            target=device_worker,
            args=(app, device),
            daemon=True
        ).start()

def stop_simulator():

    global running

    running = False