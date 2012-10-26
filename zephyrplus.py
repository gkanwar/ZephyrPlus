#! /usr/bin/python2

# Tornado Server
import tornado.httpserver, tornado.ioloop, tornado.web, tornado.auth

# Multiprocesses
import os, subprocess, threading

# Utility libraries
import datetime, time
import math
import simplejson
import sys

# Logging and debugging
import traceback
import email, smtplib

# Zephyr Libraries
import zephyr
import loadZephyrs
zephyr.init()

# Django Library
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from models import Zephyr, Subscription, Account
import django.conf

LOGFILE_NAME = django.conf.settings.TORNADO_LOGFILE_NAME

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        #username = self.get_secure_cookie("user", max_age_days=31)
        username = self.get_secure_cookie("user")
        if username is not None:
            account, created = Account.objects.get_or_create(username=username)
            if created:
                account.subscriptions.add(Subscription.objects.get_or_create(class_name="lobby", instance="*", recipient="*")[0])
                account.subscriptions.add(Subscription.objects.get_or_create(class_name=username, instance="*", recipient="*")[0])
                zephyrLoader.addSubscription(Subscription.objects.get_or_create(class_name=username, instance="*", recipient="*")[0])
            return account
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
        self.set_secure_cookie("user", username, expires_days=31)
        self.redirect(self.get_argument("next", "/"))

class GoogleLoginHandler(LoginHandler, tornado.auth.GoogleMixin):
    pass

class CertsLoginHandler(LoginHandler):
    _OPENID_ENDPOINT = "https://garywang.scripts.mit.edu/openid/login.py"

class StupidLoginHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.web.authenticated
    def get(self):
        if self.current_user.username in ['garywang', 'gurtej', 'mikewu', 'timyang', 'zeidman']:
            username=self.get_argument("username")
            self.set_secure_cookie("user", username, expires_days=31)
        self.redirect("/")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")

class MessageWaitor(object):
    # waiter stores (request, Subscription)
    waiters = [] # table that deals with long polling requests

    @classmethod
    def wait_for_messages(cls, request, sub):
        cls.waiters.append((request, sub))

    @classmethod
    def new_message(cls, zephyr):
        new_waiters = []
        for waitee in cls.waiters:
            if waitee[1].match(zephyr):
                waitee[0].write_zephyrs([zephyr])
            else:
                new_waiters.append(waitee)
        cls.waiters = new_waiters

class ChatUpdateHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        class_name=self.get_argument('class', None)
        instance = self.get_argument('instance', "*")
        recipient = self.get_argument('recipient', "*")
        startdate = self.get_argument('startdate', "0") # change later to 2 weeks ago
        enddate = self.get_argument('enddate', str(1000*2**35)) # if longpolling, should not have end date
        longpoll = self.get_argument('longpoll', "False")
        #TODO: do input validation on arguments
        if class_name is not None:
            sub = Subscription(class_name=class_name, instance=instance, recipient=recipient)
        else:
            sub = self.current_user
        zephyrs = Zephyr.objects.filter(sub.get_filter(), date__gt=datetime.datetime.fromtimestamp(float(startdate)/1000),
                date__lt=datetime.datetime.fromtimestamp(float(enddate)/1000))

        if len(zephyrs) == 0 and longpoll.lower() == "true":
            MessageWaitor.wait_for_messages(self,sub)
        else:
            self.write_zephyrs(zephyrs)

    def write_zephyrs(self, zephyrs):
        response = []
        for zephyr in zephyrs:
            totalMilliSeconds = int(math.ceil((time.mktime(zephyr.date.timetuple()) + zephyr.date.microsecond/1e6)*1000))
            values = {
                    'id': zephyr.id,
                    'message': zephyr.message,
                    'sender': zephyr.sender,
                    'date': totalMilliSeconds,
                    'class': zephyr.dst.class_name,
                    'instance': zephyr.dst.instance,
                    'recipient': zephyr.dst.recipient,
                    'signature': zephyr.signature
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
        class_name = self.get_argument('class', 'message').encode("utf-8")
        instance = self.get_argument('instance', 'personal').encode("utf-8")
        recipient = self.get_argument('recipient', '').encode("utf-8")
        signature = self.get_argument('signature', None)
        message = self.get_argument('message', '').encode("utf-8")
        username = self.current_user.username
        if signature is not None:
            signature += ") ("
        else:
            signature = ""
        signature += django.conf.settings.SIGNATURE or ""
        signature = signature.encode("utf-8")
        log("Send " + class_name + " " + instance + " " + recipient + " " + username.encode("utf-8") + " " + message)
        zephyr.ZNotice(cls=class_name,
                instance=instance,
                recipient=recipient,
                message=signature+'\x00'+message+'\n',
                sender=username if '@' in username else username + '@ATHENA.MIT.EDU').send()

class NewZephyrHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        z_id = self.get_argument('id', default=0)
        if z_id != None and z_id > 0:
            z = Zephyr.objects.filter(id=z_id)
            MessageWaitor.new_message(z[0])
#class NewZephyrHandler(threading.Thread):
#    def run(self):
#        while True:
#            loadZephyrOutput= readZephyrProc.stdout.readline()
#            log(loadZephyrOutput)
#            if loadZephyrOutput != '':
#                log("Received " + loadZephyrOutput)
#                z_id = int(loadZephyrOutput)
#                if z_id != None and z_id > 0:
#                    z = Zephyr.objects.filter(id=z_id)
#                    try:
#                        MessageWaitor.new_message(z[0])
#                    except:
#                        print("Zephyr " + str(z_id) + " does not exist")
#            time.sleep(1)

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
                } for sub in user.subscriptions.all()],
            "data": user.js_data
            }))

    @tornado.web.authenticated
    def post(self):
        user = self.current_user
        action = self.get_argument('action').lower()
        if action == 'subscribe' or action == 'unsubscribe':
            class_name = self.get_argument('class', 'message').lower()
            instance = self.get_argument('instance', '*').lower()
            recipient = self.get_argument('recipient', '*').lower()
            sub, created = Subscription.objects.get_or_create(class_name=class_name, instance=instance, recipient=recipient)
            if action == 'subscribe':
                user.subscriptions.add(sub)
                if created:
                    log("Subscribe " + str(sub))
                    zephyrLoader.addSubscription(sub)
            else:
                user.subscriptions.remove(sub)
            self.set_header('Content-Type', 'text/plain')
            self.write(simplejson.dumps({
                "class": sub.class_name,
                "instance": sub.instance,
                "recipient": sub.recipient
                }))
        elif action == 'save_data':
            user.js_data = self.get_argument('data')
            user.save()
            self.set_header('Content-Type', 'text/plain')
            self.write(user.js_data)

# Writes debuging messages to logfile
def log(msg):
    datestr = datetime.datetime.now().strftime("[%m/%d %H:%M]")
    if LOGFILE_NAME is not None:
        logfile = open(LOGFILE_NAME, "a")
        logfile.write(datestr + " " + msg + "\n")
        logfile.close()
    else:
        print datestr, msg

def sendmail(recipient, subject, message):
    msg = email.mime.text.MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = django.conf.settings.EXCEPTIONS_FROM
    msg['To'] = recipient
    s = smtplib.SMTP('outgoing.mit.edu')
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()

def excepthook(type, value, tb):
    msg = "".join(traceback.format_exception(type, value, tb))
    log(msg)
    if django.conf.settings.EXCEPTIONS_TO is not None:
        sendmail(django.conf.settings.EXCEPTIONS_TO, "ZephyrPlus exception", msg)

def installThreadExcepthook():
    """
    Workaround for sys.excepthook thread bug
    http://spyced.blogspot.com/2007/06/workaround-for-sysexcepthook-bug.html
    Call once from __main__ before creating any threads.
    """
    init_old = threading.Thread.__init__
    def init(self, *args, **kwargs):
        init_old(self, *args, **kwargs)
        run_old = self.run
        def run_with_except_hook(*args, **kw):
            try:
                run_old(*args, **kw)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                sys.excepthook(*sys.exc_info())
        self.run = run_with_except_hook
    threading.Thread.__init__ = init


settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": django.conf.settings.SECRET_KEY,
        "login_url": "/login",
        "xsrf_cookies": False,
        "debug": True,
        }

application = tornado.web.Application([
        (r"/chat", ChatUpdateHandler),
        (r"/update", NewZephyrHandler),
        (r"/login", CertsLoginHandler),
        (r"/logout", LogoutHandler),
        (r"/user", UserHandler),
        (r"/", MainPageHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": settings["static_path"]}),
        (r"/admin/usermorph", StupidLoginHandler),
        ], **settings)

class WebServer(threading.Thread):
    def run(self):
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8888)
        tornado.ioloop.IOLoop.instance().start()

def main():
    if django.conf.settings.DEBUG:
        log("WARNING: DEBUG is enabled. Django is storing all SQL queries. You will run out of memory...")
        sys.stderr.write("WARNING: DEBUG is enabled. Django is storing all SQL queries. You will run out of memory...\n")
    
    # Install custom excepthook to email us on exceptions
    sys.excepthook=excepthook
    installThreadExcepthook()

    # Log our pid so another process can watch mem
    log("Starting tornado server...")
    # Start our listener process
    global zephyrLoader
    zephyrLoader = loadZephyrs.ZephyrLoader()
    zephyrLoader.start()

    try:
        WebServer().run() # Don't do multithreading for now, just get a stable working website
    finally:
        zephyrLoader.stop = True

if __name__ == "__main__":
    main()
# vim: set expandtab:
