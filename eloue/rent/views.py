# -*- coding: utf-8 -*-
import logbook

from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list_detail import object_detail

from eloue.accounts.forms import EmailAuthenticationForm
from eloue.rent.decorators import validate_ipn
from eloue.rent.forms import BookingForm, PreApprovalIPNForm, PayIPNForm
from eloue.rent.models import Booking
from eloue.rent.wizard import BookingWizard

log = logbook.Logger('eloue.rent')


@require_POST
@csrf_exempt
@validate_ipn
def preapproval_ipn(request):
    form = PreApprovalIPNForm(request.POST)
    if form.is_valid():
        booking = Booking.objects.get(preapproval_key=form.cleaned_data['preapproval_key'])
        if form.cleaned_data['approved'] and form.cleaned_data['status'] == 'ACTIVE':
            # Changing state
            booking.payment_state = Booking.PAYMENT_STATE.AUTHORIZED
            booking.borrower.paypal_email = form.cleaned_data['sender_email']
            booking.borrower.save()
            # Sending emails
            booking.send_acceptation_email()
            booking.send_notification_email()
        else:
            booking.payment_state = Booking.PAYMENT_STATE.REJECTED
        booking.save()
    return HttpResponse()


@require_POST
@csrf_exempt
@validate_ipn
def pay_ipn(request):
    form = PayIPNForm(request.POST)
    if form.is_valid():
        booking = Booking.objects.get(pay_key=form.cleaned_data['pay_key'])
        if form.cleaned_data['action_type'] == 'PAY_PRIMARY' and form.cleaned_data['status'] == 'INCOMPLETE':
            booking.payment_state = Booking.PAYMENT_STATE.HOLDED
        booking.save()
    return HttpResponse()

   
@never_cache
def booking_create(request, *args, **kwargs):
    wizard = BookingWizard([BookingForm,EmailAuthenticationForm])
    return wizard(request, *args, **kwargs)


def booking_success(request, booking_id):
    return object_detail(request, queryset=Booking.objects.all(), object_id=booking_id, template_name='rent/booking_success.html', template_object_name='booking')


def booking_failure(request, booking_id):
    return object_detail(request, queryset=Booking.objects.all(), object_id=booking_id, template_name='rent/booking_failure.html',  template_object_name='booking')
