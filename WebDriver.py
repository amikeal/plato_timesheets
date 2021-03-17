#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Assumes: Python 3 (>= 3.6)
#          selenium ($ pip install selenium)
#          ChromeDriver (http://chromedriver.chromium.org)
#          Chrome binary (> v61)
#

__author__ = "Adam Mikeal <adam@tamu.edu>"
__version__ = "0.8"

import os
import sys
import logging
import subprocess
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.common.exceptions import NoSuchElementException

# Module variables
CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
DRIVER_PATH = 'bin/chromedriver'
CHROME_MINVER = '61'
DRIVER_MINVER = '2.4'
LOG_LEVEL = logging.DEBUG
DUO_TIMEOUT = 15

# Set up logging
LOG = logging.getLogger('web_driver')
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s: %(message)s'))
LOG.addHandler(log_handler)
LOG.setLevel(LOG_LEVEL)

class AuthenticatedWeb(object):

	TARGET_URL = None
	DRIVER = None
	AUTH_URL = 'https://cas.tamu.edu'

	def __init__(self, url, chrome_path=None, chrome_driver=None, auth_url=None, duo_timeout=None, log_level=None):

		# Set the log level first (if specified)
		if log_level:
			self.set_log_level(log_level)

		# store object variables
		self.TARGET_URL = url
		LOG.info(f"Using target URL: {self.TARGET_URL}")

		# Override the default binary paths if specified
		if chrome_path:
			self.CHROME_PATH = os.path.abspath(chrome_path)
		else:
			self.CHROME_PATH = os.path.abspath(CHROME_PATH)
		LOG.info(f"Using Chrome binary loaction: {self.CHROME_PATH}")

		if chrome_driver:
			self.DRIVER_PATH = os.path.abspath(chrome_driver)
		else:
			self.DRIVER_PATH = os.path.abspath(DRIVER_PATH)
		LOG.info(f"Using selenium driver location: {self.DRIVER_PATH}")

		# Override the default CAS URL if specified
		if auth_url:
			self.AUTH_URL = auth_url

		if duo_timeout:
			if isinstance(duo_timeout, int):
				LOG.info(f"DUO_TIMEOUT set to {duo_timeout} seconds")
				DUO_TIMEOUT = duo_timeout
			else:
				LOG.error(f"Unable to set DUO_TIMEOUT to specified value ('{duo_timeout}'); must be an integer. Using default value ({DUO_TIMEOUT})")
		
		# Test paths and binaries
		if not os.path.isfile(self.CHROME_PATH):
			LOG.error(f"No binary found at CHROME_PATH: {self.CHROME_PATH}")
			return None

		if not self._check_version(self.CHROME_PATH, CHROME_MINVER, version_index=2):
			LOG.error(f"Chrome version specified is too old: must be >{CHROME_MINVER}")
			return None

		if not os.path.isfile(self.DRIVER_PATH):
			LOG.error(f"No binary found at DRIVER_PATH: {self.DRIVER_PATH}")
			return None

		if not self._check_version(self.DRIVER_PATH, DRIVER_MINVER):
			LOG.error(f"Chrome driver specified is too old: must be >{DRIVER_MINVER}")
			return None

		# Prep the headless Chrome
		chrome_options = Options()  
		chrome_options.add_argument("--headless")
		chrome_options.binary_location = self.CHROME_PATH
		self.DRIVER = webdriver.Chrome(executable_path=self.DRIVER_PATH, options=chrome_options)

		#
		# Attempt to get to the target site (expect CAS redirection)
		#    https://selenium-python.readthedocs.io/api.html#selenium.webdriver.remote.webdriver.WebDriver
		#
		self.DRIVER.get(self.TARGET_URL)

		# Detect if CAS redirection happened
		if self.AUTH_URL in self.DRIVER.current_url:
			LOG.debug(f"Auth redirection detected; current URL: {self.DRIVER.current_url}")

	def __repr__(self):
		return f"Headless Chrome object for URL: {self.TARGET_URL} (currently at {self.DRIVER.current_url})"

	def __del__(self):
		# Close the connection to the headless browser (clean up resources)
		if self.DRIVER:
			LOG.debug("Calling close() on selenium driver...")
			self.DRIVER.close()

	def set_log_level(self, lvl):
		if not isinstance(lvl, int):
			LOG.error(f"Invalid log level: '{lvl}' (expects integer)")
			raise ValueError(f"Invalid log level: '{lvl}'")
		LOG_LEVEL = lvl
		LOG.setLevel(LOG_LEVEL)
		LOG.info(f"New log level set: {lvl} ({logging.getLevelName(lvl)})")

	def _check_version(self, binary_path, minimum_version, version_index=1, flag='--version'):
		try:
			# grab the version string by passing '--version' option to the binary
			output = subprocess.check_output(f"'{binary_path}' {flag}", shell=True)
			LOG.debug(f"Version output: {output.decode('utf-8')}")

			# split the output string into parts and grab the part specified by 'version_index'
			output_parts = output.decode('utf-8').split()
			LOG.debug(f"Version index: {version_index}; List element: '{output_parts[version_index]}'")

			# compare the version part to the 'minumum_version' string
			if output_parts[version_index] < minimum_version:
				return False
			else:
				return True
		except Exception as e:
			LOG.error(f"Unable to verify version for binary: {binary_path}")
			LOG.debug(f"{e.__class__.__name__}: {e}")
			return False

	def authenticate(self, netid, password, expect_duo=True):
		# Check for AUTH_URL and exit if not seen
		if self.AUTH_URL not in self.DRIVER.current_url:
			LOG.error(f"Unable to perform authentication (expected {self.AUTH_URL}; current_url={self.DRIVER.current_url} )")	
			return False

		# Start the auth process
		LOG.info(f"Authenticating using NetID: {netid}")
		LOG.info(f"Authenticating using password: {password[0]}{'*'*(len(password)-2)}{password[-1]}")

		try:
			# Find the username field and enter the NetID
			u_fld = self.DRIVER.find_element_by_id("username")
			u_fld.clear()
			u_fld.send_keys(netid)
			u_fld.send_keys(Keys.TAB)

			# Enter the password
			p_fld = self.DRIVER.find_element_by_id("password")
			p_fld.clear()
			p_fld.send_keys(password)
			p_fld.send_keys(Keys.RETURN)

		except NoSuchElementException as e:
			LOG.error(f"Unable to locate username or password field")
			LOG.debug(f"{e.__class__.__name__}: {e}")
			return False

		except Exception as e:
			LOG.error(f"Unable to access username or password field")
			LOG.debug(f"{e.__class__.__name__}: {e}")
			return False

		# return now if expect_duo is set to False
		if not expect_duo:
			LOG.debug(f"expect_duo=False; Not attempting 2FA")
			return True

		# Handle the Duo 2-factor auth
		try:
			# Enter the Duo iframe
			LOG.debug("Attempting to enter Duo <iframe> for 2FA")
			self.DRIVER.switch_to.frame(self.DRIVER.find_element_by_id("duo_iframe"))

			# Get the correct button and click it
			LOG.debug("Clicking button for default 2FA method (should be push notification)")
			button = self.DRIVER.find_element_by_xpath('//*[@id="auth_methods"]/fieldset[1]/div[1]/button')
			button.click()

			# Wait for the page to redirect
			LOG.info(f"Waiting {DUO_TIMEOUT} seconds for Duo 2FA...")
			WebDriverWait(self.DRIVER, DUO_TIMEOUT).until(EC.url_contains(self.TARGET_URL))
			LOG.debug(f"Detected redirect to target URL ('{self.TARGET_URL}')")
			return True
		except Exception as e:
			LOG.error("Could not complete Duo 2FA process.")
			LOG.debug(f"{e.__class__.__name__}: {e}")
			return False

	def by_xpath(self, xpath_str, find_all=False):
		LOG.debug(f"Called by_xpath() using expression: '{xpath_str}'")
		if find_all:
			return self.DRIVER.find_elements_by_xpath(xpath_str)
		else:
			return self.DRIVER.find_element_by_xpath(xpath_str)

	def by_name(self, elem_name, find_all=False):
		LOG.debug(f"Called by_name() using string: '{elem_name}'")
		if find_all:
			return self.DRIVER.find_elements_by_name(elem_name)
		else:
			return self.DRIVER.find_element_by_name(elem_name)

	def by_id(self, elem_id):
		LOG.debug(f"Called by_id() using string: '{elem_id}'")
		return self.DRIVER.find_element_by_id(elem_id)

	def send_keys(self, keys):
		#TODO: Don't think this method is valid here
		LOG.debug(f"Called send_keys() using string: '{keys}'")
		return self.DRIVER.send_keys(keys)

	def go(self, url):
		LOG.debug(f"Called get() with url: '{url}'")
		return self.DRIVER.get(url)
