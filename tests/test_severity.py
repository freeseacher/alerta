
import unittest

try:
    import simplejson as json
except ImportError:
    import json

from uuid import uuid4
from alerta.app import app


class SeverityTestCase(unittest.TestCase):

    def setUp(self):

        app.config['TESTING'] = True
        app.config['AUTH_REQUIRED'] = False
        self.app = app.test_client()

        self.auth_alert = {
            'event': 'node_pwned',
            'resource': 'node1',
            'environment': 'Production',
            'service': ['Network'],
            'severity': 'security',
            'correlate': ['node_trace', 'node_down', 'node_marginal', 'node_up', 'node_pwned'],
            'tags': ['foo'],
            'attributes': {'foo': 'abc def', 'bar': 1234, 'baz': False}
        }
        self.critical_alert = {
            'event': 'node_down',
            'resource': 'node1',
            'environment': 'Production',
            'service': ['Network'],
            'severity': 'critical',
            'correlate': ['node_trace', 'node_down', 'node_marginal', 'node_up', 'node_pwned']
        }
        self.major_alert = {
            'event': 'node_marginal',
            'resource': 'node1',
            'environment': 'Production',
            'service': ['Network'],
            'severity': 'major',
            'correlate': ['node_trace', 'node_down', 'node_marginal', 'node_up', 'node_pwned']
        }
        self.warn_alert = {
            'event': 'node_marginal',
            'resource': 'node1',
            'environment': 'Production',
            'service': ['Network'],
            'severity': 'warning',
            'correlate': ['node_trace', 'node_down', 'node_marginal', 'node_up', 'node_pwned']
        }
        self.normal_alert = {
            'event': 'node_up',
            'resource': 'node1',
            'environment': 'Production',
            'service': ['Network'],
            'severity': 'normal',
            'correlate': ['node_trace', 'node_down', 'node_marginal', 'node_up', 'node_pwned']
        }

        self.trace_alert = {
            'event': 'node_trace',
            'resource': 'node1',
            'environment': 'Production',
            'service': ['Network'],
            'severity': 'trace',
            'correlate': ['node_trace', 'node_down', 'node_marginal', 'node_up', 'node_pwned']
        }

        self.ok_alert = {
            'event': 'node_ok',
            'resource': 'node2',
            'environment': 'Production',
            'service': ['Network'],
            'severity': 'ok',
            'correlate': []
        }

        self.inform_alert = {
            'event': 'node_inform',
            'resource': 'node3',
            'environment': 'Production',
            'service': ['Network'],
            'severity': 'informational',
            'correlate': []
        }

        self.headers = {
            'Content-type': 'application/json'
        }

    def tearDown(self):

        pass

    def test_inactive(self):

        # prevSev=unknown, sev=ok, status=closed, trend=noChange
        response = self.app.post('/alert', data=json.dumps(self.ok_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 0)
        self.assertEqual(data['alert']['repeat'], False)
        self.assertEqual(data['alert']['previousSeverity'], 'unknown')
        self.assertEqual(data['alert']['severity'], 'ok')
        self.assertEqual(data['alert']['status'], 'closed')
        self.assertEqual(data['alert']['trendIndication'], 'noChange')

        # prevSev=unknown, sev=informational, status=unknown, trend=lessSevere
        response = self.app.post('/alert', data=json.dumps(self.inform_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 0)
        self.assertEqual(data['alert']['repeat'], False)
        self.assertEqual(data['alert']['previousSeverity'], 'unknown')
        self.assertEqual(data['alert']['severity'], 'informational')
        self.assertEqual(data['alert']['status'], 'unknown')
        self.assertEqual(data['alert']['trendIndication'], 'lessSevere')

    def test_active(self):

        # prevSev=unknown, sev=major, status=open, trend=moreSevere
        response = self.app.post('/alert', data=json.dumps(self.major_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 0)
        self.assertEqual(data['alert']['repeat'], False)
        self.assertEqual(data['alert']['previousSeverity'], 'unknown')
        self.assertEqual(data['alert']['severity'], 'major')
        self.assertEqual(data['alert']['status'], 'open')
        self.assertEqual(data['alert']['trendIndication'], 'moreSevere')

        alert_id = data['id']

        # ack alert
        response = self.app.post('/alert/' + alert_id + '/status', data=json.dumps({'status': 'ack'}), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = self.app.get('/alert/' + alert_id)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['status'], 'ack')

        # prevSev=unknown, sev=major, status=(current=ack), trend=moreSevere
        response = self.app.post('/alert', data=json.dumps(self.major_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 1)
        self.assertEqual(data['alert']['repeat'], True)
        self.assertEqual(data['alert']['previousSeverity'], 'unknown')
        self.assertEqual(data['alert']['severity'], 'major')
        self.assertEqual(data['alert']['status'], 'ack')
        self.assertEqual(data['alert']['trendIndication'], 'moreSevere')

        # prevSev=major, sev=critical, status=open, trend=moreSevere
        response = self.app.post('/alert', data=json.dumps(self.critical_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 0)
        self.assertEqual(data['alert']['repeat'], False)
        self.assertEqual(data['alert']['previousSeverity'], 'major')
        self.assertEqual(data['alert']['severity'], 'critical')
        self.assertEqual(data['alert']['status'], 'open')
        self.assertEqual(data['alert']['trendIndication'], 'moreSevere')

        # prevSev=major, sev=critical, status=(current=open), trend=noChange
        response = self.app.post('/alert', data=json.dumps(self.critical_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 1)
        self.assertEqual(data['alert']['repeat'], True)
        self.assertEqual(data['alert']['previousSeverity'], 'major')
        self.assertEqual(data['alert']['severity'], 'critical')
        self.assertEqual(data['alert']['status'], 'open')
        self.assertEqual(data['alert']['trendIndication'], 'moreSevere')

        # ack alert
        response = self.app.post('/alert/' + alert_id + '/status', data=json.dumps({'status': 'ack'}), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = self.app.get('/alert/' + alert_id)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['status'], 'ack')

        # prevSev=critical, sev=warning, status=(current=ack), trend=lessSevere
        response = self.app.post('/alert', data=json.dumps(self.warn_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 0)
        self.assertEqual(data['alert']['repeat'], False)
        self.assertEqual(data['alert']['previousSeverity'], 'critical')
        self.assertEqual(data['alert']['severity'], 'warning')
        self.assertEqual(data['alert']['status'], 'ack')
        self.assertEqual(data['alert']['trendIndication'], 'lessSevere')

        # prevSev=warning, sev=normal, status=closed, trend=lessSevere
        response = self.app.post('/alert', data=json.dumps(self.normal_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 0)
        self.assertEqual(data['alert']['repeat'], False)
        self.assertEqual(data['alert']['previousSeverity'], 'warning')
        self.assertEqual(data['alert']['severity'], 'normal')
        self.assertEqual(data['alert']['status'], 'closed')
        self.assertEqual(data['alert']['trendIndication'], 'lessSevere')

        # prevSev=warning, sev=normal, status=closed, trend=noChange
        response = self.app.post('/alert', data=json.dumps(self.normal_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 1)
        self.assertEqual(data['alert']['repeat'], True)
        self.assertEqual(data['alert']['previousSeverity'], 'warning')
        self.assertEqual(data['alert']['severity'], 'normal')
        self.assertEqual(data['alert']['status'], 'closed')
        self.assertEqual(data['alert']['trendIndication'], 'lessSevere')

        # prevSev=normal, sev=trace, status=closed, trend=lessSevere
        response = self.app.post('/alert', data=json.dumps(self.trace_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 0)
        self.assertEqual(data['alert']['repeat'], False)
        self.assertEqual(data['alert']['previousSeverity'], 'normal')
        self.assertEqual(data['alert']['severity'], 'trace')
        self.assertEqual(data['alert']['status'], 'closed')
        self.assertEqual(data['alert']['trendIndication'], 'lessSevere')

        # prevSev=trace, sev=security, status=open, trend=moreSevere
        response = self.app.post('/alert', data=json.dumps(self.auth_alert), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['alert']['duplicateCount'], 0)
        self.assertEqual(data['alert']['repeat'], False)
        self.assertEqual(data['alert']['previousSeverity'], 'trace')
        self.assertEqual(data['alert']['severity'], 'security')
        self.assertEqual(data['alert']['status'], 'open')
        self.assertEqual(data['alert']['trendIndication'], 'moreSevere')
