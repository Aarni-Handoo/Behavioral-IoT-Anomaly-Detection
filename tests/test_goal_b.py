"""Unittest checks, using an isolated in-memory SQLite database."""
import unittest
from flask import Flask
from backend.database import db
from backend.models.device import Device
from backend.models.packet_log import PacketLog
from backend.models.anomaly_log import AnomalyLog
from backend.routes.main_routes import main_bp
from backend.services.adaptive_detector import classify_interval, reference_jitter


class DetectionUnitTests(unittest.TestCase):
    def test_exact_threshold(self):
        self.assertFalse(classify_interval(2, 0.2, 2.6)['anomaly'])
    def test_missing_baseline(self):
        self.assertFalse(classify_interval(None, 0.2, 2.6)['ready'])
    def test_normal_jitter_keeps_fixed_threshold(self):
        self.assertEqual(classify_interval(2, .2, 2.8, 1, 1)['adaptive_threshold'], 3)
    def test_higher_jitter_increases_threshold(self):
        data=classify_interval(2, .2, 2.8, 1.5, 1)
        self.assertAlmostEqual(data['adaptive_threshold'],3.25)
        self.assertTrue(data['fixed_anomaly'])
        self.assertTrue(data['anomaly'])
    def test_jitter_absent_falls_back(self):
        data=classify_interval(2,.2,2.8,None,None)
        self.assertEqual(data['adaptive_threshold'],3)
    def test_jitter_capped(self):
        self.assertEqual(classify_interval(2,.2,2.8,100,1)['adaptive_threshold'],3.5)
    def test_reject_invalid_intervals(self):
        self.assertFalse(classify_interval(2,.2,-1)['ready'])
        self.assertFalse(classify_interval(float('nan'),.2,2)['ready'])
    def test_reference_jitter(self):
        self.assertEqual(reference_jitter([None,0.4,0.8,-1,1.2]),0.8)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__,template_folder='../frontend/templates',static_folder='../frontend/static')
        app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(app)
        app.register_blueprint(main_bp)
        self.app=app
        self.ctx=app.app_context(); self.ctx.push(); db.create_all()
        db.session.add(Device(device_id=1,device_name='Sensor',device_type='Sensor',ip_address='192.0.2.1',mac_address='AA:00:00:00:00:01',mean_interval=2,std_interval=.2,learning_status=True,trust_score=90))
        for i in range(6):
            db.session.add(PacketLog(packet_id=i+1,device_id=1,jitter=1.0,transmission_interval=2,packet_size=64))
        db.session.commit()
        self.client=app.test_client()
    def tearDown(self):
        db.session.remove();db.drop_all();self.ctx.pop()
    def test_api_read_only(self):
        before=AnomalyLog.query.count()
        response=self.client.get('/api/adaptive-evaluate/1?interval=2.8&jitter=1.5')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['adaptive_threshold'],3.25)
        self.assertEqual(AnomalyLog.query.count(),before)
        self.assertEqual(db.session.get(Device,1).trust_score,90)
    def test_api_missing_inputs(self):
        self.assertEqual(self.client.get('/api/adaptive-evaluate/1?interval=2.8').status_code,400)
    def test_api_unknown_device(self):
        self.assertEqual(self.client.get('/api/adaptive-evaluate/999?interval=2&jitter=1').status_code,404)
    def test_ui_page(self):
        response=self.client.get('/adaptive-lab?device_id=1&interval=2.8&jitter=1.5')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'Adaptive Detection Lab',response.data)
    def test_home_css_link(self):
        response=self.client.get('/')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'dashboard.css',response.data)

if __name__ == '__main__':
    unittest.main()


