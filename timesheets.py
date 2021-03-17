#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse
import getpass
import logging
import WebDriver

CMD_LIST = {
	'submit':  'Submit any available personal timesheets',
	'approve': 'Approve all overdue timesheets for direct reports',
}

# Global variables
LOG = logging.getLogger('timesheets')
LOG_LEVEL = logging.WARNING
TEST_MODE = False


# Initialize logging
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s: %(message)s'))
LOG.addHandler(log_handler)
LOG.setLevel(LOG_LEVEL)


def approve(web_driver):

	# Get a list of all actionable links
	links = []
	for a in web_driver.by_xpath('//a[contains(@href, "timeentryapprove.asp")]', find_all=True):
		links.append(a.get_attribute('href'))
	LOG.debug(f"Identified {len(links)} matching links...")

	if len(links) < 1:
		print("\nNo unapproved timesheets found.")
		sys.exit(0)

	# Iterate through all those links and approve the timecards
	for page in links:
		web_driver.go(page)

		# Grab the employee name (for log)
		try:
			name_elem = web_driver.by_xpath('/html/body/font/div/table[3]/tbody/tr/td/font/font/form/p[1]/table/tbody/tr[1]/td[2]/font')
			date_elem = web_driver.by_xpath('/html/body/font/div/table[3]/tbody/tr/td/font/p[2]/table/tbody/tr/td/font/b/font')
			print(f"Employee: {name_elem.text}")
			print(f"Time period: {date_elem.text}")
		except Exception as e:
			print("\nCould not read employee data from webapp.\n\n")
			LOG.debug(f"{e.__class__.__name__}: {e}")

		# Find and click the "Approve" button
		approve_btn = web_driver.by_name('btnTA_Approve')
		if TEST_MODE is False:
			approve_btn.send_keys(WebDriver.Keys.RETURN)
			print("APPROVED\n")


def submit(web_driver):
	
	# Keep doing this as long as there are more timesheets to approve
	while True:

		# Look for the "Submit for Approval" button
		try:
			submit_btn = web_driver.by_name('btnTE_TimeSubmit')
			submit_btn.send_keys(WebDriver.Keys.RETURN)
		except Exception as e:
			print("No timesheets are available for submission.")
			LOG.debug(f"{e.__class__.__name__}: {e}")
			break

		# Look for the second "Submit" button
		try:
			date_elem = web_driver.by_xpath('/html/body/font/div/table[3]/tbody/tr/td/font/p/table/tbody/tr[1]/td/table/tbody/tr/td/font/b/font')
			print(f"Time period: {date_elem.text} ")

			# If we are NOT in text mode, actually submit the timesheet
			if TEST_MODE is False:
				second_submit = web_driver.by_name('btnTE_TimeConfirm')
				second_submit.send_keys(WebDriver.Keys.RETURN)
				print("SUBMITTED\n")

		except Exception as e:
			# Could not locate the second "Submit" button -- something is wrong
			print("Something went wrong.")
			LOG.debug(f"{e.__class__.__name__}: {e}")
			break

		# Look for a "NEXT" link, and follow it to the next page
		try:
			next_link = web_driver.by_xpath('/html/body/font/div/table[3]/tbody/tr/td/font/p[3]/b/a')
			next_link.send_keys(WebDriver.Keys.RETURN)
		except Exception as e:
			print("No more timesheets to submit.")
			LOG.debug(f"{e.__class__.__name__}: {e}")
			break


if __name__ == '__main__':

	parser = argparse.ArgumentParser(
	    description='Submit and approve PLATO timesheets.',
	    usage='''timesheets.py COMMAND [<args>]

commands:
   submit     Submit any available personal timesheets
   approve    Approve all overdue timesheets for direct reports

''')
	parser.add_argument('COMMAND', nargs='?', default=None, help='Subcommand to run')
	parser.add_argument('-u', dest='USERNAME', default=None, help='Use the supplied value for the NetID authentication')
	parser.add_argument('-p', dest='PASSWORD', default=None, help='Use the supplied value for the password')
	parser.add_argument('-v', '--verbose', dest='VERBOSE', action='count', help='Output extra info (more -v\'s = more info)')
	parser.add_argument('-t', '--test', dest='TEST_MODE', action='store_true', help='Run in test mode (no changes are made)')
	args = parser.parse_args()

	if not args.COMMAND or not args.COMMAND in CMD_LIST:
		print('Unrecognized command')
		parser.print_help()
		exit(1)

	# Set the verbosity based on # of v's (-v, -vv)
	if args.VERBOSE == 1:
		LOG_LEVEL = logging.INFO
	elif args.VERBOSE == 2:
		LOG_LEVEL = logging.DEBUG
	else:
		LOG_LEVEL = logging.WARNING
	LOG.setLevel(LOG_LEVEL)

	# Check for TEST_MODE
	if args.TEST_MODE:
		TEST_MODE = args.TEST_MODE
		print("\nRUNNING IN TEST MODE. No changes will be applied.\n")

	# Grab the username from the commandline arg, or prompt the user
	if args.USERNAME:
		NETID = args.USERNAME
	else:
		NETID = input('NetID: ')

	# Grab the password from the commandline arg, or prompt the user
	if args.PASSWORD:
		PASSWD = args.PASSWORD
	else:
		PASSWD = getpass.getpass('Password: ')

	# Check for environment variables for paths
	if os.getenv('CHROME_PATH'):
		CHROME_PATH = os.getenv('CHROME_PATH')
	else:
		CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

	if os.getenv('DRIVER_PATH'):
		DRIVER_PATH = os.getenv('DRIVER_PATH')
	else:
		DRIVER_PATH = "bin/chromedriver"

	# Set the correct URL for the action selected
	if args.COMMAND == 'approve':
		plato_url = 'https://plato.tamu.edu/Approval/'
	else:
		plato_url = 'https://plato.tamu.edu/timeentry.asp'

	# Create the web automator object
	web = WebDriver.AuthenticatedWeb(plato_url, log_level=LOG_LEVEL, chrome_path=CHROME_PATH, chrome_driver=DRIVER_PATH)
	print("Waiting for Duo 2FA...")
	web.authenticate(NETID, PASSWD)

	# Use dispatch pattern to invoke method with same name, and pass the WebDriver obj
	locals()[args.COMMAND](web)
