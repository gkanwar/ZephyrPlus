import tornado.httpserver, tornado.ioloop, tornado.web, tornado.auth
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

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        username = self.get_secure_cookie("user")
        if username is not None:
            return Account.objects.get_or_create(username=username)[0]
        return None

class MainPageHandler(BaseHandler):
    def get(self):
        if self.current_user is None:
            self.render("templates/login.html")
        else:
            self.render("templates/index.html")

class LoginHandler(tornado.web.RequestHandler, tornado.auth.OpenIdMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self._on_auth)
            return
        self.authenticate_redirect()

    def _on_auth(self, user):
        if user is None or "email" not in user:
            self.redirect("/")
            return
        username = user["email"].lower()
        if username.endswith("@mit.edu"):
            username = username.split("@")[0]
        self.set_secure_cookie("user", username)
        self.redirect(self.get_argument("next", "/"))

class GoogleLoginHandler(LoginHandler, tornado.auth.GoogleMixin):
    pass

class CertsLoginHandler(LoginHandler):
    _OPENID_ENDPOINT = "https://garywang.scripts.mit.edu/openid/login.py"

class MessageWaitor(object):
	# waiter stores (request, Subscription)
	waiters = [] # table that deals with long polling requests

	@classmethod
	def wait_for_messages(cls, request, sub):
		cls.waiters.append((request, sub))

	@classmethod
	def new_message(cls, zephyr):
		for waitee in cls.waiters:
			if waitee[1].match(zephyr):
				response = []
				values = {
						'message': zephyr.message,
						'sender': zephyr.sender,
						'date': (zephyr.date - datetime.datetime.fromtimestamp(0)).total_seconds()*1000,
						'class': zephyr.dst.class_name,
						'instance': zephyr.dst.instance,
						'recipient': zephyr.dst.recipient
						}
				response.append(values)
				waitee[0].set_header('Content-Type', 'text/plain')
				waitee[0].write(simplejson.dumps(response))
				waitee[0].finish()
				cls.waiters.remove(waitee)

class ChatUpdateHandler(BaseHandler):
	@tornado.web.asynchronous
	@tornado.web.authenticated
	def get(self, *args, **kwargs):
		class_name=self.get_argument('class')
		instance = self.get_argument('instance', "*")
		recipient = self.get_argument('recipient', "*")
		startdate = self.get_argument('startdate', "0") # change later to 2 weeks ago
		enddate = self.get_argument('enddate', str(1000*2**35)) # if longpolling, should not have end date
		longpoll = self.get_argument('longpoll', "False")
		#TODO: do input validation on arguments
		sub = Subscription(class_name=class_name, instance=instance, recipient=recipient)
		print('\n');
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
                                    'date': int((zephyr.date - datetime.datetime.fromtimestamp(0)).total_seconds()*1000),
                                    'class': zephyr.dst.class_name,
                                    'instance': zephyr.dst.instance,
                                    'recipient': zephyr.dst.recipient
                                }
                            response.append(values)
			self.set_header('Content-Type', 'text/plain')
			self.write(simplejson.dumps(response))
			self.finish()
	
	def on_connection_close(self):
            for waitee in MessageWaitor.waiters:
                if waitee[0] == self:
                    MessageWaitor.waiters.remove(waitee)
	
        @tornado.web.authenticated
	def post(self, *args, **kwargs):
		class_name = self.get_argument('class', 'message')
		instance = self.get_argument('instance', 'personal')
		recipient = self.get_argument('recipient', '*')
		signature = self.get_argument('signature', None)
		message = self.get_argument('message')
		username = self.current_user.username
		if signature is not None:
			signature = username + " (" + signature + ")"
		else:
			signature = username
                signature += " via ZephyrPlus"
		proc = subprocess.Popen(["zwrite", "-c", class_name, "-i", instance, "-s", signature, recipient], stdin=subprocess.PIPE)
		proc.stdin.write(message)
		proc.stdin.close()

class NewZephyrHandler(tornado.web.RequestHandler):
	def get(self, *args, **kwargs):
		z_id = self.get_argument('id', default=0);
		if z_id != None and z_id > 0:
			z = Zephyr.objects.filter(id=z_id)
			MessageWaitor.new_message(z[0])

class UserHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = self.current_user
        self.set_header('Content-Type', 'text/plain')
        self.write(simplejson.dumps({
                "username": user.username,
                "subscriptions": [{
                        "class": sub.class_name,
                        "instance": sub.instance,
                        "recipient": sub.recipient
                    } for sub in user.subscriptions.all()]
            }))
    

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": "rS24mrw/2iCQUSwtuptW8p1jbidrs5eqV3hdPuJ8894L",
    "login_url": "/login",
    "xsrf_cookies": False,
    "debug": True,
}

application = tornado.web.Application([
        (r"/chat", ChatUpdateHandler),
        (r"/update", NewZephyrHandler),
        (r"/login", CertsLoginHandler),
        (r"/user", UserHandler),
        (r"/", MainPageHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": settings["static_path"]}),
    ], **settings)

def main():
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(8888)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
