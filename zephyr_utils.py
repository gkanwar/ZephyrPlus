import base64
import hashlib
import hmac
import logging
import os
from random import SystemRandom
import sys
from threading import Lock
import time
import zephyr

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from chat.models import Zephyr, Subscription
from django import db
import django.conf


CLOCK_SKEW_MAX_S = 120

random = SystemRandom()
logger = logging.getLogger('zephyrplus.zephyr_utils')


def send_zephyr(cls, instance, recipient, sender, message, signature):
    '''Sends a Zephyr. This handles encoding everything as utf-8 and
    adding a hmac.'''

    def encode(u):
        return u.encode('utf-8')

    if hasattr(zephyr.ZNotice, 'charset'):
        fields = [signature, message]
    else:
        fields = [encode(signature), encode(message)]

    z = zephyr.ZNotice(
        cls=encode(cls),
        instance=encode(instance),
        recipient=encode(recipient),
        sender=encode(sender),
        fields=fields,
        format='http://zephyr.1ts.org/wiki/df',
        auth=False
    )

    _add_hmac(z)
    z.send()


def receive_zephyr():
    '''Receives a Zephyr and decodes strings to unicode.'''
    z = zephyr.receive()
    if z is None:
        return

    z.auth = z.auth or _check_hmac(z)

    if hasattr(z, 'charset') and z.charset.lower() != 'unknown':
        charset = z.charset.lower()
    else:
        charset = 'utf-8'

    def decode(s):
        try:
            return s.decode(charset)
        except UnicodeDecodeError as e:
            logger.warning(u'Failed to decode string %r' % s, exc_info=True)
            return s.decode(charset, 'replace')

    return zephyr.ZNotice(
        uid=z.uid,
        kind=z.kind,
        auth=z.auth,
        cls=decode(z.cls),
        instance=decode(z.instance),
        recipient=decode(z.recipient),
        sender=decode(z.sender),
        opcode=decode(z.opcode),
        message=decode(z.message)
    )


def _add_hmac(z):
    while len(z.fields) < 2:
        z.fields = [''] + z.fields
    z.fields.append('%.6f' % (time.time() + random.random() / 100.))
    z.fields.append(_hmac_znotice(z))


_seen_times = set()
_seen_times_lock = Lock()


def _check_hmac(z):
    '''Pops the hmac off the message and checks if it is valid.'''
    if len(z.fields) < 4:
        return False

    received_hmac = z.fields.pop()
    if ((hasattr(hmac, 'compare_digest') and
         not hmac.compare_digest(received_hmac, _hmac_znotice(z)))
        or not received_hmac == _hmac_znotice(z)):
        logger.debug('hmac mismatch: %s', z.__dict__)
        return False

    try:
        sent_time = float(z.fields.pop())
    except ValueError:
        logger.debug('bad time format: %s', z.__dict__)
        return False
    current_time = time.time()
    if current_time - sent_time > CLOCK_SKEW_MAX_S:
        logger.debug('zephyr too old: %s', z.__dict__)
        return False

    with _seen_times_lock:
        global _seen_times
        if sent_time in _seen_times:
            logger.debug('duplicate zephyr: %s', z.__dict__)
            return False
        _seen_times.add(sent_time)
        if random.random() < 0.001 and \
           current_time - min(_seen_times) > CLOCK_SKEW_MAX_S:
            _seen_times = {t for t in _seen_times
                           if current_time - t < CLOCK_SKEW_MAX_S}

    # Overwrite the UID because the original UID isn't authenticated.
    z.uid.address = received_hmac
    z.uid.time = sent_time

    return True


def _hmac_znotice(z):
    return _compute_hmac(
        z.kind,
        z.cls,
        z.instance,
        z.recipient or '',
        z.sender,
        z.opcode or '',
        z.message,
    )


def _compute_hmac(*fields):
    builder = hmac.new(django.conf.settings.SECRET_KEY, digestmod=hashlib.sha256)
    for field in fields:
        s = field.encode('utf-8') if isinstance(field, unicode) else str(field)
        builder.update(str(len(s)))
        builder.update(' ')
        builder.update(s)
    digest = builder.digest()
    return base64.b64encode(digest)
