# -*- coding: utf-8 -*-
import datetime
import logbook
import types
import random
import urllib

from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
from fsm.fields import FSMField
from fsm import transition
from pyke import knowledge_engine
from urlparse import urljoin

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import permalink
from django.db.models.signals import post_save
from django.utils.formats import get_format
from django.utils.translation import ugettext_lazy as _

from eloue.accounts.models import Patron
from eloue.products.models import CURRENCY, UNIT, Product
from eloue.products.utils import Enum
from eloue.rent.decorators import incr_sequence
from eloue.rent.fields import UUIDField, IntegerAutoField
from eloue.rent.manager import BookingManager, CurrentSiteBookingManager
from eloue.rent.payments.paypal_payment import AdaptivePapalPayments, PaypalError
from eloue.rent.payments.non_payment import NonPayments
from eloue.rent.payments.fsm_transition import smart_transition
from eloue.signals import post_save_sites
from eloue.utils import create_alternative_email, convert_from_xpf


PAY_PROCESSORS = {
    "nopay": NonPayments,
    "paypal": AdaptivePapalPayments
}

BOOKING_STATE = Enum([
    ('authorizing', 'AUTHORIZING', _(u"En cours d'autorisation")),
    ('authorized', 'AUTHORIZED', _(u"En attente")),
    ('rejected', 'REJECTED', _(u'Rejeté')),
    ('canceled', 'CANCELED', _(u'Annulé')),
    ('pending', 'PENDING', _(u'A venir')),
    ('ongoing', 'ONGOING', _(u'En cours')),
    ('ended', 'ENDED', _(u'Terminé')),
    ('incident', 'INCIDENT', _(u'Incident')),
    ('refunded', 'REFUNDED', _(u'Remboursé')),
    ('deposit', 'DEPOSIT', _(u'Caution versée')),
    ('closing', 'CLOSING', _(u"En attende de clôture")),
    ('closed', 'CLOSED', _(u'Clôturé')),
    ('outdated', 'OUTDATED', _(u"Dépassé"))
])

DEFAULT_CURRENCY = get_format('CURRENCY') if not settings.CONVERT_XPF else "XPF"

COMMISSION = D(str(getattr(settings, 'COMMISSION', 0.15)))
INSURANCE_FEE = D(str(getattr(settings, 'INSURANCE_FEE', 0.0594)))
INSURANCE_COMMISSION = D(str(getattr(settings, 'INSURANCE_COMMISSION', 0)))
INSURANCE_TAXES = D(str(getattr(settings, 'INSURANCE_TAXES', 0.09)))


USE_HTTPS = getattr(settings, 'USE_HTTPS', True)

PACKAGES_UNIT = {
    'hour': UNIT.HOUR,
    'week_end': UNIT.WEEK_END,
    'day': UNIT.DAY,
    'week': UNIT.WEEK,
    'two_weeks': UNIT.TWO_WEEKS,
    'month': UNIT.MONTH
}

PACKAGES = {
    UNIT.HOUR: lambda amount, delta: amount * (delta.seconds / 60),
    UNIT.WEEK_END: lambda amount, delta: amount,
    UNIT.DAY: lambda amount, delta: amount * delta.days,
    UNIT.WEEK: lambda amount, delta: amount * delta.days,
    UNIT.TWO_WEEKS: lambda amount, delta: amount * delta.days,
    UNIT.MONTH: lambda amount, delta: amount * delta.days
}

log = logbook.Logger('eloue.rent')


class Booking(models.Model):
    """A reservation"""
    uuid = UUIDField(primary_key=True)
    
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()
    
    state = FSMField(default='authorizing', choices=BOOKING_STATE)
    
    deposit_amount = models.DecimalField(max_digits=8, decimal_places=2)
    insurance_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY, default=DEFAULT_CURRENCY)
    
    owner = models.ForeignKey(Patron, related_name='bookings')
    borrower = models.ForeignKey(Patron, related_name='rentals')
    product = models.ForeignKey(Product, related_name='bookings')
    
    contract_id = IntegerAutoField(unique=True, db_index=True)
    pin = models.CharField(blank=True, max_length=4)
    ip = models.IPAddressField(blank=True, null=True)
    
    created_at = models.DateTimeField(blank=True, editable=False)
    canceled_at = models.DateTimeField(null=True, blank=True, editable=False)
    
    preapproval_key = models.CharField(null=True, editable=False, blank=True, max_length=255)
    pay_key = models.CharField(null=True, editable=False, blank=True, max_length=255)
    
    sites = models.ManyToManyField(Site, related_name='bookings')
    
    on_site = CurrentSiteBookingManager()
    objects = BookingManager()
    
    STATE = BOOKING_STATE
    
    NOT_NEED_IPN = True
    
    @incr_sequence('contract_id', 'rent_booking_contract_id_seq')
    def save(self, *args, **kwargs):
        
        if not self.pk:
            self.created_at = datetime.datetime.now()
            self.pin = str(random.randint(1000, 9999))
            self.deposit_amount = self.product.deposit_amount
            if self.product.has_insurance:
                self.insurance_amount = self.insurance_fee + self.insurance_taxes + self.insurance_commission
            else:
                self.insurance_amount = D(0)
        super(Booking, self).save(*args, **kwargs)
        
    
    @permalink
    def get_absolute_url(self):
        return ('booking_detail', [self.pk.hex])
    
    def __unicode__(self):
        return self.product.summary
    
    def __init__(self, *args, **kwargs):
        
        self.payment_type = "paypal" # for test sake, nopay or paypal
        self.payment_processor = PAY_PROCESSORS[self.payment_type](self) # give me a field like paypal/nopay, etc, I can instance an object.
        
        super(Booking, self).__init__(*args, **kwargs)
        for state in BOOKING_STATE.enum_dict:
            setattr(self, "is_%s" % state.lower(), types.MethodType(self._is_factory(state), self))
    
    @staticmethod
    def _is_factory(state):
        def is_state(self):
            return self.state == getattr(BOOKING_STATE, state)
        return is_state
        
    @staticmethod
    def calculate_price(product, started_at, ended_at):
        delta = ended_at - started_at
        
        engine = knowledge_engine.engine((__file__, '.rules'))
        engine.activate('pricing')
        for price in product.prices.iterator():
            engine.assert_('prices', 'price', (price.unit, price.day_amount))
        vals, plans = engine.prove_1_goal('pricing.pricing($type, $started_at, $ended_at, $delta)', started_at=started_at, ended_at=ended_at, delta=delta)
        engine.reset()
        
        amount, unit = D(0), PACKAGES_UNIT[vals['type']]
        package = PACKAGES[unit]
        for price in product.prices.filter(unit=unit, started_at__isnull=True, ended_at__isnull=True):
            amount += package(price.day_amount, delta)
        
        for price in product.prices.filter(unit=unit, started_at__isnull=False, ended_at__isnull=False):
            amount += package(price.day_amount, price.delta(started_at, ended_at))
        
        return unit, amount.quantize(D(".00"))
    
    def not_need_ipn(self):
        return self.payment_processor.NOT_NEED_IPN
        
    @smart_transition(source='authorizing', target='authorized', conditions=[not_need_ipn], save=True)
    def preapproval(self, cancel_url=None, return_url=None, ip_address=None):
        """Preapprove payments for borrower from Paypal.
        
        Keywords arguments :
        cancel_url -- The URL to which the sender’s browser is redirected after the sender cancels the preapproval at paypal.com.
        return_url -- The URL to which the sender’s browser is redirected after the sender approves the preapproval on paypal.com.
        ip_address -- The ip address of sender.
        
        The you should redirect user to :
        https://www.paypal.com/webscr?cmd=_ap-preapproval&preapprovalkey={{ preapproval_key }}
        """
        print ">>>>> payment processor type >>>>>>", type(self.payment_processor)
        try:
            self.preapproval_key = self.payment_processor.preapproval(cancel_url, return_url, ip_address)
        except PaypalError, e: #TODO, move the paypal error into the payments module
            self.state = BOOKING_STATE.REJECTED
            log.error(e)
        self.save()
    
    def send_recovery_email(self):
        context = {
            'booking': self,
            'preapproval_url': settings.PAYPAL_COMMAND % urllib.urlencode({
                'cmd': '_ap-preapproval',
                'preapprovalkey': self.preapproval_key
            })
        }
        message = create_alternative_email('rent/emails/borrower_recovery', context, settings.DEFAULT_FROM_EMAIL, [self.borrower.email])
        message.send()
    
    def send_ask_email(self):
        context = {'booking': self}
        message = create_alternative_email('rent/emails/owner_ask', context, settings.DEFAULT_FROM_EMAIL, [self.owner.email])
        message.send()
        message = create_alternative_email('rent/emails/borrower_ask', context, settings.DEFAULT_FROM_EMAIL, [self.borrower.email])
        message.send()
    
    def send_acceptation_email(self):
        from eloue.rent.contract import ContractGenerator
        context = {'booking': self}
        contract_generator = ContractGenerator()
        contract = contract_generator(self)
        content = contract.getvalue()
        message = create_alternative_email('rent/emails/owner_acceptation', context, settings.DEFAULT_FROM_EMAIL, [self.owner.email])
        message.attach('contrat.pdf', content, 'application/pdf')
        message.send()
        message = create_alternative_email('rent/emails/borrower_acceptation', context, settings.DEFAULT_FROM_EMAIL, [self.borrower.email])
        message.attach('contrat.pdf', content, 'application/pdf')
        message.send()
    
    def send_rejection_email(self):
        context = {'booking': self}
        message = create_alternative_email('rent/emails/borrower_rejection', context, settings.DEFAULT_FROM_EMAIL, [self.borrower.email])
        message.send()
    
    def send_cancelation_email(self, source=None):
        context = {'booking': self}
        if self.owner == source:
            message = create_alternative_email('rent/emails/owner_cancelation_to_owner', context, settings.DEFAULT_FROM_EMAIL, [self.owner.email])
            message.send()
            message = create_alternative_email('rent/emails/owner_cancelation_to_borrower', context, settings.DEFAULT_FROM_EMAIL, [self.borrower.email])
            message.send()
        else:
            message = create_alternative_email('rent/emails/borrower_cancelation_to_owner', context, settings.DEFAULT_FROM_EMAIL, [self.owner.email])
            message.send()
            message = create_alternative_email('rent/emails/borrower_cancelation_to_borrower', context, settings.DEFAULT_FROM_EMAIL, [self.borrower.email])
            message.send()
    
    def send_ended_email(self):
        context = {'booking': self}
        message = create_alternative_email('rent/emails/owner_ended', context, settings.DEFAULT_FROM_EMAIL, [self.owner.email])
        message.send()
        message = create_alternative_email('rent/emails/borrower_ended', context, settings.DEFAULT_FROM_EMAIL, [self.borrower.email])
        message.send()
    
    
    def send_closed_email(self):
        context = {'booking': self}
        message = create_alternative_email('rent/emails/owner_closed', context, settings.DEFAULT_FROM_EMAIL, [self.owner.email])
        message.send()
        message = create_alternative_email('rent/emails/borrower_closed', context, settings.DEFAULT_FROM_EMAIL, [self.borrower.email])
        message.send()
    
    @property
    def commission(self):
        """Return our commission
        
        >>> booking = Booking(total_amount=10)
        >>> booking.commission
        Decimal('1.50')
        """
        return self.total_amount * COMMISSION
        
    @property
    def total_commission(self):
        """ Return all the commission
        
        >>> booking = Booking(total_amount=10)
        >>> booking.total_commission
        Decimal('2.040')
        """
        return self.commission + self.insurance_fee
    
    @property
    def net_price(self):
        """Return net price for owner
        
        >>> booking = Booking(total_amount=10)
        >>> booking.net_price
        Decimal('8.50')
        """
        return self.total_amount - self.commission
    
    @property
    def insurance_commission(self):
        """Return our commission on insurance
        
        >>> booking = Booking(total_amount=10)
        >>> booking.insurance_commission
        Decimal('0')
        """
        return self.total_amount * INSURANCE_COMMISSION
    
    @property
    def insurance_fee(self):
        """Return insurance commission
        
        >>> booking = Booking(total_amount=10)
        >>> booking.insurance_fee
        Decimal('0.540')
        """
        return self.total_amount * INSURANCE_FEE
    
    @property
    def insurance_taxes(self):
        """Return insurance taxes
        
        >>> booking = Booking(total_amount=10)
        >>> booking.insurance_taxes
        Decimal('0.04860')
        """
        return self.insurance_fee * INSURANCE_TAXES
    
    @transition(source='pending', target='ongoing')
    def hold(self, cancel_url=None, return_url=None):
        """Take money from borrower and keep it safe for later.
        
        Keywords arguments :
        cancel_url -- The URL to which the sender’s browser is redirected after the sender cancels the preapproval at paypal.com.
        return_url -- The URL to which the sender’s browser is redirected after the sender approves the preapproval on paypal.com.
        ip_address -- The ip address of sender.
        
        Then you should redirect user to :
        https://www.paypal.com/webscr?cmd=_ap-payment&paykey={{ pay_key }}
        """
        self.pay_key = self.payment_processor.pay(cancel_url, return_url)
        self.save()
    
    @transition(source='ended', target='closing', save=True)
    @transition(source='closing', target='closed', conditions=[not_need_ipn], save=True)
    def pay(self):
        """Return deposit_amount to borrower and pay the owner"""
        self.payment_processor.execute_payment()
    
    @transition(source=['authorized', 'pending'], target='canceled', save=True)
    def cancel(self):
        """Cancel preapproval for the borrower"""
        self.payment_processor.cancel_preapproval()
    
    @transition(source='incident', target='deposit', save=True)
    def litigation(self, amount=None, cancel_url='', return_url=''):
        """Giving caution to owner"""
        # FIXME : Deposit amount isn't considered in preapproval amount
       
        self.payment_processor.give_caution(amount, cancel_url, return_url)
    
    @transition(source='incident', target='refunded', save=True)
    def refund(self):
        """Refund borrower or owner if something as gone wrong"""
        self.payment_processor.refund()
    
    @property
    def _currency(self):
        if settings.CONVERT_XPF:
            return "EUR"
        else:
            return self.currency
    

class Sinister(models.Model):
    uuid = UUIDField(primary_key=True)
    sinister_id = IntegerAutoField(unique=True, db_index=True)
    description = models.TextField()
    patron = models.ForeignKey(Patron, related_name='sinisters')
    booking = models.ForeignKey(Booking, related_name='sinisters')
    product = models.ForeignKey(Product, related_name='sinisters')
    
    created_at = models.DateTimeField(blank=True, editable=False)
    
    @incr_sequence('sinister_id', 'rent_sinister_sinister_id_seq')
    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = datetime.datetime.now()
        super(Sinister, self).save(*args, **kwargs)
    

post_save.connect(post_save_sites, sender=Booking)
