#! /usr/bin/env python

import os
import sys
import httplib
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import datetime

from django.db import models
from models import Zephyr, Subscription, Account

def main(argv):
	if len(argv) != 6:
		print('Error: Tried to insert ' + str(argv[1:]))
		sys.exit(2)
	# expect zephyrs in format:
	# class_name, instance, recipient, sender, message
	
	print('Insert: ' + str(argv[1:]))
	# Require that class_name, instance, and recipient all be in lower case
	s = Subscription.objects.get_or_create(class_name=argv[1].lower(), instance=argv[2].lower(), recipient=argv[3].lower())[0]
	z = Zephyr(message=argv[5], sender=argv[4], date=datetime.datetime.now(), dst=s)
	z.save()

	# Tell the server to update
	z_id = z.id
	h = httplib.HTTPConnection('localhost:8888')
	h.request('GET', '/update?id='+str(z_id))
	
	r = h.getresponse()
	print(r.status, r.reason)


if __name__ == "__main__":
	main(sys.argv)
