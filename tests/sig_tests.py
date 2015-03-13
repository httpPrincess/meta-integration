import hashlib
import hmac
import os
import unittest
from server.run import verify_signature
from collections import namedtuple


class SigTests(unittest.TestCase):
    def setUp(self):
        self.secret = 'abc'
        request = namedtuple('Request', ['headers', 'data'])
        with open('./example-hook-content.json') as f:
            request.data = f.read()

        mac = hmac.new(self.secret,
                       msg=request.data,
                       digestmod=hashlib.sha1)
        request.headers = {'X-Hub-Signature': 'sha1=%s' % mac.hexdigest()}
        self.gihub_request = request

    def tearDown(self):
        pass

    def test_verification(self):
        os.environ['GITHUB_SECRET'] = 'foo'
        result = verify_signature(self.gihub_request)
        self.assertFalse(result)

        os.environ['GITHUB_SECRET'] = self.secret
        result = verify_signature(self.gihub_request)
        self.assertTrue(result)