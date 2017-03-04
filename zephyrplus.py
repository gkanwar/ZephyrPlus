#! /usr/bin/env python

# Tornado Server
import tornado.httpserver, tornado.ioloop, tornado.web, tornado.auth

# Multiprocesses
import os, subprocess, threading, thread

# Utility libraries
import datetime, time
import math
import signal
import simplejson
import sys
import functools

# Logging and debugging
import logging
import traceback
import email, smtplib

# Zephyr Libraries
import zephyr
import loadZephyrs
from zephyr_utils import send_zephyr
zephyr.init()

# Django Library
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django
django.setup()
from chat.models import Zephyr, Subscription, Account
import django.conf
from django import db

# Auth
from oidc import OidcMixin


logger = logging.getLogger('zephyrplus.main')


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
                zephyrLoader.subscribe(username)
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
                logger.warn(u'OIDC login failed', exc_info=True)
                self.redirect("/")
                return
            if user is None or "email" not in user:
                logger.warn(u'OIDC email missing')
                self.redirect("/")
                return
            self.login(user["email"])
            self.redirect(self.get_argument("next", "/"))
        elif self.get_argument("error", False):
            logger.warn(u'OIDC error: %s: %s',
                        self.get_argument('error'),
                        self.get_argument('error_description', ''))
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
        class_name = self.get_argument('class', u'message')
        instance = self.get_argument('instance', u'personal')
        recipient = self.get_argument('recipient', u'')
        signature = self.get_argument('signature', None)
        message = self.get_argument('message', u'')
        username = self.current_user.username
        if signature is not None:
            signature += u') ('
        else:
            signature = u''
        signature += django.conf.settings.SIGNATURE or u''
        logger.info(u'Send %s %s %s %s %s', class_name, instance, recipient, username, message)
        send_zephyr(cls=class_name,
                    instance=instance,
                    recipient=recipient,
                    sender=username if '@' in username else username + '@ATHENA.MIT.EDU',
                    message=message,
                    signature=signature)


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
            "data": user.js_data,
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
                    logger.info('Subscribe %s', sub)
                    zephyrLoader.subscribe(class_name)
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


def debug_log(msg):
    logger.debug(msg)


def add_signal_handler(sig, server):
    '''Adds a signal handler to shut down the server and IOLoop.'''

    loop = tornado.ioloop.IOLoop.instance()

    @tornado.gen.coroutine
    def shutdown():
        server.stop()
        yield tornado.gen.sleep(2)
        loop.stop()

    def handler(sig, frame):
        logger.info('Received signal %s, shutting down\n%s', sig,
                    ''.join(traceback.format_stack(frame)))
        loop.add_callback_from_signal(shutdown)

    signal.signal(sig, handler)


settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": django.conf.settings.SECRET_KEY,
    "login_url": "/login",
    "xsrf_cookies": False,
    "debug": True,
}

application = tornado.web.Application([
    (r"/chat", ChatUpdateHandler),
    (r"/login", CertsLoginHandler),
    (r"/oidclogin", OidcLoginHandler),
    (r"/logout", LogoutHandler),
    (r"/user", UserHandler),
    (r"/(class/.+)?", MainPageHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": settings["static_path"]}),
    (r"/admin/usermorph", StupidLoginHandler),
], **settings)


@tornado.gen.coroutine
def start():
    if django.conf.settings.DEBUG:
        logger.warning(u'DEBUG is enabled. Django is storing all SQL queries. You will run out of memory...')

    logger.info(u'Starting tornado server...')

    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    add_signal_handler(signal.SIGINT, http_server)
    add_signal_handler(signal.SIGTERM, http_server)

    # Start our listener process
    global zephyrLoader
    zephyrLoader = loadZephyrs.ZephyrLoader(MessageWaitor.new_message)
    yield zephyrLoader.start()

    logger.info(u'Server listening on port %s', django.conf.settings.PORT)
    http_server.listen(django.conf.settings.PORT)


def main():
    try:
        start().add_done_callback(lambda fut: fut.result())
        IOLoop.current().start()
    except Exception:
        logger.critical(u'Uncaught exception, exiting!', exc_info=True)


if __name__ == "__main__":
    main()

# vim: set expandtab:
