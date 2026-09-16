from backend.simulator.device_generator import SMART_HOME_DEVICES
from backend.simulator.packet_generator import generate_packet


def simulate():

    packets = []

    for device in SMART_HOME_DEVICES:

        packet = generate_packet(device)

        packets.append(packet)

    return packets