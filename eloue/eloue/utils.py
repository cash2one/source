# -*- coding: utf-8 -*-
import hashlib
import hmac
import locale

from decimal import ROUND_UP, ROUND_DOWN, Decimal as D
from urlparse import urlparse, urljoin

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlquote
from django.utils import translation
from django.forms.util import ErrorList

try:
    import json
except ImportErorr:
    try:
        import simplejson as json
    except ImportErorr:
        from django.utils import simplejson as json

CAMO_URL = getattr(settings, 'CAMO_URL', 'https://media.e-loue.com/proxy/')
CAMO_KEY = getattr(settings, 'CAMO_KEY')

USE_HTTPS = getattr(settings, 'USE_HTTPS', True)


def form_errors_append(form, field_name, message):
    '''
    Add an ValidationError to a field (instead of __all__) during Form.clean():

    class MyForm(forms.Form):
        def clean(self):
            value_a=self.cleaned_data['value_a']
            value_b=self.cleaned_data['value_b']
            if value_a==... and value_b==...:
                formutils.errors_append(self, 'value_a', u'Value A must be ... if value B is ...')
            return self.cleaned_data
    '''
    assert form.fields.has_key(field_name), field_name
    error_list=form.errors.get(field_name)
    
    if error_list is None:
        error_list=ErrorList()
        form.errors[field_name]=error_list
    elif error_list[-1]==message: #FIXME, unicode isn't comparable with str, message in error list cannot work so only two messages are allowed
        return 
    error_list.append(message)


def cache_key(fragment_name, *args):
    hasher = hashlib.md5(u':'.join([urlquote(arg) for arg in args]))
    return 'template.cache.%s.%s' % (fragment_name, hasher.hexdigest())


def create_alternative_email(prefix, context, from_email, recipient_list):
    context.update({
        'site': Site.objects.get_current(),
        'protocol': "https" if USE_HTTPS else "http"
    })
    subject = render_to_string("%s_email_subject.txt" % prefix, context)
    text_content = render_to_string("%s_email.txt" % prefix, context)
    html_content = render_to_string("%s_email.html" % prefix, context)
    message = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    message.attach_alternative(html_content, "text/html")
    return message


def generate_camo_url(url):
    parts = urlparse(url)
    parts = {
        'scheme': parts.scheme,
        'hostname': parts.hostname,
        'path': parts.path if not parts.path.startswith('//') else parts.path[1:],
        'params': parts.params
    }
    url = urljoin("%(scheme)s://%(hostname)s" % parts, "%(path)s?%(params)s" % parts)
    digest = hmac.new(CAMO_KEY, url, hashlib.sha1).hexdigest()
    return "%s%s?url=%s" % (CAMO_URL, digest, url)


def currency(value):
    """It totally ignores currency linked with value."""
    old_locale = locale.getlocale()
    if settings.CONVERT_XPF:
        return "%s XPF" % D(value)
    try:
        new_locale = locale.normalize(translation.to_locale("%s.utf8" % translation.get_language()))
        locale.setlocale(locale.LC_ALL, new_locale)
        return locale.currency(D(value), True, True)
    except (TypeError, locale.Error):
        return D(value)
    finally:
        locale.setlocale(locale.LC_ALL, old_locale)


def convert_from_xpf(value):
    amount = value * D(settings.XPF_EXCHANGE_RATE)
    return amount.quantize(D("0.00"), rounding=ROUND_UP)

def convert_to_xpf(value):
    amount = value / D(settings.XPF_EXCHANGE_RATE)
    return amount.quantize(D("0.00"), rounding=ROUND_UP)

class Enum(object):
    """
    A small helper class for more readable enumerations,
    and compatible with Django's choice convention.

    >>> PERSON = Enum([
    ...   (100, 'NAME', 'Verbose name title'),
    ...   (200, 'AGE', 'Verbose age title')
    ... ])
    >>> PERSON.AGE
    200
    >>> PERSON[1]
    (200, 'Verbose age title')
    >>> PERSON['NAME']
    100
    >>> len(PERSON)
    2
    >>> (100, 'Verbose name title') in PERSON
    True
    """
    def __init__(self, enum_list):
        self.enum_list = [(item[0], item[2]) for item in enum_list]
        self.enum_list_prefixed = [(item[0], item[3] if len(item) > 3 else item[2]) for item in enum_list]
        self.enum_dict = dict([(item[1], item[0]) for item in enum_list])

    def __contains__(self, v):
        return (v in self.enum_list)

    def __len__(self):
        return len(self.enum_list)

    def __getitem__(self, v):
        if isinstance(v, basestring):
            return self.enum_dict[v]
        elif isinstance(v, int):
            return self.enum_list[v]

    def __getattr__(self, name):
        return self.enum_dict[name]

    def __iter__(self):
        return self.enum_list.__iter__()

    def keys(self):
        return self.enum_dict.keys()

    def values(self):
        return self.enum_dict.values()

    @property
    def prefixed(self):
        return dict(self.enum_list_prefixed)

    @property
    def reverted(self):
        return dict(zip(self.enum_dict.itervalues(), self.enum_dict.iterkeys()))