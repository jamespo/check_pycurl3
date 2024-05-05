#!/bin/env python3

from check_pycurl3 import CheckPyCurl, CheckPyCurlOptions
import logging
import threading
import unittest
import flask
import flask.cli
from time import sleep


class TestCheckPyCurl3(unittest.TestCase):

	@classmethod
	def setUpClass(self):
		self.app = flask.Flask(__name__)
		# make flask quiet
		logging.getLogger('werkzeug').disabled = True
		flask.cli.show_server_banner = lambda *args: None
		self.host = '127.0.0.1'
		self.port = 17171
		self.flask = threading.Thread(target=lambda: self.app.run(host=self.host, port=self.port,
																  debug=False, use_reloader=False),
									  daemon=True)
		self.flask.start()
		# give flask thread a chance to start
		sleep(1)

		@self.app.route('/')
		def root_url():
			return 'Hello, World!'


	def test_simple_check_pycurl3_200(self):
		cp_options = CheckPyCurlOptions()
		cp_options.url = 'http://%s:%s' % (self.host, self.port)
		cpc = CheckPyCurl(cp_options)
		rc = cpc.curl()
		self.assertEqual(rc, 0)
		self.assertEqual(cpc.results['status'],
						 '%s returned HTTP 200' % cp_options.url)

	def test_simple_check_pycurl3_404(self):
		cp_options = CheckPyCurlOptions()
		cp_options.url = 'http://%s:%s/absent' % (self.host, self.port)
		cpc = CheckPyCurl(cp_options)
		rc = cpc.curl()
		self.assertEqual(rc, 2)
		self.assertEqual(cpc.results['status'],
						 '%s returned HTTP 404' % cp_options.url)


if __name__ == '__main__':
    unittest.main()
