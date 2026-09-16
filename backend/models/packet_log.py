from backend.database import db


class PacketLog(db.Model):

    __tablename__ = "packet_logs"

    packet_id = db.Column(db.BigInteger, primary_key=True)

    device_id = db.Column(
        db.Integer,
        db.ForeignKey("device_profiles.device_id"),
        nullable=False
    )

    packet_timestamp = db.Column(db.DateTime)

    packet_size = db.Column(db.Integer)

    protocol = db.Column(db.String(20))

    source_ip = db.Column(db.String(45))

    destination_ip = db.Column(db.String(45))

    transmission_interval = db.Column(db.Float)

    latency = db.Column(db.Float)

    jitter = db.Column(db.Float)

    rssi = db.Column(db.Float)

    battery_level = db.Column(db.Float)