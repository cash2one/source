# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import login
from django.views.generic.simple import direct_to_template

from django_lean.experiments.models import GoalRecord
from django_lean.experiments.utils import WebUser

from eloue.accounts.forms import EmailAuthenticationForm
from eloue.accounts.models import Patron
from eloue.products.models import Product
from eloue.rent.models import Booking
from eloue.rent.forms import BookingForm
from eloue.wizard import CustomFormWizard

class BookingWizard(CustomFormWizard):    
    def done(self, request, form_list):
        missing_form = form_list[-1]
        
        if request.user.is_anonymous(): # Create new Patron
            auth_form = form_list[1]
            new_patron = auth_form.get_user()
            if not new_patron:
                new_patron = Patron.objects.create_inactive(missing_form.cleaned_data['username'], 
                    auth_form.cleaned_data['email'], auth_form.cleaned_data['password'])
            if not hasattr(new_patron, 'backend'):
                from django.contrib.auth import load_backend
                backend = load_backend(settings.AUTHENTICATION_BACKENDS[0])
                new_patron.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
            login(request, new_patron)
        else:
            new_patron = request.user
        
        missing_form.instance = new_patron
        new_patron, new_address, new_phone = missing_form.save()
        
        booking_form = form_list[0]
        booking_form.instance.total_amount = Booking.calculate_price(booking_form.instance.product, 
            booking_form.cleaned_data['started_at'], booking_form.cleaned_data['ended_at'])
        booking_form.instance.borrower = new_patron
        booking = booking_form.save()
        
        booking.preapproval(
            cancel_url="http://cancel.me",
            return_url="http://return.me",
            ip_address=request.META['REMOTE_ADDR']
        )
        
        GoalRecord.record('rent_object', WebUser(request))
        return direct_to_template(request, template="rent/booking_preapproval.html", extra_context={
            'booking':booking,
        })
    
    def get_form(self, step, data=None):
        if issubclass(self.form_list[step], BookingForm):
            product = self.extra_context['product']
            booking = Booking(product=product, owner=product.owner)
            return self.form_list[step](data, prefix=self.prefix_for_step(step), 
                initial=self.initial.get(step, None), instance=booking)
        return super(BookingWizard, self).get_form(step, data)
    
    def parse_params(self, request, *args, **kwargs):
        self.extra_context['product'] = Product.objects.get(pk=kwargs['product_id'])
    
    def process_step(self, request, form, step):
        return super(BookingWizard, self).process_step(request, form, step)
    
    def get_template(self, step):
        if issubclass(self.form_list[step], EmailAuthenticationForm):
            return 'rent/booking_register.html'
        elif issubclass(self.form_list[step], BookingForm):
            return 'rent/booking_basket.html'
        else:
            return 'rent/booking_missing.html'
    
