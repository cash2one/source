# -*- coding: utf-8 -*-
import re

from datetime import datetime, timedelta
from httplib2 import Http
from lxml import objectify
from urllib import urlencode

from django.utils.encoding import smart_str

from . import BaseSource, meta_class


class SourceClass(BaseSource):
    _meta = meta_class('sources', 'jigsaw')

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
        pickup_date = datetime.now() + timedelta(days=7)
        dropoff_date = pickup_date + timedelta(days=1)
        for location in self.get_locations():
            root = self.request(self.build_xml({
                'age': 25, 'location': location['id'],
                'pickup_year': pickup_date.year, 'pickup_month': pickup_date.month, 'pickup_day': pickup_date.day, 'pickup_hour': 12, 'pickup_minute': 30,
                'dropoff_year': dropoff_date.year, 'dropoff_month': dropoff_date.month, 'dropoff_day': dropoff_date.day, 'dropoff_hour': 12, 'dropoff_minute': 30,
            }))
            for match in root.xpath('//Match'):
                pickup = match.Route.PickUp
                vehicle = match.Vehicle
                lat, lon = self.get_coordinates(pickup.Location.get('locName'))
                yield self.make_product({
                    'summary': vehicle.Name.pyval,
                    'description': vehicle.Description.pyval,
                    'categories': ['auto-et-moto', 'voiture'],
                    'location': '%s,%s' % (lon, lat),
                    'city': pickup.Location.get('locName'),
                    'price': match.Price.pyval,
                    'owner': 'elocationdevoitures',
                    'owner_url': 'http://www.elocationdevoitures.fr/',
                    'url': 'http://www.elocationdevoitures.fr/SearchResults.do?country=%(country)s&city=%(city)s&location=%(location)s&dropLocation=%(location)s&puYear=%(pickup_year)d&puMonth=%(pickup_month)d&puDay=%(pickup_day)d&puHour=12&puMinute=20&doYear=%(dropoff_year)d&doMonth=%(dropoff_month)d&doDay=%(dropoff_day)d&doHour=12&doMinute=30&driversAge=%(age)d&affiliateCode=eloue_fr' % {
                        'age': 25, 'location': location['id'], 'city': location['city'], 'country': location['country'],
                        'pickup_year': pickup_date.year, 'pickup_month': pickup_date.month, 'pickup_day': pickup_date.day, 'pickup_hour': 12, 'pickup_minute': 30,
                        'dropoff_year': dropoff_date.year, 'dropoff_month': dropoff_date.month, 'dropoff_day': dropoff_date.day, 'dropoff_hour': 12, 'dropoff_minute': 30,
                    },
                    'thumbnail': vehicle.ImageURL.pyval,
                }, pk=vehicle.get('id'))
