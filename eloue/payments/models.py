from django.contrib.contenttypes import generic
from django.db import models

from eloue.rent.models import Booking
from eloue.payments import *

class PaymentInformation(models.Model, abstract_payment.AbstractPayment):
    booking = generic.GenericRelation(Booking)
    class Meta:
        abstract = True

class NonPaymentInformation(PaymentInformation, non_payment.NonPayments):
	pass

class PaypalPaymentInformation(PaymentInformation, paypal_payment.AdaptivePapalPayments):
    preapproval_key = models.CharField(null=True, editable=False, blank=True, max_length=255)
    pay_key = models.CharField(null=True, editable=False, blank=True, max_length=255)

class PayboxPaymentInformation(PaymentInformation):
	numappel = models.CharField(max_length=20)
	numtrans = models.CharField(max_length=20)
	class Meta:
		abstract = True

class PayboxDirectPaymentInformation(PaymentInformation, paybox_payment.PayboxDirectPayment):
    numauth = models.CharField(max_length=20)

class PayboxDirectPlusPaymentInformation(PaymentInformation, paybox_payment.PayboxDirectPlusPayment):
	pass