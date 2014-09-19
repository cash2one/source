# -*- coding: utf-8 -*-
from .urls import *

from functools import partial

from django.contrib.auth.views import logout_then_login, password_reset, password_reset_confirm, password_reset_confirm_uidb36, password_reset_done, password_reset_complete
from django.contrib.sitemaps.views import index, sitemap

from accounts.forms import EmailPasswordResetForm, PatronSetPasswordForm
from accounts.views import activate, authenticate, authenticate_headless, contact, google_oauth_callback, patron_subscription
from products.views import homepage, search, homepage_object_list
from products.search import product_only_search, car_search, realestate_search

urlpatterns = patterns('',
    url(r'^invitation_sent/$', TemplateView.as_view(template_name='accounts/invitation_sent.html'), name='invitation_sent'),
    url(r'^user_geolocation/$', 'accounts.views.user_geolocation', name='user_geolocation'),
    url(r'^get_user_location/$', 'accounts.views.get_user_location', name='get_user_location'),
    url(r"^announcements/", include("announcements.urls")),
    url(r'^sitemap.xml$', index, {'sitemaps': sitemaps}, name="sitemap"),
    url(r'^sitemap-(?P<section>.+).xml$', sitemap, {'sitemaps': sitemaps}),
    url(r'^reset/$', password_reset, {
        'is_admin_site': False,
        'password_reset_form': EmailPasswordResetForm,
        'template_name': 'accounts/password_reset_form.html',
        'email_template_name': 'accounts/emails/password_reset_email'
        }, name="password_reset"),
    url(r'^reset/done/$', password_reset_done, {
        'template_name': 'accounts/password_reset_done.html'
    }, name="password_reset_done"),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', password_reset_confirm, {
        'set_password_form': PatronSetPasswordForm,
        'template_name': 'accounts/password_reset_confirm.html'
    }, name="password_reset_confirm"),
    # TODO: You can remove this url pattern after your app has been deployed with Django 1.6 for PASSWORD_RESET_TIMEOUT_DAYS (3 days).
    url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm_uidb36, {
        'set_password_form': PatronSetPasswordForm,
        'template_name': 'accounts/password_reset_confirm.html'
    }),
    url(r'^reset/complete/$', password_reset_complete, {
        'template_name': 'accounts/password_reset_complete.html'
    }, name="password_reset_complete"),
    url(r'^espace_pro/$', patron_subscription, name="patron_subscription"),
    url(r'^faq/', include('faq.urls')),
    url(r'^contact/$', contact, name="contact"),
    url(r'^activate/(?P<activation_key>\w+)/$', activate, name='auth_activate'),
    url(r'^login/$', authenticate, name='auth_login'),
    url(r'^login_headless/$', authenticate_headless, name='auth_login_headless'),
    url(r'^logout/$', logout_then_login, name='auth_logout'),
    url(r'^oauth2callback$', google_oauth_callback),
    url(r'^dashboard/', include('eloue.dashboard.urls')),
    url(r'^media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'^%s' % "loueur/", include('accounts.urls')),
    url(r'^%s' % "location/", include('products.urls')),
    url(r'^%s' % "jeu-concours/", include('contest.urls')),
    url(r'^booking/', include('rent.urls')),
    url(r'^experiments/', include('django_lean.experiments.urls')),
    url(r'^edit/reports/', include('django_lean.experiments.admin_urls')),
    url(r'^edit/', include(admin.site.urls)),
    url(r'edit/', include('accounts.admin_urls')),
    url(r'^edit/stats/', include('reporting.admin_urls')),
    url(r'^api/', include('eloue.api.urls')),
    url(r'^oauth/', include('oauth_provider.urls')),
    url(r'^slimpay/', include('payments.slimpay_urls')),
    url(r'^$', homepage, name="home"),
    url(r'^lists/object/(?P<offset>[0-9]*)$', partial(homepage_object_list, search_index=product_only_search), name=''),
    url(r'^lists/car/(?P<offset>[0-9]*)$', partial(homepage_object_list, search_index=car_search), name=''),
    url(r'^lists/realestate/(?P<offset>[0-9]*)$', partial(homepage_object_list, search_index=realestate_search), name=''),
    url(r'^%s/$' % 'recherche', search, name="search"),
    url(r'^propw/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', password_reset_confirm, {
        'set_password_form': PatronSetPasswordForm,
        'template_name': 'accounts/professional_password_reset_confirm.html',
    }, name="propw"),
    # TODO: You can remove this url pattern after your app has been deployed with Django 1.6 for PASSWORD_RESET_TIMEOUT_DAYS (3 days).
    url(r'^propw/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm_uidb36, {
        'set_password_form': PatronSetPasswordForm,
        'template_name': 'accounts/professional_password_reset_confirm.html',
    }),
) + api2_urlpatterns