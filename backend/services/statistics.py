from backend.models.packet_log import PacketLog


def get_packet_statistics():

    total_packets = PacketLog.query.count()

    tcp = PacketLog.query.filter_by(protocol="TCP").count()
    udp = PacketLog.query.filter_by(protocol="UDP").count()
    mqtt = PacketLog.query.filter_by(protocol="MQTT").count()
    http = PacketLog.query.filter_by(protocol="HTTP").count()

    return {
        "total_packets": total_packets,
        "tcp": tcp,
        "udp": udp,
        "mqtt": mqtt,
        "http": http
    }