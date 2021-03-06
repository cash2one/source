# -*- coding: utf-8 -*-
import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TransactionTestCase

from products.models import Product, Price


class PriceTest(TransactionTestCase):
    reset_sequences = True
    fixtures = ['category', 'patron', 'address', 'product']
    
    def test_amount_values_negative(self):
        price = Price(amount=-1, product_id=1, unit=1, currency='EUR')
        self.assertRaises(ValidationError, price.full_clean)
    
    def test_amount_values_positive(self):
        try:
            price = Price(amount=20, product_id=4, unit=0, currency='EUR')
            price.full_clean()
        except ValidationError, e:
            self.fail(e)
    

class StandardPriceTest(TransactionTestCase):
    reset_sequences = True
    fixtures = ['category', 'patron', 'address', 'product']
    
    def test_product_pricing(self):
        standard_price = Price.objects.create(unit=1, amount=10, product_id=1, currency='EUR')
        product = Product.objects.get(pk=1)
        self.assertTrue(standard_price in product.prices.all())
    

class SeasonalPriceTest(TransactionTestCase):
    reset_sequences = True
    fixtures = ['category', 'patron', 'address', 'product', 'booking']
    
    def test_product_pricing(self):
        seasonal_price = Price.objects.create(
            name='Haute saison',
            product_id=1,
            amount=30,
            unit=1,
            currency='EUR',
            started_at=datetime.date.today(),
            ended_at=datetime.date.today() + datetime.timedelta(days=3)
        )
        product = Product.objects.get(pk=1)
        self.assertTrue(seasonal_price in product.prices.all())
    
