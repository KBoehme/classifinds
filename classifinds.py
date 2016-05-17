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
try:
    # Python 3
    from urllib.parse import urlparse, parse_qs
except ImportError:
    # Python 2
    from urlparse import urlparse, parse_qs

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

# Use sms gateway provided by mobile carrier:
# at&t:     number@mms.att.net
# t-mobile: number@tmomail.net
# verizon:  number@vtext.com
# sprint:   number@page.nextel.com
TEXT_MESSAGE_MAP = {
	'at&t':     'mms.att.net',
	't-mobile': 'tmomail.net',
	'verizon':  'vtext.com',
	'sprint':   'page.nextel.com'
}

"""
Find some cool stuff.
"""
config = configparser.ConfigParser()
base = "/home/ec2-user/classifinds/" #Add base of config.ini file and things.json...

config.read(base + 'config.ini')
ourthings = json.load(open(base + 'things.json'))

TEXT_MESSAGE = "I think I just klassifound something you might like. Check your email."

URL_TO_API_MAP = {
	"max_price": "max",
	"min_price": "min",
	"search": "s",
	"nid": "category",
	"zip": "z",
	"distance": "d"
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

def prepare_query(query):
	prepared_query = {}
	for old_key, new_key in URL_TO_API_MAP.items():
		if old_key in query:
			prepared_query[new_key] = query[old_key]
	prepared_query["cmd"] = "list"
	return prepared_query


def handle_things(email, things):
	klassifinds_log.info("Checking {} stuff".format(email))
	# Create message container.
	email_summary = MIMEMultipart('related')
	email_summary['Subject'] = "Klassifind winners"
	email_summary['From'] = config.get('SECRETS', 'email')
	email_summary['To'] = email
	email_contents = []
	total_hits = 0
	send_text = False
	for search_url, info in things.items():
		keywords = info['keywords']
		text_person = info['text']

		query = parse_qs( urlparse(search_url).query )
		query = prepare_query(query)
		cool_thing = query['s']

		r = requests.post(config.get('PARAMS', 'api_base'), data=query)
		hitresults = json.loads(r.text)
		now = datetime.now()
		last_run = now - timedelta(minutes = 5)
		promising_ads = [ad for ad in hitresults if (datetime.fromtimestamp(ad['display_time']) > last_run) and ad['image'] ]
		klassifinds_log.info("\t- {} - Found {} ads ({} promising)".format(cool_thing, len(hitresults), len(promising_ads)))
		hits = 0
		ad_hit_contents = []
		for ad in promising_ads:
			#Only process ads from the last hour...
			result = process_ad(ad, keywords)
			if result:
				hits += 1
				ad_hit_contents.append(result)
				if text_person:
					send_text = True
		if hits:
			email_contents.append("<h2>{}</h2>".format(' '.join(cool_thing).title()))
			email_contents.extend(ad_hit_contents)
			email_contents.append('<hr>')
		total_hits += hits
	html = ''.join(email_contents)
	email_summary.attach(MIMEText(html, 'html'))
	return total_hits, email_summary, send_text

def klassifinds():
	klassifinds_log.info(datetime.utcnow())
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(config.get('SECRETS', 'email'), config.get('SECRETS', 'key'))

	for name, info in ourthings.items():
		email = info['email']
		phone = info['phone']
		carrier = info['carrier']
		things = info['things']

		total_hits, email_summary, send_text = handle_things(email, things)
		if total_hits and not DEBUG:
			klassifinds_log.info("Sending {} Klassifind winners to {}.".format(total_hits, email))
			server.sendmail(config.get('SECRETS', 'email'), email, email_summary.as_string())
			if send_text:
				klassifinds_log.info("Sending text message to {}.".format(phone))
				server.sendmail( config.get('SECRETS', 'email'), '{}@{}'.format(phone, TEXT_MESSAGE_MAP[carrier]), TEXT_MESSAGE)
	klassifinds_log.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
if __name__ == '__main__':
	klassifinds()
