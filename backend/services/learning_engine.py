from statistics import mean, stdev

from backend.models.device import Device
from backend.models.packet_log import PacketLog
from backend.database import db


MIN_PACKETS_REQUIRED = 5


def learn_device_behavior(device):
    packets = (
        PacketLog.query
        .filter_by(device_id=device.device_id)
        .order_by(PacketLog.packet_id.asc())
        .all()
    )

    intervals = [
        packet.transmission_interval
        for packet in packets
        if packet.transmission_interval is not None
    ]

    if len(intervals) < MIN_PACKETS_REQUIRED:
        return False

    # Calculate average communication interval
    device.mean_interval = mean(intervals)

    # Calculate natural variation in communication interval
    if len(intervals) > 1:
        device.std_interval = stdev(intervals)
    else:
        device.std_interval = 0

    # Higher score = more consistent communication rhythm
    if device.mean_interval > 0:
        variation_ratio = device.std_interval / device.mean_interval
        device.rhythm_score = max(
            0,
            100 * (1 - variation_ratio)
        )
    else:
        device.rhythm_score = 0

    # Mark device as learned
    device.learning_status = True

    db.session.commit()

    return True


def learn_all_devices():
    devices = Device.query.all()

    learned = 0

    for device in devices:
        if learn_device_behavior(device):
            learned += 1

    return learned