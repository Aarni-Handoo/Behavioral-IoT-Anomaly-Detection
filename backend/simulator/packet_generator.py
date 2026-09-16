import random
from datetime import datetime

PROTOCOLS = ["TCP", "UDP", "MQTT", "HTTP"]


def generate_packet(device):

    interval = device["interval"]

    packet = {
        "device_name": device["name"],
        "device_type": device["type"],
        "ip_address": device["ip"],
        "timestamp": datetime.now(),

        "packet_size": random.randint(64, 1500),

        "protocol": random.choice(PROTOCOLS),

        "source_ip": device["ip"],

        "destination_ip": "192.168.1.1",

        "interval": round(
            random.normalvariate(interval, interval * 0.05),
            2
        ),

        "latency": round(random.uniform(5, 30), 2),

        "jitter": round(random.uniform(0.1, 2), 2),

        "battery": round(random.uniform(20, 100), 2),

        "rssi": round(random.uniform(-70, -30), 2)
    }

    return packet