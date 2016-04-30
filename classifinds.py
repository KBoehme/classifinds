import requests
import smtplib
import json
import configparser
import json
import time
from datetime import datetime, timedelta
import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

"""
Find some cool stuff.
"""
config = configparser.ConfigParser()
config.read('config.ini')
ourthings = json.load(open('things.json'))
params = json.load(open('params.json'))

logging.basicConfig(filename='klassifinds.log',level=logging.INFO)

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
	r = requests.post(config['PARAMS']['api_base'], data=ad_params)
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
		return_string = HTML_EMAIL_TEMPLATE.format(ad['image'], config['PARAMS']['thumbnail'], ad_info['title'], 
			ad_info['price'], ad_info['city'], ad_info['state'], ' '.join(keyword_hits),
			config['PARAMS']['web_base'], '218', ad['sid'])
	else:
		return_string = None

	return return_string

def handle_things(email, things):
	logging.info("Checking {} stuff".format(email))
	# Create message container.
	email_summary = MIMEMultipart('related')
	email_summary['Subject'] = config['EMAIL']['subject']
	email_summary['From'] = config['EMAIL']['email']
	email_summary['To'] = email
	email_contents = []
	total_hits = 0
	for cool_thing, info in things.items():

		params['s'] = cool_thing
		logging.info("\t- {}".format(cool_thing))
		max_price = info['max']
		keywords = info['keywords']

		r = requests.post(config['PARAMS']['api_base'], data=params)
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
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(config['EMAIL']['email'], config['EMAIL']['key'])

	for email, things in ourthings.items():
		total_hits, email_summary = handle_things(email, things)
		if total_hits and not DEBUG:
			logging.info("Sending {} Klassifind winners to {}.".format(total_hits, email))
			server.sendmail(config['EMAIL']['email'], email, email_summary.as_string())

if __name__ == '__main__':
	klassifinds()