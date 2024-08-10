#!/bin/env python3

from check_pycurl3 import CheckPyCurl, CheckPyCurlOptions, CheckPyCurlMulti, get_cli_options
import logging
import os
import os.path
import shlex
import shutil
import subprocess
import tempfile
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
		"""create localhost http instance in thread"""
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

	def test_runfile(self):
		"""create simple runfile & test"""
		runfile = tempfile.NamedTemporaryFile(delete=False)
		runfile_contents = "---\n\nurls:\n  - url: http://%s:%s\n" % (self.host, self.port)
		runfile.write(runfile_contents.encode("utf-8"))
		runfile.close()
		cpm = CheckPyCurlMulti(runfile.name)
		cpm.parse_runfile()
		cpc = cpm.check_runfile()
		os.remove(runfile.name)
		self.assertEqual(cpc.results["rc"], 0)


	def test_simple_check_pycurl3_200(self):
		"""simple localhost 200"""
		cp_options = CheckPyCurlOptions()
		cp_options.url = 'http://%s:%s' % (self.host, self.port)
		cpc = CheckPyCurl(cp_options)
		rc = cpc.curl()
		self.assertEqual(rc, 0)
		self.assertEqual(cpc.results['status'],
						 '%s returned HTTP 200' % cp_options.url)

	def test_simple_check_pycurl3_content(self):
		"""test content of response"""
		cp_options = CheckPyCurlOptions()
		cp_options.url = 'http://%s:%s' % (self.host, self.port)
		cp_options.test = 'regex:Hello'
		cpc = CheckPyCurl(cp_options)
		rc = cpc.curl()
		self.assertEqual(rc, 0)
		self.assertEqual(cpc.results['status'],
						 'Hello found in %s' % cp_options.url)

	def test_simple_check_pycurl3_404(self):
		"""test 404"""
		cp_options = CheckPyCurlOptions()
		cp_options.url = 'http://%s:%s/absent' % (self.host, self.port)
		cpc = CheckPyCurl(cp_options)
		rc = cpc.curl()
		self.assertEqual(rc, 2)
		self.assertEqual(cpc.results['status'],
						 '%s returned HTTP 404' % cp_options.url)

	def test_cli_parsing(self):
		"""test cli arg parsing"""
		test_url = "https://www.google.com"
		testargs = ["check_pycurl3.py", "-u", test_url]
		with unittest.mock.patch.object(sys, 'argv', testargs):
			options = get_cli_options()
			assert options.url == test_url


class TestHTTPSCheckPyCurl3(unittest.TestCase):

	@classmethod
	def genSelfSigned(cls):
		'''generate self-signed cert'''
		cls.tmpdir = tempfile.mkdtemp()
		cls.cert = os.path.join(cls.tmpdir, 'flask.crt')
		cls.key = os.path.join(cls.tmpdir, 'flask.key')
		create_cert = '/bin/openssl req -x509 -newkey rsa:2048 -keyout %s -out %s -sha256 -days 2 -nodes -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=localhost"' % (cls.key, cls.cert)
		subprocess.run(shlex.split(create_cert), stdout = subprocess.DEVNULL,
					   stderr = subprocess.DEVNULL)

	@classmethod
	def setUpClass(cls):
		"""create localhost https instance in thread"""
		cls.app = flask.Flask(__name__)
		# make flask quiet
		logging.getLogger('werkzeug').disabled = True
		flask.cli.show_server_banner = lambda *args: None
		cls.genSelfSigned()
		cls.host = 'localhost'
		cls.port = 17173
		cls.flask = threading.Thread(target=lambda: cls.app.run(host=cls.host, port=cls.port,
																ssl_context=(cls.cert, cls.key),
																debug=False, use_reloader=False),
									 daemon=True)
		cls.flask.start()
		# give flask thread a chance to start
		sleep(1)

		@cls.app.route('/')
		def root_url():
			return 'Hello, World!'

	def test_https_check_pycurl3_200(self):
		cp_options = CheckPyCurlOptions()
		cp_options.url = 'https://%s:%s' % (self.host, self.port)
		cp_options.insecure = True  # self-signed
		cpc = CheckPyCurl(cp_options)
		rc = cpc.curl()
		self.assertEqual(rc, 0)
		self.assertEqual(cpc.results['status'],
						 '%s returned HTTP 200' % cp_options.url)

	def test_failcert_check_pycurl3_200(self):
		"""check for selfsigned failure"""
		cp_options = CheckPyCurlOptions()
		cp_options.url = 'https://%s:%s' % (self.host, self.port)
		cpc = CheckPyCurl(cp_options)
		rc = cpc.curl()
		self.assertEqual(rc, 2)
		self.assertEqual(cpc.results['status'], 'SSL certificate problem: self-signed certificate')

	@classmethod
	def tearDownClass(cls):
		"""clean up temp cert dir"""
		shutil.rmtree(cls.tmpdir)


if __name__ == '__main__':
    unittest.main()
