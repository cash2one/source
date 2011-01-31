# -*- coding: utf-8 -*-
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from eloue.rent.models import Booking


class BookingAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {'fields': ('state', 'product', 'started_at', 'ended_at')}),
        (_('Borrower & Owner'), {'fields': ('borrower', 'owner', 'ip')}),
        (_('Payment'), {'fields': ('total_amount', 'insurance_amount', 'deposit_amount', 'currency')}),
    )
    list_filter = ('started_at', 'ended_at', 'state', 'created_at')
    raw_id_fields = ('owner', 'borrower', 'product')
    list_display = ('product_name', 'borrower_url', 'borrower_phone', 'borrower_email', 'owner_url', 'owner_phone', 'owner_email',
        'started_at', 'ended_at', 'created_at', 'total_amount', 'state')
    ordering = ['-created_at']
    actions = ['send_recovery_email']
    search_fields = ['product__summary', 'owner__username', 'owner__email', 'borrower__email', 'borrower__username']
    
    def send_recovery_email(self, request, queryset):
        for booking in queryset:
            booking.send_recovery_email()
    send_recovery_email.short_description = _(u"Envoyer un email de relance")
    
    def product_name(self, obj):
        return obj.product.summary
    product_name.short_description = _('Product')
    
    def borrower_url(self, obj):
        return '<a href="%s">%s</a>' % (
            reverse('admin:accounts_patron_change', args=[obj.borrower.pk]),
            obj.borrower.username
        )
    borrower_url.short_description = _('Borrower')
    borrower_url.allow_tags = True
    
    def borrower_email(self, obj):
        return '<a href="mailto:%(email)s">%(email)s</a>' % {'email': obj.borrower.email}
    borrower_email.short_description = _('Borrower email')
    borrower_email.allow_tags = True
    
    def borrower_phone(self, obj):
        if obj.borrower.phones.exists():
            return obj.borrower.phones.all()[0]
    borrower_phone.short_description = _('Borrower phone')
    
    def owner_url(self, obj):
        return '<a href="%s">%s</a>' % (
            reverse('admin:accounts_patron_change', args=[obj.owner.pk]),
            obj.owner.username
        )
    owner_url.short_description = _('Owner')
    owner_url.allow_tags = True
    
    def owner_email(self, obj):
        return '<a href="mailto:%(email)s">%(email)s</a>' % {'email': obj.owner.email}
    owner_email.short_description = _('Owner email')
    owner_email.allow_tags = True
    
    def owner_phone(self, obj):
        if obj.owner.phones.exists():
            return obj.owner.phones.all()[0]
    owner_phone.short_description = _('Owner phone')
    

admin.site.register(Booking, BookingAdmin)
