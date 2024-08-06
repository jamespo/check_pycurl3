#!/bin/env python3

from check_pycurl3 import CheckPyCurl, CheckPyCurlOptions, get_cli_options
import logging
import threading
import unittest
import unittest.mock
import flask
import flask.cli
import sys
from time import sleep


class TestCheckPyCurl3(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.app = flask.Flask(__name__)
		# make flask quiet
		logging.getLogger('werkzeug').disabled = True
		flask.cli.show_server_banner = lambda *args: None
		cls.host = '127.0.0.1'
		cls.port = 17171
		cls.flask = threading.Thread(target=lambda: cls.app.run(host=cls.host, port=cls.port,
																  debug=False, use_reloader=False),
									  daemon=True)
		cls.flask.start()
		# give flask thread a chance to start
		sleep(1)

		@cls.app.route('/')
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

	def test_simple_check_pycurl3_content(self):
		cp_options = CheckPyCurlOptions()
		cp_options.url = 'http://%s:%s' % (self.host, self.port)
		cp_options.test = 'regex:Hello'
		cpc = CheckPyCurl(cp_options)
		rc = cpc.curl()
		self.assertEqual(rc, 0)
		self.assertEqual(cpc.results['status'],
						 'Hello found in %s' % cp_options.url)

	def test_simple_check_pycurl3_404(self):
		cp_options = CheckPyCurlOptions()
		cp_options.url = 'http://%s:%s/absent' % (self.host, self.port)
		cpc = CheckPyCurl(cp_options)
		rc = cpc.curl()
		self.assertEqual(rc, 2)
		self.assertEqual(cpc.results['status'],
						 '%s returned HTTP 404' % cp_options.url)

	def test_cli_parsing(self):
		test_url = "https://www.google.com"
		testargs = ["check_pycurl3.py", "-u", test_url]
		with unittest.mock.patch.object(sys, 'argv', testargs):
			options = get_cli_options()
			assert options.url == test_url

if __name__ == '__main__':
    unittest.main()
