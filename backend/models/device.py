from backend.database import db


class Device(db.Model):

    __tablename__ = "device_profiles"

    device_id = db.Column(db.Integer, primary_key=True)

    device_name = db.Column(db.String(100), nullable=False)

    device_type = db.Column(db.String(50), nullable=False)

    ip_address = db.Column(db.String(45), unique=True, nullable=False)

    mac_address = db.Column(db.String(30), unique=True, nullable=False)

    mean_interval = db.Column(db.Float, default=0)

    std_interval = db.Column(db.Float, default=0)

    rhythm_score = db.Column(db.Float, default=0)

    neighbor_fingerprint = db.Column(db.Text)

    trust_score = db.Column(db.Float, default=100)

    learning_status = db.Column(db.Boolean, default=False)