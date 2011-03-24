# -*- coding: utf-8 -*-
import re

from datetime import datetime, timedelta
from httplib2 import Http
from lxml import objectify
from urllib import urlencode

from django.utils.encoding import smart_str

from . import BaseSource, Product


class SourceClass(BaseSource):
    def request(self, xml):
        response, content = Http().request("http://www.elocationdevoitures.fr/service/ServiceRequest.do?%s" % urlencode({'xml': xml}))
        return objectify.fromstring(content)
    
    def build_xml(self, params):
        xml = """<SearchRQ>
            <Credentials username="eloue_fr" password="eloue" remoteIp="46.51.172.206" />
            <PickUp>
             <Location id="%(location)s" />
             <Date year="%(pickup_year)d" month="%(pickup_month)d" day="%(pickup_day)d" hour="%(pickup_hour)d" minute="%(pickup_minute)d"/>
            </PickUp>
            <DropOff>
             <Location id="%(location)s" />
             <Date year="%(dropoff_year)d" month="%(dropoff_month)d" day="%(dropoff_day)d" hour="%(dropoff_hour)d" minute="%(dropoff_minute)d"/>
            </DropOff>
            <DriverAge>%(age)d</DriverAge>
           </SearchRQ>""" % params
        return re.sub(r'\n\s*', '', xml)

    def get_cities(self):
        cities = []
        for country in ['France - Continent', 'France - Corse']:
            root = self.request("""<PickUpCityListRQ><Credentials username="eloue_fr" password="eloue" remoteIp="46.51.172.206" /><Country>%(country)s</Country></PickUpCityListRQ>""" % {'country': country})
            for city in root.xpath('//City'):
                cities.append({'country': country, 'city': smart_str(city.pyval)})
        return cities
    
    def get_locations(self):
        locations = []
        for city in self.get_cities():
            root = self.request("""<PickUpLocationListRQ><Credentials username="eloue_fr" password="eloue" remoteIp="46.51.172.206" /><Country>%(country)s</Country><City>%(city)s</City></PickUpLocationListRQ>""" % city)
            for location in root.xpath('//Location'):
                locations.append({
                    'id': location.get('id'),
                    'name': location.pyval,
                    'city': city['city'],
                    'country': city['country'],
                })
        return locations
    
    def get_docs(self):
        """
        The format of the return is as follows:
        
        {'categories_exact': ['auto-et-moto', 'voiture'], 
        'owner_exact': 'elocationdevoitures', 
        'description': u"Pour les couples ou les petites familles qui souhaitent un v\xe9hicule avec espace suppl\xe9mentaire, cette quatre-portes interm\xe9diaire avec l'air conditionn\xe9 sera parfaite ", 
        'text': u"Citroen C5 Pour les couples ou les petites familles qui souhaitent un v\xe9hicule avec espace suppl\xe9mentaire, cette quatre-portes interm\xe9diaire avec l'air conditionn\xe9 sera parfaite ", 
        'price': 114.04, 
        'django_ct': 'products.product', 
        'owner': 'elocationdevoitures', 
        'lat': 43.92148, 
        'lng': 4.786, 
        'id': 'source.jigsaw.53356827', 
        'categories': ['auto-et-moto', 'voiture'], 
        'city': 'Avignon Gare de TGV', 
        'django_id': 'jigsaw.53356827', 
        'sites_exact': [1, 2, 3], 
        'url': 'http://www.elocationdevoitures.fr/SearchResults.do?country=France - Continent&city=Avignon&location=3052&dropLocation=3052&puYear=2011&puMonth=3&puDay=31&puHour=12&puMinute=20&doYear=2011&doMonth=4&doDay=1&doHour=12&doMinute=30&driversAge=25&affiliateCode=eloue_fr', 
        'created_at': datetime.datetime(2011, 3, 24, 11, 2, 6, 188509), 
        'sites': [1, 2, 3], 
        'summary': 'Citroen C5', 
        'owner_url': 'http://www.elocationdevoitures.fr/', 
        'price_exact': 114.04, 
        'thumbnail': 'https://media.e-loue.com/proxy/2205a9a908df217c61657df0d8f85fc5a86734bf?url=http://www.elocationdevoitures.fr/images/car_images/D/citroen_c5.jpg'}
        """
        print "get voiture docs called"
        docs = []
        pickup_date = datetime.now() + timedelta(days=7)
        dropoff_date = pickup_date + timedelta(days=1)
        for location in self.get_locations():
            root = self.request(self.build_xml({
                'age': 25, 'location': location['id'],
                'pickup_year': pickup_date.year, 'pickup_month': pickup_date.month, 'pickup_day': pickup_date.day, 'pickup_hour': 12, 'pickup_minute': 30,
                'dropoff_year': dropoff_date.year, 'dropoff_month': dropoff_date.month, 'dropoff_day': dropoff_date.day, 'dropoff_hour': 12, 'dropoff_minute': 30,
            }))
            for match in root.xpath('//Match'):
                lat, lon = BaseSource().get_coordinates(match.Route.PickUp.Location.get('locName'))
                docs.append(Product({
                    'id': '%s.%s' % (SourceClass().get_prefix(), match.Vehicle.get('id')),
                    'summary': match.Vehicle.Name.pyval,
                    'description': match.Vehicle.Description.pyval,
                    'categories': ['auto-et-moto', 'voiture'],
                    'lat': lat, 'lng': lon,
                    'city': match.Route.PickUp.Location.get('locName'),
                    'price': match.Price.pyval,
                    'owner': 'elocationdevoitures',
                    'owner_url': 'http://www.elocationdevoitures.fr/',
                    'url': 'http://www.elocationdevoitures.fr/SearchResults.do?country=%(country)s&city=%(city)s&location=%(location)s&dropLocation=%(location)s&puYear=%(pickup_year)d&puMonth=%(pickup_month)d&puDay=%(pickup_day)d&puHour=12&puMinute=20&doYear=%(dropoff_year)d&doMonth=%(dropoff_month)d&doDay=%(dropoff_day)d&doHour=12&doMinute=30&driversAge=%(age)d&affiliateCode=eloue_fr' % {
                        'age': 25, 'location': location['id'], 'city': location['city'], 'country': location['country'],
                        'pickup_year': pickup_date.year, 'pickup_month': pickup_date.month, 'pickup_day': pickup_date.day, 'pickup_hour': 12, 'pickup_minute': 30,
                        'dropoff_year': dropoff_date.year, 'dropoff_month': dropoff_date.month, 'dropoff_day': dropoff_date.day, 'dropoff_hour': 12, 'dropoff_minute': 30,
                    },
                    'thumbnail': match.Vehicle.ImageURL.pyval,
                    'django_id': 'jigsaw.%s' % match.Vehicle.get('id')
                }))
        print "######### docs #######", docs
        return docs
    
    def get_prefix(self):
        return 'source.jigsaw'
    
