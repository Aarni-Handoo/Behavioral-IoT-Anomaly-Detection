from backend.database import db


class AnomalyLog(db.Model):
    __tablename__ = "anomaly_logs"

    anomaly_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    device_id = db.Column(
        db.Integer,
        db.ForeignKey("device_profiles.device_id"),
        nullable=False
    )

    observed_interval = db.Column(db.Float)
    anomaly_score = db.Column(db.Float)
    reason = db.Column(db.Text)
    detected_at = db.Column(db.DateTime)