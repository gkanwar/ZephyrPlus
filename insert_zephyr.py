#! /usr/bin/env python2

import time
import os
import sys
import httplib
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import datetime

from django.db import models
from models import Zephyr, Subscription, Account


debug = True

### to append a zephyr to the incomingZephyrs pipe a user must:
#	add the zephyrs class_name, instance, recipient, sender, message
#	and signature to new lines and then add one extra empty line
#
def main(argv):
	delimitor="\x00\n"
	if debug:
		print "Starting insert_zephyr"
	pipePath = "./incomingZephyrs.pipe"
	#open fifo pipe
	file = open(pipePath)	
	if debug:
		print "listening to pipe"
	zArray = []	
	zBuffer = ""
	while 1:
		line = file.readline()
		if line == '':
			time.sleep(0.1)
			continue
		if  line == delimitor:
			#print("D")
			zArray.append(zBuffer)
			#print(zArray)
			zBuffer = ""
			if len(zArray) == 6:
				print(str(zArray))
				#processLine(zArray)
				zArray = []
				zBuffer = ""
		else:
			zBuffer = zBuffer + line[:-1]
			#print(zBuffer)

def processLine(zArray):
	if debug:
		print "processing",zArray
	if len(zArray) != 6:
		print('Error: Tried to insert ' + str(zArray))
		sys.exit(2)
	# expect zephyrs in format:
	# class_name, instance, recipient, sender, message, signature
	
	print('Insert: ' + str(zArray))
	# Require that class_name, instance, and recipient all be in lower case
	s = Subscription.objects.get_or_create(class_name=zArray[0].lower(), instance=zArray[1].lower(), recipient=zArray[2].lower())[0]
	
	sender = zArray[3]
	signature = zArray[5]
	if sender == "daemon/zephyrplus.xvm.mit.edu":
            sender = signature.split(" ")[0]
            if signature.find("(") != -1:
                signature = signature[signature.find("(")+1:signature.rfind(")")]
            else:
                signature = ""
	signature = signature.replace(" (via ZephyrPlus", "").replace("via ZephyrPlus", "")
	z = Zephyr(message=zArray[4], sender=sender, date=datetime.datetime.now(), dst=s, signature=signature)
	z.save()

	# Tell the server to update
	z_id = z.id
	h = httplib.HTTPConnection('localhost:8888')
	h.request('GET', '/update?id='+str(z_id))
	
	r = h.getresponse()
	print(r.status, r.reason)


if __name__ == "__main__":
	main(sys.argv)
