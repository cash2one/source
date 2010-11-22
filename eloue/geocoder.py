# -*- coding: utf-8 -*-
import hashlib
import urllib

from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import smart_str
from django.utils import simplejson

GOOGLE_API_KEY = getattr(settings, 'GOOGLE_API_KEY', 'ABQIAAAA7bPNcG5t1-bTyW9iNmI-jRRqVDjnV4vohYMgEqqi0RF2UFYT-xSSwfcv2yfC-sACkmL4FuG-A_bScQ')


class Geocoder(object):
    def __init__(self, use_cache=True):
        self.use_cache = use_cache
    
    def geocode(self, location):
        location = self.format_place(location)
        name, coordinates, cache_hit = None, None, False
        if self.use_cache:
            coordinates = cache.get('location:%s' % self.hash_key(location))
            cache_hit = True
            
        if coordinates == None:
            name, coordinates = self._geocode(location)
        
        if not cache_hit and self.use_cache:
            cache.set('location:%s' % self.hash_key(location), coordinates, 0)
        return name, coordinates
    
    def _geocode(self, location):
        raise NotImplementedError
    
    def format_place(self, location):
        return smart_str(location.strip().lower())
    
    def hash_key(self, location):
        return hashlib.md5(location).hexdigest()
    

class GoogleGeocoder(Geocoder):
    # http://code.google.com/apis/maps/documentation/geocoding/index.html
    def _geocode(self, location):
        json = simplejson.load(urllib.urlopen(
            'http://maps.googleapis.com/maps/api/geocode/json?' + urllib.urlencode({
                'address': location,
                'oe': 'utf8',
                'sensor': 'false',
                'region': 'fr',
                'key': GOOGLE_API_KEY
            })
        ))
        try:
            lon = json['results'][0]['geometry']['location']['lng']
            lat = json['results'][0]['geometry']['location']['lat']
        except (KeyError, IndexError):
            return None, (None, None)
        name = json['results'][0]['formatted_address']
        return name, (lat, lon)
    
