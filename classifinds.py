import requests
import smtplib
import json
try:
	import configparser
except ImportError:
	import ConfigParser as configparser

import json
import time
import os
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

"""
Find some cool stuff.
"""
config = configparser.ConfigParser()
base = "" #Add base of config.ini file and things.json...

config.read(base + 'config.ini')
ourthings = json.load(open(base + 'things.json'))
params = {
	"cmd": "list",
	"c": "500",
	"o": "0",
	"min": "0",
	"max": "100",
	"d": "20",
	"srt": "Most+recent",
	"slr": "Private+sellers"
}
# Set up a specific logger with our desired output level
klassifinds_log = logging.getLogger('MyLogger')
klassifinds_log.setLevel(logging.INFO)

# Add the log message handler to the logger
handler = RotatingFileHandler(base+'klassifinds.log', maxBytes=1000000, backupCount=0)

klassifinds_log.addHandler(handler)


DEBUG = False

HTML_EMAIL_TEMPLATE = """\
			<div class="column">
			<img class="thumbnail" src="{}{}">
			<h5>{}   |   {}    |    {}/{}    | {}</h5>
			<a href="{}nid={}&ad={}">Go to ad</a>
			</div>
		"""

def process_ad(ad, keywords):
	ad_params = {
		"cmd": "ad",
		"id": ad['sid']
	}
	r = requests.post(config.get('PARAMS', 'api_base'), data=ad_params)
	ad_info = json.loads(r.text)[0]
	ad_description = []
	if ad_info['title']:
		ad_despcrition = ad_info['title'].split()
	if ad_info['body']:
		ad_description += ad_info['body'].split()

	ad_description = [word.lower() for word in ad_description]
	keyword_hits = []
	for word in keywords:
		if word.lower() in ad_description:
			keyword_hits.append(word)

	return_string = ""
	if keyword_hits:
		return_string = HTML_EMAIL_TEMPLATE.format(ad['image'], config.get('PARAMS', 'thumbnail'), ad_info['title'], 
			ad_info['price'], ad_info['city'], ad_info['state'], ' '.join(keyword_hits),
			config.get('PARAMS', 'web_base'), '218', ad['sid'])
	else:
		return_string = None

	return return_string

def handle_things(email, things):
	klassifinds_log.info("Checking {} stuff".format(email))
	# Create message container.
	email_summary = MIMEMultipart('related')
	email_summary['Subject'] = "Klassifind winners"
	email_summary['From'] = config.get('EMAIL', 'email')
	email_summary['To'] = email
	email_contents = []
	total_hits = 0
	for cool_thing, info in things.items():

		params['s'] = cool_thing
		klassifinds_log.info("\t- {}".format(cool_thing))
		max_price = info['max']
		keywords = info['keywords']

		r = requests.post(config.get('PARAMS', 'api_base'), data=params)
		hitresults = json.loads(r.text)
		now = datetime.now()
		last_run = now - timedelta(hours = 1)
		promising_ads = [ad for ad in hitresults if (datetime.fromtimestamp(ad['display_time']) > last_run) and ad['image'] and float(ad['price']) < max_price ]
		hits = 0
		ad_hit_contents = []
		for ad in promising_ads:
			#Only process ads from the last hour...
			result = process_ad(ad, keywords)
			if result:
				hits += 1
				ad_hit_contents.append(result)
		if hits:
			email_contents.append("<h2>{}</h2>".format(' '.join(cool_thing.split('+')).title()))
			email_contents.extend(ad_hit_contents)
			email_contents.append('<hr>')
		total_hits += hits
	html = ''.join(email_contents)
	email_summary.attach(MIMEText(html, 'html'))
	return total_hits, email_summary

def klassifinds():
	klassifinds_log.info(datetime.utcnow())
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(config.get('EMAIL', 'email'), config.get('EMAIL', 'key'))

	for email, things in ourthings.items():
		total_hits, email_summary = handle_things(email, things)
		if total_hits and not DEBUG:
			klassifinds_log.info("Sending {} Klassifind winners to {}.".format(total_hits, email))
			server.sendmail(config.get('EMAIL', 'email'), email, email_summary.as_string())
	klassifinds_log.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
if __name__ == '__main__':
	klassifinds()