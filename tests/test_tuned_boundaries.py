import unittest

from backend.services.adaptive_detector import classify_interval


class TunedThresholdBoundaryTests(unittest.TestCase):

    def test_fixed_threshold_exact(self):
        result = classify_interval(2.0, 0.2, 2.6, 1.0, 1.0)
        self.assertFalse(result["anomaly"])

    def test_adaptive_threshold_exact(self):
        result = classify_interval(2.0, 0.2, 2.65, 1.5, 1.0)
        self.assertAlmostEqual(result["adaptive_threshold"], 3.25)
        self.assertFalse(result["anomaly"])

    def test_just_above_adaptive_threshold(self):
        result = classify_interval(2.0, 0.2, 2.652, 1.5, 1.0)
        self.assertTrue(result["anomaly"])

    def test_maximum_threshold(self):
        result = classify_interval(2.0, 0.2, 2.7, 5.0, 1.0)
        self.assertAlmostEqual(result["adaptive_threshold"], 3.5)
        self.assertFalse(result["anomaly"])

    def test_just_above_maximum_threshold(self):
        result = classify_interval(2.0, 0.2, 2.702, 5.0, 1.0)
        self.assertTrue(result["anomaly"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
