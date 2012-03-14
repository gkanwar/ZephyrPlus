import tornado.httpserver
import tornado.ioloop
import tornado.web

import os
import time
import datetime
import simplejson
import subprocess
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

#import models
from models import Zephyr, Subscription, Account

#from django.conf import settings
#settings.configure(DATABASE_ENGINE='sqlite3', DATABASE_NAME='zephyrs.db')

class MainPageHandler(tornado.web.RequestHandler):
    def get(self):
        logged_in = False
        if not logged_in:
            self.render("templates/login.html")
        else:
            self.render("templates/index.html")

class MessageWaitor(object):
	# waiter stores (request, Subscription)
	waiters = [] # table that deals with long polling requests

	@classmethod
	def wait_for_messages(cls, request, sub):
		cls.waiters.append((request, sub))

	def new_messages(cls, zephyr):
		for waitee in cls.waiters:
			if waitee[1].match(zephyr):
				waitee[0].write(zephyr)
				waitee[0].finish()
				waiter.remove(callback)
				
class ChatUpdateHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	def get(self, *args, **kwargs):
		class_name=self.get_argument('class')
		instance = self.get_argument('instance', "*")
		recipient = self.get_argument('recipient', "*")
		startdate = self.get_argument('startdate', "0") # change later to 2 weeks ago
		enddate = self.get_argument('enddate', str(1000*2**35)) # if longpolling, should not have end date
		longpoll = self.get_argument('longpoll', "False")
		#TODO: do input validation on arguments
		sub = Subscription(class_name=class_name, instance=instance, recipient=recipient)
		print sub
		print sub.get_filter()
		print "startdate:" + str(datetime.datetime.fromtimestamp(float(startdate)/1000))
		print "enddate:" + str(datetime.datetime.fromtimestamp(float(enddate)/1000))

		zephyrs = sub.get_filter().filter(date__gt=datetime.datetime.fromtimestamp(float(startdate)/1000),
										  date__lt=datetime.datetime.fromtimestamp(float(enddate)/1000))

		if len(zephyrs) == 0 and longpoll.lower() == "true":
			MessageWaitor.wait_for_messages(self,sub)
		else:
			response = []
			for zephyr in zephyrs:
                            values = {
                                    'message': zephyr.message,
                                    'sender': zephyr.sender,
                                    'date': (zephyr.date - datetime.datetime.fromtimestamp(0)).total_seconds()*1000,
                                    'class': zephyr.dst.class_name,
                                    'instance': zephyr.dst.instance,
                                    'recipient': zephyr.dst.recipient
                                }
                            response.append(values)
			self.set_header('Content-Type', 'text/plain')
			self.write(simplejson.dumps(response))
			self.finish()
	
	def post(self, *args, **kwargs):
		class_name = self.get_argument('class', 'message')
		instance = self.get_argument('instance', 'personal')
		recipient = self.get_argument('recipient', '*')
		signature = self.get_argument('signature', None)
		message = self.get_argument('message')
		if signature is not None:
			signature = "username" + " (" + signature + ")"
		else:
			signature = "username"
		proc = subprocess.Popen(["zwrite", "-c", class_name, "-i", instance, "-s", signature, recipient], stdin=subprocess.PIPE)
		proc.stdin.write(message)
		proc.stdin.close()

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": "rS24mrw/2iCQUSwtuptW8p1jbidrs5eqV3hdPuJ8894L",
    "login_url": "/login",
    "xsrf_cookies": True,
}

application = tornado.web.Application([
	(r"/chat", ChatUpdateHandler),
	(r"/", MainPageHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": settings["static_path"]}),
		], debug=True)

def main():
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(8888)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
