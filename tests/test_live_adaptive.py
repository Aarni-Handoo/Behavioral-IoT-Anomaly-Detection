import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.services.anomaly_detector import detect_anomaly


class LiveAdaptiveIntegrationTests(unittest.TestCase):

    def make_device(self):
        return SimpleNamespace(
            device_id=999,
            learning_status=True,
            mean_interval=5.0,
            std_interval=0.2,
            trust_score=100.0
        )

    def test_adaptive_prevents_fixed_alert(self):
        device = self.make_device()

        with patch(
            "backend.services.anomaly_detector.db.session"
        ) as session:
            result = detect_anomaly(
                device,
                observed_interval=5.65,
                observed_jitter=1.5,
                baseline_jitter=1.0
            )

            self.assertTrue(result["fixed_anomaly"])
            self.assertFalse(result["anomaly"])
            self.assertTrue(result["adaptive_active"])
            self.assertEqual(device.trust_score, 100.0)
            session.add.assert_not_called()
            session.commit.assert_not_called()

    def test_strong_anomaly_still_detected(self):
        device = self.make_device()

        with patch(
            "backend.services.anomaly_detector.db.session"
        ) as session:
            result = detect_anomaly(
                device,
                observed_interval=6.0,
                observed_jitter=1.5,
                baseline_jitter=1.0
            )

            self.assertTrue(result["anomaly"])
            self.assertEqual(device.trust_score, 90.0)
            session.add.assert_called_once()
            session.commit.assert_called_once()

    def test_missing_jitter_uses_fixed_threshold(self):
        device = self.make_device()

        with patch(
            "backend.services.anomaly_detector.db.session"
        ) as session:
            result = detect_anomaly(
                device,
                observed_interval=5.65
            )

            self.assertTrue(result["fixed_anomaly"])
            self.assertTrue(result["anomaly"])
            self.assertFalse(result["adaptive_active"])
            self.assertEqual(device.trust_score, 90.0)
            session.add.assert_called_once()
            session.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
