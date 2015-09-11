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
import functools

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
from django import db

# Auth
from oidc import OidcMixin

LOGFILE_NAME = django.conf.settings.TORNADO_LOGFILE_NAME

class BaseHandler(tornado.web.RequestHandler):
    def login(self, username):
        username = username.lower()
        if username.endswith("@mit.edu"):
            username = username.split("@")[0]
        self.set_secure_cookie("user", username, expires_days=31)

    def get_current_user(self):
        debug_log("get_current_user")
        username = self.get_secure_cookie("user")
        if username is not None:
            account, created = Account.objects.get_or_create(username=username)
            if created:
                account.subscriptions.add(Subscription.objects.get_or_create(class_name="lobby", instance="*", recipient="*")[0])
                account.subscriptions.add(Subscription.objects.get_or_create(class_name=username, instance="*", recipient="*")[0])
                zephyrLoader.addSubscription(Subscription.objects.get_or_create(class_name=username, instance="*", recipient="*")[0])
            debug_log("get_current_user done %s"%username)
            return account
        return None

def same_origin(method):
    """Require that the request comes from the same origin as the
    resource"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        # We should really be using CSRF tokens, but for now, this is better
        # than nothing
        our_origin = django.conf.settings.ORIGIN or \
            "%s://%s" % (self.request.protocol, self.request.host)
        their_origin = ""
        if "Origin" in self.request.headers:
            their_origin = self.request.headers["Origin"]
        elif "Referer" in self.request.headers:
            their_origin = "/".join(
                self.request.headers["Referer"].split("/", 3)[:3])
        if our_origin != their_origin:
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper

class MainPageHandler(BaseHandler):
    def get(self, *args):
        if self.current_user is None:
            self.render("templates/login.html", next=self.request.uri)
        else:
            self.render("templates/index.html")

class CertsLoginHandler(BaseHandler, tornado.auth.OpenIdMixin):
    _OPENID_ENDPOINT = "https://garywang.scripts.mit.edu/openid/login.py"

    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("openid.mode", False):
            user = None
            user = yield self.get_authenticated_user()
            if user is None or "email" not in user:
                self.redirect("/")
                return
            self.login(user["email"])
            self.redirect(self.get_argument("next", "/"))
        else:
            yield self.authenticate_redirect()

class OidcLoginHandler(BaseHandler, OidcMixin):
    _OIDC_AUTHORIZATION_ENDPOINT = django.conf.settings.OIDC_AUTH
    _OIDC_TOKEN_ENDPOINT = django.conf.settings.OIDC_TOKEN
    _OIDC_USERINFO_ENDPOINT = django.conf.settings.OIDC_USERINFO
    _OIDC_CLIENT_ID = django.conf.settings.OIDC_CLIENT_ID
    _OIDC_CLIENT_SECRET = django.conf.settings.OIDC_CLIENT_SECRET

    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("code", False):
            try:
                user = yield self.get_authenticated_user()
            except tornado.auth.AuthError as e:
                log(repr(e))
                self.redirect("/")
                return
            if user is None or "email" not in user:
                log("OIDC email missing")
                self.redirect("/")
                return
            self.login(user["email"])
            self.redirect(self.get_argument("next", "/"))
        elif self.get_argument("error", False):
            log("OIDC error: %s: %s" % (self.get_argument("error"),
                                        self.get_argument("error_description", "")))
            self.redirect("/")
        else:
            yield self.authorize_redirect()

class StupidLoginHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        if self.current_user.username in ['garywang', 'gurtej', 'mikewu', 'timyang', 'zeidman']:
            username = self.get_argument("username")
            self.login(username)
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
        debug_log("get")
        class_name=self.get_argument('class', None)
        instance = self.get_argument('instance', "*")
        recipient = self.get_argument('recipient', "*")
        startdate = self.get_argument('startdate', "0") # change later to 2 weeks ago
        enddate = self.get_argument('enddate', str(1000*2**35)) # if longpolling, should not have end date
        longpoll = self.get_argument('longpoll', "False")
        #TODO: do input validation on arguments

        startdate = datetime.datetime.fromtimestamp(float(startdate)/1000)
        enddate = datetime.datetime.fromtimestamp(float(enddate)/1000)

        if class_name is not None:
            sub = Subscription.objects.get_or_create(class_name=class_name, instance=instance, recipient=recipient)[0]
        else:
            sub = self.current_user

        debug_log("get got sub")
        zephyrs = Zephyr.objects.filter(sub.get_filter(),
                                        date__gt=startdate,
                                        date__lt=enddate).select_related('dst').order_by('id')
        debug_log("get got zephyrs")

        if enddate > datetime.datetime.now():
            simple_zephyrs = Zephyr.objects.filter(sub.get_filter()).order_by('-id')
            exists = simple_zephyrs.exists() and simple_zephyrs[0].date > startdate
        else:
            exists = zephyrs.exists()

        if not exists and longpoll.lower() == "true":
            debug_log("get not zephyr.exists")
            MessageWaitor.wait_for_messages(self,sub)
        else:
            debug_log("get zephyr.exists")
            self.write_zephyrs(zephyrs)
        debug_log("get done")

    def write_zephyrs(self, zephyrs):
        debug_log("write_zephyrs")
        response = []
        last_id = 0
        for zephyr in zephyrs:
            if zephyr.id == last_id:
                continue
            last_id = zephyr.id
            debug_log(str(last_id))
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
            if len(response) > 5000:
                break
        self.set_header('Content-Type', 'text/plain')
        self.write(simplejson.dumps(response))
        self.finish()
        debug_log("write_zephyrs done")

    def on_connection_close(self):
        debug_log("on_connection_close")
        for waitee in MessageWaitor.waiters:
            if waitee[0] == self:
                MessageWaitor.waiters.remove(waitee)
        debug_log("on_connection_close done")

    @tornado.web.authenticated
    @same_origin
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
                sender=username if '@' in username else username + '@ATHENA.MIT.EDU',
                format='http://zephyr.1ts.org/wiki/df').send()

class NewZephyrHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        debug_log("new zephyr start")
        z_id = self.get_argument('id', default=0)
        if z_id != None and z_id > 0:
            z = Zephyr.objects.filter(id=z_id)
            MessageWaitor.new_message(z[0])
        debug_log("new zephyr end")
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
    @same_origin
    def post(self):
        user = self.current_user
        action = self.get_argument('action').lower()
        if action == 'subscribe' or action == 'unsubscribe':
            class_name = self.get_argument('class', 'message').lower()
            instance = self.get_argument('instance', '*').lower()
            recipient = '*'
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
    datestr = datetime.datetime.now().strftime("[%m/%d %H:%M:%S.%f]")
    if LOGFILE_NAME is not None:
        logfile = open(LOGFILE_NAME, "a")
        logfile.write(datestr + " " + str(msg) + "\n")
        logfile.close()
    else:
        print datestr, msg

def debug_log(msg):
    #log(msg)
    #print datetime.datetime.now(), msg
    pass

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
        (r"/oidclogin", OidcLoginHandler),
        (r"/logout", LogoutHandler),
        (r"/user", UserHandler),
        (r"/(class/.+)?", MainPageHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": settings["static_path"]}),
        (r"/admin/usermorph", StupidLoginHandler),
        ], **settings)

class WebServer(threading.Thread):
    def run(self):
        http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
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
