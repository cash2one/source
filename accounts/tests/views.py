# -*- coding: utf-8 -*-


import django.forms as forms

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase
from django.utils.translation import ugettext as _

from accounts.forms import PatronPasswordChangeForm, ContactForm
from accounts.models import Patron, Address
from payments import paypal_payment
from payments.paypal_payment import verify_paypal_account

def dummy_verify_paypal_account(email, first_name, last_name):
    if first_name=='Lin' and last_name=='LIU' and email=='unverified_paypal_account@e-loue.com':
        return 'UNVERIFIED'
    elif first_name=='Lin' and last_name=='LIU' and email=='invalid@e-loue.com':
        return 'INVALID'
    elif first_name=='Lin' and last_name=='LIU' and email=='test_verified_status@e-loue.com':
        return 'VERIFIED'

class PatronInfoAjaxTest(TransactionTestCase):
    reset_sequences = True
    fixtures = ['category', 'patron', 'address', 'price', 'product', 'booking']

    def test_work_autocomplete(self):
        import json
        self.assertTrue(self.client.login(username='alexandre.woog@e-loue.com', password='alexandre'))
        response = self.client.get(reverse('accounts_work_autocomplete'), {
            'term': 'e-'
        })
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(len(response), 2)
        response = self.client.get(reverse('accounts_work_autocomplete'), {
            'term': 'google'
        })
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(len(response), 0)
    
    def test_school_autocomplete(self):
        import json
        self.assertTrue(self.client.login(username='alexandre.woog@e-loue.com', password='alexandre'))
        response = self.client.get(reverse('accounts_studies_autocomplete'), {
            'term': 'e'
        })
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(len(response), 5)
        response = self.client.get(reverse('accounts_studies_autocomplete'), {
            'term': 'el'
        })
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(len(response), 2)

class PatronTest(TransactionTestCase):
    reset_sequences = True
    fixtures = ['category', 'patron', 'address', 'price', 'product', 'booking']
    
    def setUp(self):
        paypal_payment.verify_paypal_account = dummy_verify_paypal_account
    
    def tearDown(self):
        paypal_payment.verify_paypal_account = verify_paypal_account
        
    def test_patron_detail_view(self):
        response = self.client.get(reverse('patron_detail', args=['alexandre']))
        self.assertEqual(response.status_code, 200)
    
    def test_patron_detail_compat(self):
        response = self.client.get(reverse('patron_detail_compat', args=['alexandre', 1]))
        self.assertRedirects(response, reverse('patron_detail', args=['alexandre']), status_code=301)
    
    def test_patron_edit(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit'), {
            'first_name': 'Alex',
            'last_name': 'Woog',
            'username': 'alexandre',
            'email': 'alexandre.woog@e-loue.com',
            'is_professional': False,
            'is_subscribed': False
        })
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse('patron_edit'))
        patron = Patron.objects.get(email='alexandre.woog@e-loue.com')
        self.assertEquals(patron.first_name, 'Alex')

        # unconfirmed case
        response = self.client.post(reverse('patron_edit'), {
            'first_name': 'Lin',
            'last_name': 'LIU',
            'username': 'alexandre',
            'email': 'alexandre.woog@e-loue.com',
            'paypal_email': 'unverified_paypal_account@e-loue.com',
            'is_professional': False,
            'is_subscribed': False
        })
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse('patron_edit'))
        
        # invalid case
        response = self.client.post(reverse('patron_edit'), {
            'first_name': 'Lin',
            'last_name': 'LIU',
            'username': 'alexandre',
            'email': 'alexandre.woog@e-loue.com',
            'paypal_email': 'invalid@e-loue.com',
            'is_professional': False,
            'is_subscribed': False
        })
        
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse('patron_edit'))

        # verified case
        response = self.client.post(reverse('patron_edit'), {
            'first_name': 'Lin',
            'last_name': 'LIU',
            'username': 'alexandre',
            'email': 'alexandre.woog@e-loue.com',
            'paypal_email': 'test_verified_status@e-loue.com',
            'is_professional': False,
            'is_subscribed': False
        })
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse('patron_edit'))
        
        
    def test_patron_edit_form(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.get(reverse('patron_edit'))
        self.assertEquals(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertTrue(isinstance(response.context['form'], forms.ModelForm))
        
        
    def test_patron_edit_email_already_exists(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit'), {
            'first_name': 'Alex',
            'last_name': 'Woog',
            'username': 'alexandre',
            'email': 'timothee.peignier@e-loue.com',
            'is_professional': False,
            'is_subscribed': False
        })
        self.assertEquals(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(_(u"Un compte avec cet email existe déjà") in form.errors['email'][0])
    
    def test_patron_edit_email_empty(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit'), {
            'first_name': 'Alex',
            'last_name': 'Woog',
            'email': '',
            'username': 'alexandre',
            'is_professional': False,
            'is_subscribed': False
        })
        self.assertEquals(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(_(u"This field is required.") in form.errors['email'][0])
    
    def test_patron_edit_junk_email(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit'), {
            'first_name': 'Alex',
            'last_name': 'Woog',
            'username': 'alexandre',
            'email': 'alexandre.woog@jetable.net',
            'is_professional': False,
            'is_subscribed': False
        })
        self.assertEquals(response.status_code, 200)
        form = response.context['form']
        self.assertTrue( _(u"Pour garantir un service de qualité et la sécurité des utilisateurs d'e-loue.com dans le métro, vous ne pouvez pas vous enregistrer avec une adresse email jetable. Ne craignez rien, vous ne recevrez aucun courrier indésirable.") in form.errors['email'][0])
    
    def test_patron_password_form(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.get(reverse('patron_edit_password'))
        self.assertEquals(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertTrue(isinstance(response.context['form'], PatronPasswordChangeForm))
    
    def test_patron_password(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit_password'), {
            'old_password': 'alexandre',
            'new_password1': 'alex',
            'new_password2': 'alex'
        })
        self.assertEquals(response.status_code, 200)
    
    def test_patron_dashboard(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.get(reverse('dashboard'))
        self.assertEquals(response.status_code, 200)
    
    def test_contact_form(self):
        response = self.client.get(reverse('contact'))
        self.assertEquals(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertTrue(isinstance(response.context['form'], ContactForm))
    
    def test_contact_with_cc(self):
        response = self.client.post(reverse('contact'), {
            'subject': "J'ai un sujet pour vous",
            'message': "J'ai un message pour vous.",
            'sender': "moi@mondomaine.com",
            'cc_myself': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "J'ai un sujet pour vous")
        self.assertEqual(mail.outbox[0].body, "J'ai un message pour vous.")
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertTrue('contact@e-loue.com' in mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].extra_headers['Cc'], "moi@mondomaine.com")
        self.assertEqual(mail.outbox[0].extra_headers['Reply-To'], "moi@mondomaine.com")
    
    def test_contact_without_cc(self):
        response = self.client.post(reverse('contact'), {
            'subject': "J'ai un sujet pour vous",
            'message': "J'ai un message pour vous.",
            'sender': "moi@mondomaine.com",
            'cc_myself': False
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "J'ai un sujet pour vous")
        self.assertEqual(mail.outbox[0].body, "J'ai un message pour vous.")
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertTrue('contact@e-loue.com' in mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].extra_headers['Reply-To'], "moi@mondomaine.com")
        self.assertFalse('Cc' in mail.outbox[0].extra_headers)
    
    def test_borrower_history(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.get(reverse('borrower_booking_history'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('object_list' in response.context)
    
    def test_borrower_booking(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.get(reverse('borrower_booking_pending'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('object_list' in response.context)
    
    def test_owner_product(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.get(reverse('owner_product'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('product_list' in response.context)
    
    def test_owner_history(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.get(reverse('owner_booking_history'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('object_list' in response.context)
    
    def test_owner_booking(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.get(reverse('owner_booking_pending'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('object_list' in response.context)

class AddressManagement(TransactionTestCase):
    reset_sequences = True
    fixtures = ['category', 'patron', 'address', 'price', 'product']

    def test_modify_address(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit_addresses'), {
            'addresses-0-zipcode': '99999',
            'addresses-0-address1': 'FOO',
            'addresses-0-id': '1',
            'addresses-0-city': 'BAR',
            'addresses-0-country': 'FR',
            'addresses-1-zipcode': '75003',
            'addresses-1-address1': '11, rue debelleyme',
            'addresses-1-id': '3',
            'addresses-1-city': 'Paris',
            'addresses-1-country': 'FR',
            'addresses-2-zipcode': '',
            'addresses-2-address1': '',
            'addresses-2-city': '',
            'addresses-2-country': '',
            'addresses-INITIAL_FORMS': '2',
            'addresses-MAX_NUM_FORMS': '',
            'addresses-TOTAL_FORMS': '3',
        })
        self.assertRedirects(response, reverse('patron_edit_addresses'))
        address = Address.objects.get(pk=1)
        self.assertEqual(address.city, "BAR")
        self.assertEqual(address.address1, "FOO")
        self.assertEqual(address.country, 'FR')
        self.assertEqual(address.zipcode, u'99999')

    def test_new_address_with_error(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit_addresses'), {
            'addresses-0-zipcode': '75003',
            'addresses-0-address1': '11, rue debelleyme',
            'addresses-0-id': '1',
            'addresses-0-city': 'Paris',
            'addresses-0-country': 'FR',
            'addresses-1-zipcode': '75003',
            'addresses-1-address1': '11, rue debelleyme',
            'addresses-1-id': '3',
            'addresses-1-city': 'Paris',
            'addresses-1-country': 'FR',
            'addresses-2-zipcode': '324',
            'addresses-2-address1': '',
            'addresses-2-city': '',
            'addresses-2-country': '',
            'addresses-INITIAL_FORMS': '2',
            'addresses-MAX_NUM_FORMS': '',
            'addresses-TOTAL_FORMS': '3',
        })
        self.assertTemplateUsed(response, 'accounts/patron_edit_addresses.html')
        self.assertContains(response, _('This field is required.'))
    
    def test_remove_used_address(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit_addresses'), {
            'addresses-0-zipcode': '75003',
            'addresses-0-address1': '11, rue debelleyme',
            'addresses-0-id': '1',
            'addresses-0-city': 'Paris',
            'addresses-0-country': 'FR',
            'addresses-0-DELETE': 'on',
            'addresses-1-zipcode': '75003',
            'addresses-1-address1': '11, rue debelleyme',
            'addresses-1-id': '3',
            'addresses-1-city': 'Paris',
            'addresses-1-country': 'FR',
            'addresses-2-zipcode': '',
            'addresses-2-address1': '',
            'addresses-2-city': '',
            'addresses-2-country': '',
            'addresses-INITIAL_FORMS': '2',
            'addresses-MAX_NUM_FORMS': '',
            'addresses-TOTAL_FORMS': '3',
        })
        self.assertTemplateUsed(response, 'accounts/patron_edit_addresses.html')
        self.assertContains(response, 'Vous ne pouvez pas supprimer une adresse associé à un produit. Veuillez le changer sur le page produit.')

    def test_remove_unused_address(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit_addresses'), {
            'addresses-0-zipcode': '75003',
            'addresses-0-address1': '11, rue debelleyme',
            'addresses-0-id': '1',
            'addresses-0-city': 'Paris',
            'addresses-0-country': 'FR',
            'addresses-1-DELETE': 'on',
            'addresses-1-zipcode': '75003',
            'addresses-1-address1': '11, rue debelleyme',
            'addresses-1-id': '3',
            'addresses-1-city': 'Paris',
            'addresses-1-country': 'FR',
            'addresses-2-zipcode': '',
            'addresses-2-address1': '',
            'addresses-2-city': '',
            'addresses-2-country': '',
            'addresses-INITIAL_FORMS': '2',
            'addresses-MAX_NUM_FORMS': '',
            'addresses-TOTAL_FORMS': '3',
        })
        self.assertRedirects(response, reverse('patron_edit_addresses'))
    
    def test_add_new_address(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit_addresses'), {
            'addresses-0-zipcode': '75003',
            'addresses-0-address1': '11, rue debelleyme',
            'addresses-0-id': '1',
            'addresses-0-city': 'Paris',
            'addresses-0-country': 'FR',
            'addresses-1-zipcode': '75003',
            'addresses-1-address1': '11, rue debelleyme',
            'addresses-1-id': '3',
            'addresses-1-city': 'Paris',
            'addresses-1-country': 'FR',
            'addresses-2-zipcode': '75019',
            'addresses-2-address1': '10, passage Montenegro',
            'addresses-2-city': 'Paris',
            'addresses-2-country': 'FR',
            'addresses-INITIAL_FORMS': '2',
            'addresses-MAX_NUM_FORMS': '',
            'addresses-TOTAL_FORMS': '3',
        })
        self.assertRedirects(response, reverse('patron_edit_addresses'))


class PhonenumberManagement(TransactionTestCase):
    reset_sequences = True
    fixtures = ['category', 'patron', 'address', 'price', 'product', 'phones']

    def test_new_phone_number(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit_phonenumber'), {
            'phones-0-number': '0123456789',
            'phones-1-number': '24234', 
            'phones-TOTAL_FORMS': '2', 
            'phones-0-id': '1',
            'phones-1-id': '', 
            'phones-MAX_NUM_FORMS': '',
            'phones-INITIAL_FORMS': '1'
        })
        self.assertRedirects(response, reverse('patron_edit_phonenumber'))

    def test_delete_last_phone_number(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit_phonenumber'), {
            'phones-0-number': '0123456789',
            'phones-1-number': '', 
            'phones-0-DELETE': 'on',
            'phones-TOTAL_FORMS': '2', 
            'phones-0-id': '1',
            'phones-1-id': '', 
            'phones-MAX_NUM_FORMS': '',
            'phones-INITIAL_FORMS': '1'
        })
        self.assertTemplateUsed(response, 'accounts/patron_edit_phonenumber.html')
        self.assertContains(response, '<li>Vous ne pouvez pas supprimer tous vos numéros.</li>')

    def test_add_wrong_number(self):
        self.client.login(username='alexandre.woog@e-loue.com', password='alexandre')
        response = self.client.post(reverse('patron_edit_phonenumber'), {
            'phones-0-number': '0123456789',
            'phones-1-number': 'gergreg', 
            'phones-TOTAL_FORMS': '2', 
            'phones-0-id': '1',
            'phones-1-id': '', 
            'phones-MAX_NUM_FORMS': '',
            'phones-INITIAL_FORMS': '1'
        })
        self.assertTemplateUsed(response, 'accounts/patron_edit_phonenumber.html')
        self.assertContains(response, _(u'Vous devez spécifiez un numéro de téléphone'))
