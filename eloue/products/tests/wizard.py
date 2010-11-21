# -*- coding: utf-8 -*-
import os

from django.core.urlresolvers import reverse
from django.test import TestCase

from mock import patch

from eloue.products.models import Picture
from eloue.wizard import MultiPartFormWizard

local_path = lambda path: os.path.join(os.path.dirname(__file__), path)


class ProductWizardTest(TestCase):
    fixtures = ['patron', 'address', 'price', 'product', 'picture']
    
    def test_zero_step(self):
        response = self.client.get(reverse('product_create'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_create.html')
    
    def test_first_step_as_anonymous(self):
        f = open(local_path('../fixtures/bentley.jpg'))
        response = self.client.post(reverse('product_create'), {
            '0-category': 484,
            '0-picture': f,
            '0-summary': 'Bentley Brooklands',
            '0-price': '150',
            '0-deposit_amount': '1500',
            '0-quantity': 1,
            '0-description': 'Voiture de luxe tout confort',
            'wizard_step': 0
        })
        self.assertTrue(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_register.html')
        self.assertEquals(Picture.objects.count(), 2)
    
    @patch.object(MultiPartFormWizard, 'security_hash')
    def test_second_step_as_anonymous(self, mock_method):
        mock_method.return_value = '6941fd7b20d720833717a1f92e8027af'
        response = self.client.post(reverse('product_create'), {
            '0-category': 484,
            '0-picture_id': 1,
            '0-summary': 'Bentley Brooklands',
            '0-price': '150',
            '0-deposit_amount': '1500',
            '0-quantity': 1,
            '0-description': 'Voiture de luxe tout confort',
            '1-email': 'alexandre.woog@e-loue.com',
            '1-exists': 1,
            '1-password': 'alexandre',
            'hash_0': '6941fd7b20d720833717a1f92e8027af',
            'wizard_step': 1
        })
        self.assertTrue(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_missing.html')
    
    @patch.object(MultiPartFormWizard, 'security_hash')
    def test_third_step_as_anonymous(self, mock_method):
        mock_method.return_value = '6941fd7b20d720833717a1f92e8027af'
        response = self.client.post(reverse('product_create'), {
            '0-category': 484,
            '0-picture_id': 1,
            '0-summary': 'Bentley Brooklands',
            '0-price': '150',
            '0-deposit_amount': '1500',
            '0-quantity': 1,
            '0-description': 'Voiture de luxe tout confort',
            '1-email': 'alexandre.woog@e-loue.com',
            '1-exists': 1,
            '1-password': 'alexandre',
            '2-phones__phone': '0123456789',
            '2-addresses__address1': '11, rue debelleyme',
            '2-addresses__zipcode': '75003',
            '2-addresses__city': 'Paris',
            '2-addresses__country': 'FR',
            'hash_0': '6941fd7b20d720833717a1f92e8027af',
            'hash_1': '6941fd7b20d720833717a1f92e8027af',
            'wizard_step': 2
        })
        self.assertRedirects(response, reverse('booking_create', args=['bentley-brooklands', 5]))
    