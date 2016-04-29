import requests
import smtplib
import json
import configparser
import json
import time
"""
Find some cool stuff.
"""
config = configparser.ConfigParser()
config.read('config.ini')
ourthings = json.load(open('things.json'))
params = json.load(open('params.json'))

DEBUG = True

def process_search(text):
	hitresults = json.loads(text)
	for ad in hitresults:
		print(time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(ad['display_time']/1000.)))

server = None
if not DEBUG:
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(config['EMAIL']['email'], config['EMAIL']['key'])

for email, info in ourthings.items():
	things = info['things']
	print("Checking {} stuff".format(email))
	for cool_thing in things:
		params['s'] = cool_thing
		print("\t- {}".format(cool_thing))

		r = requests.post(config['PARAMS']['api_base'], data=params)
		process_search(r.text)
		if not DEBUG:
			server.sendmail(config['EMAIL']['email'], email, msg)
			server.quit()



