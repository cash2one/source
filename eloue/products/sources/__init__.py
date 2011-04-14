# -*- coding: utf-8 -*-
import hashlib
import hmac
import logbook

from datetime import datetime
from pysolr import Solr
from multiprocessing import Pool, cpu_count
from urlparse import urlparse, urljoin
from itertools import islice

from django.conf import settings
from django.utils import importlib

from eloue.geocoder import GoogleGeocoder
from eloue.utils import generate_camo_url

log = logbook.Logger('eloue.rent.sources')
SOURCES = getattr(settings, 'AFFILIATION_SOURCES', ['skiplanet', 'lv'])
BATCHSIZE = 20 # getattr(settings, 'AFFILIATION_BATCHSIZE', 10)

CAMO_URL = getattr(settings, 'CAMO_URL', 'https://media.e-loue.com/proxy/')
CAMO_KEY = getattr(settings, 'CAMO_KEY')


class Product(dict):
    def __init__(self, *args, **kwargs):  # TODO: Need improvement
        super(Product, self).__init__(*args, **kwargs)
        self.update({
            'created_at': datetime.now(),
            'django_ct': 'products.product',
            'text': "%s %s" % (self['summary'], self['description']),
            'categories_exact': self['categories'],
            'owner_exact': self['owner'],
            'price_exact': self['price'],
            'sites': settings.DEFAULT_SITES,
            'sites_exact': settings.DEFAULT_SITES,
            'thumbnail': generate_camo_url(self['thumbnail']) if 'thumbnail' in self and self['thumbnail'] else None,
        })

    def _camo_url(self, url):
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


class BaseSource(object):
    processes = 2 * cpu_count()

    def get_pool(self):
        return Pool(processes=BaseSource.processes)

    def get_prefix(self):
        raise NotImplementedError

    def get_docs(self):
        raise NotImplementedError

    def get_coordinates(self, location):
        name, (lat, lon), radius = GoogleGeocoder().geocode(location)
        return lat, lon

class SourceManager(object):
    solr = Solr(settings.HAYSTACK_SOLR_URL, timeout=900)

    def __init__(self):
        self.sources = []
        for source in SOURCES:
            mod = importlib.import_module('eloue.products.sources.%s' % source)
            self.sources.append(getattr(mod, 'SourceClass')())

    def get_docs(self):
        for source in self.sources:
            for el in source.get_docs():
                yield el

    def index_docs(self):

        def next_docs():
            docs = self.get_docs()
            while True:
                l = list(islice(docs, BATCHSIZE))
                if l: yield l
                else: return

        for batch in next_docs():
            log.info("appending batch")
            self.__class__.solr.add(batch)
            self.__class__.solr.commit()


    def remove_docs(self):
        for source in self.sources:
            self.__class__.solr.delete(q="id:%s.*" % source.get_prefix())
            self.__class__.solr.commit()


if __name__ == '__main__':
    manager = SourceManager()
    manager.remove_docs()
    manager.index_docs()
