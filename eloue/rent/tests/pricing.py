# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from decimal import Decimal as D

from django.test import TestCase

from pyke.knowledge_engine import CanNotProve

from eloue.products.models import Product, UNIT
from eloue.rent.models import Booking


class BookingPriceTest(TestCase):
    fixtures = ['category', 'patron', 'address', 'price', 'product']
    
    def setUp(self):
        self.product = Product.objects.get(pk=1)
    
    def test_calculate_hours_price(self):
        started_at = datetime.now()
        ended_at = started_at + timedelta(0, 240)
        unit, price = Booking.calculate_price(self.product, started_at, ended_at)
        self.assertEquals(price, D('1.2'))
        self.assertEquals(unit, UNIT.HOUR)
    
    def test_calculate_week_end_price(self):
        started_at = datetime(2010, 9, 17, 9, 00)
        ended_at = started_at + timedelta(days=3)
        unit, price = Booking.calculate_price(self.product, started_at, ended_at)
        self.assertEquals(price, D('12'))
        self.assertEquals(unit, UNIT.WEEK_END)
    
    def test_calculate_day_price(self):
        started_at = datetime(2010, 9, 20, 9, 00)
        ended_at = started_at + timedelta(days=4)
        unit, price = Booking.calculate_price(self.product, started_at, ended_at)
        self.assertEquals(price, D('28'))
        self.assertEquals(unit, UNIT.DAY)
    
    def test_calculate_week_price(self):
        started_at = datetime.now()
        ended_at = started_at + timedelta(days=7)
        unit, price = Booking.calculate_price(self.product, started_at, ended_at)
        self.assertEquals(price, D('35'))
        self.assertEquals(unit, UNIT.WEEK)
    
    def test_calculate_two_weeks_price(self):
        started_at = datetime.now()
        ended_at = started_at + timedelta(days=14)
        unit, price = Booking.calculate_price(self.product, started_at, ended_at)
        self.assertEquals(price, D('56'))
        self.assertEquals(unit, UNIT.TWO_WEEKS)
    
    def test_calculate_leap_two_weeks(self):
        started_at = datetime(2011, 3, 4, 9)
        ended_at = started_at + timedelta(days=29)
        unit, price = Booking.calculate_price(self.product, started_at, ended_at)
        self.assertEquals(price, D('116'))
        self.assertEquals(unit, UNIT.TWO_WEEKS)
        started_at = datetime(2011, 3, 4, 9)
        ended_at = started_at + timedelta(days=30)
        unit, price = Booking.calculate_price(self.product, started_at, ended_at)
        self.assertEquals(price, D('120'))
        self.assertEquals(unit, UNIT.TWO_WEEKS)
    
    def test_calculate_leap_month(self):
        started_at = datetime(2011, 2, 4, 9)
        ended_at = started_at + timedelta(days=28)
        unit, price = Booking.calculate_price(self.product, started_at, ended_at)
        self.assertEquals(price, D('84'))
        self.assertEquals(unit, UNIT.MONTH)
    
    def test_calculate_month_price(self):
        started_at = datetime.now()
        ended_at = started_at + timedelta(days=45)
        unit, price = Booking.calculate_price(self.product, started_at, ended_at)
        self.assertEquals(price, D('135'))
        self.assertEquals(unit, UNIT.MONTH)
    
    def test_calculate_default_price(self):
        product = Product.objects.get(pk=2)
        started_at = datetime.now()
        ended_at = started_at + timedelta(days=45)
        unit, price = Booking.calculate_price(product, started_at, ended_at)
        self.assertEquals(price, D('315'))
        self.assertEquals(unit, UNIT.DAY)
    
    def test_calculate_hourly_price(self):
        product = Product.objects.get(pk=2)
        started_at = datetime.now()
        ended_at = started_at + timedelta(seconds=360)
        unit, price = Booking.calculate_price(product, started_at, ended_at)
        self.assertEquals(price, D('3.6'))
        self.assertEquals(unit, UNIT.HOUR)
    
    def test_calculate_two_week_price(self):
        product = Product.objects.get(pk=2)
        started_at = datetime.now()
        ended_at = started_at + timedelta(days=18)
        unit, price = Booking.calculate_price(product, started_at, ended_at)
        self.assertEquals(price, D('126'))
        self.assertEquals(unit, UNIT.TWO_WEEKS)
    
    def test_calculate_strict_day_price(self):
        product = Product.objects.get(pk=4)
        started_at = datetime.now()
        ended_at = started_at + timedelta(days=1)
        unit, price = Booking.calculate_price(product, started_at, ended_at)
        self.assertEquals(price, D('450'))
        self.assertEquals(unit, UNIT.DAY)
    
    def test_calculate_strict_day_with_hours_price(self):
        product = Product.objects.get(pk=4)
        started_at = datetime.now()
        ended_at = started_at + timedelta(days=1, hours=4)
        self.assertRaises(CanNotProve, Booking.calculate_price, product, started_at, ended_at)
    
    def test_calculate_strict_with_hours_price(self):
        product = Product.objects.get(pk=4)
        started_at = datetime.now()
        ended_at = started_at + timedelta(hours=4)
        self.assertRaises(CanNotProve, Booking.calculate_price, product, started_at, ended_at)
    

class BookingSeasonTest(TestCase):
    fixtures = ['category', 'patron', 'address', 'price', 'product']
    
    def test_calculate_day_season(self):
        product = Product.objects.get(pk=3)
        started_at = datetime(2010, 9, 15)
        ended_at = started_at + timedelta(days=2)
        unit, price = Booking.calculate_price(product, started_at, ended_at)
        self.assertEquals(price, D('20'))
        self.assertEquals(unit, UNIT.DAY)
    
    def test_calculate_over_season(self):
        product = Product.objects.get(pk=3)
        started_at = datetime(2010, 9, 15, 9, 0)
        ended_at = started_at + timedelta(days=14)
        unit, price = Booking.calculate_price(product, started_at, ended_at)
        self.assertEquals(price, D('126'))
        self.assertEquals(unit, UNIT.DAY)
    
    def test_calculate_over_year(self):
        product = Product.objects.get(pk=3)
        started_at = datetime(2010, 9, 30, 9, 0)
        ended_at = started_at + timedelta(days=90)
        unit, price = Booking.calculate_price(product, started_at, ended_at)
        self.assertEquals(price, D('720'))
        self.assertEquals(unit, UNIT.DAY)
    
    def test_calculate_on_start_terminal(self):
        product = Product.objects.get(pk=3)
        started_at = datetime(2010, 6, 21, 9, 0)
        ended_at = started_at + timedelta(days=4)
        unit, price = Booking.calculate_price(product, started_at, ended_at)
        self.assertEquals(price, D('40'))
        self.assertEquals(unit, UNIT.DAY)
    
    def test_calculate_on_end_terminal(self):
        product = Product.objects.get(pk=3)
        started_at = datetime(2010, 9, 20, 9, 0)
        ended_at = started_at + timedelta(days=2)
        unit, price = Booking.calculate_price(product, started_at, ended_at)
        self.assertEquals(price, D('20'))
        self.assertEquals(unit, UNIT.DAY)
    
