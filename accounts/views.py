# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.middleware.csrf import rotate_token
from django.views.generic import ListView, View, TemplateView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlsafe_base64_decode
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect

from provider.oauth2.models import AccessToken

from rest_framework import status
from rest_framework.decorators import link, action
from rest_framework.response import Response

from eloue.views import AjaxResponseMixin, BreadcrumbsMixin
from eloue.http import JsonResponse
from eloue.decorators import ajax_required
from eloue.api import viewsets, filters, mixins, permissions
from eloue.api.decorators import list_action, ignore_filters
from eloue.api.exceptions import (
    ServerErrorEnum, DocumentedServerException, ValidationException
)

from products.search import product_search
from rent.models import Comment

from .forms import PatronSetPasswordForm, EmailPasswordResetForm, ContactForm, ContactFormPro

from .models import Patron, FacebookSession
from .utils import viva_check_phone
from . import serializers, models, search

from django.shortcuts import render
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages

USER_ME = 'me'
PAGINATE_USERS_BY = getattr(settings, 'PAGINATE_USERS_BY', 9) # UI v3: changed from 10 to 9
USE_HTTPS = getattr(settings, 'USE_HTTPS', True)

User = get_user_model()
assert User


# UI v3


class PasswordResetView(AjaxResponseMixin, View):
    http_method_names = ['post']
    form_class = EmailPasswordResetForm

    @method_decorator(ajax_required)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save(request=request, use_https=request.is_secure(), **kwargs)
            success_msg = _("We've e-mailed you instructions for setting your password to the e-mail address you submitted. You should be receiving it shortly.")
            return self.render_to_response({'detail': success_msg})
        return self.render_to_response({'errors': form.errors}, status=400)


class PasswordResetConfirmView(TemplateView):
    template_name = 'accounts/password_reset_confirm.jade'
    form_class = PatronSetPasswordForm
    token_generator = default_token_generator

    def dispatch(self, request, uidb64=None, **kwargs):
        try:
            uid = urlsafe_base64_decode(uidb64)
            user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return super(PasswordResetConfirmView, self).dispatch(request, user=user, **kwargs)

    def get_context_data(self, user=None, token=None, **kwargs):
        context = super(PasswordResetConfirmView, self).get_context_data(**kwargs)
        context.update({
            'validlink': bool(user is not None and self.token_generator.check_token(user, token)),
        })
        return context

    @method_decorator(ajax_required)
    def post(self, request, user=None, **kwargs):
        form = self.form_class(user, request.POST)
        if form.is_valid():
            form.save()
            success_msg = _("Your password has been set.  You may go ahead and log in now.")
            return JsonResponse({'detail': success_msg})
        return JsonResponse({'errors': form.errors}, status=400)


class ActivationView(TemplateView):
    template_name='activate/index.jade'

    def get_context_data(self, activation_key=None, **kwargs):
        activation_key = activation_key.lower()  # Normalize before trying anything with it.
        is_actived = Patron.objects.activate(activation_key)
        context = {
            'is_actived': is_actived,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
        }
        context.update(super(ActivationView, self).get_context_data(**kwargs))
        return context


class PatronDetailView(BreadcrumbsMixin, ListView):
    context_object_name = 'product_list'
    template_name = 'profile_public/index.jade'
    paginate_by = PAGINATE_USERS_BY

    def get(self, request, *args, **kwargs):
        if 'patron_id' in kwargs:
            # This is here to be compatible with the old app
            patron = get_object_or_404(Patron.on_site, pk=kwargs['patron_id'])
            return redirect(patron, permanent=True)
        self.object = self.get_object()
        return super(PatronDetailView, self).get(request, *args, **kwargs)

    def get_object(self):
        patron = get_object_or_404(
            Patron.on_site.select_related('default_address', 'languages'),
            slug=self.kwargs['slug']
        )
        return patron

    def get_queryset(self):
        queryset = product_search.filter(owner__exact=self.object.username).order_by('-created_at')
        list(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        patron = self.object
        borrowercomments = tuple(Comment.borrowercomments.select_related('booking__borrower', 'booking_product').filter(booking__owner=patron))
        context = {
            'patron': patron,
            'borrowercomments': borrowercomments,
        }
        context.update(super(PatronDetailView, self).get_context_data(**kwargs))
        return context


class LoginAndRedirectView(View):

    def dispatch(self, request, *args, **kwargs):
        response = redirect(request.GET['url'])
        user_token = request.GET.get('user_token', '')
        if user_token:
            try:
                AccessToken.objects.get(token=user_token, expires__gte=datetime.now())
            except AccessToken.DoesNotExist:
                pass
            else:
                max_age = 30 * 24 * 60 * 60
                expires = datetime.utcnow() + timedelta(seconds=max_age)
                rotate_token(request)
                response.set_cookie(
                    'user_token', user_token, max_age=max_age, expires=expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT"))
        return response


class LoginFacebookView(View):

    def _get_session(self, uid, facebook_token, expires):
        try:
            session = FacebookSession.objects.get(uid=uid)
        except FacebookSession.DoesNotExist:
            session = FacebookSession.objects.create(access_token=facebook_token, uid=uid, expires=expires)
        else:
            session.access_token = facebook_token
            session.expires = expires
            session.save()
        return session

    def _get_user(self, session):
        user = session.user
        if not user:
            user_data = session.me
            try:
                user = Patron.objects.get(email=user_data['email'])
            except (Patron.DoesNotExist, KeyError):
                user = None
            else:
                session.user = user
                session.save()
        return user

    def _get_or_create_user(self, session):
        user = self._get_user(session)
        if not user:
            user_data = session.me
            user = Patron.objects.create(
                username=session.uid,
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'])
            session.user = user
            session.save()
        return user

    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
        session = self._get_session(
            request.GET['user_id'], request.GET['access_token'],
            datetime.now() + timedelta(seconds=int(request.GET['expires_in'])))
        if request.GET.get('create_user', False):
            user = self._get_or_create_user(session)
        else:
            user = self._get_user(session)

        response = HttpResponse()
        if user:
            user_token = AccessToken.objects.create(user=user, client_id=1, scope=2)
            max_age = 30 * 24 * 60 * 60
            expires = datetime.utcnow() + timedelta(seconds=max_age)
            rotate_token(request)
            response.set_cookie(
                'user_token', user_token, max_age=max_age, expires=expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT"))
        return response



class ContactProView(View):
    form_class = ContactFormPro
    template_name = 'subscription/index.jade'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            name = form.cleaned_data['name']
            sender = form.cleaned_data['sender']
            phone_number = form.cleaned_data['phone_number']
            activity_field = form.cleaned_data['activity_field']
            
            new_form = self.form_class()
            recipients = ['contact@e-loue.com']

            if activity_field and name and sender:
                try:
                    message = "%s ; %s ; %s" % (name, activity_field, phone_number)
                    send_mail("Formulaire de contact Pro", "Email de contact : %s\n\nInformations du pro :\n%s" %(sender, message), "contact@e-loue.com", recipients)
                except BadHeaderError:
                    messages.add_message(request, messages.INFO, _('Erreur dans le formulaire'), extra_tags='safe')
                    return render(request, self.template_name, {'form': form, 'tag' : "error"})
                messages.add_message(request, messages.INFO, _('Le message a ete envoye avec succes'), extra_tags='safe')
                return render(request, self.template_name, {'form': new_form, 'tag' : "success"})
            else:
                messages.add_message(request, messages.INFO, _('Erreur dans le formulaire'), extra_tags='safe')
                return render(request, self.template_name, {'form': form, 'tag' : "error"})
        
        else:
            messages.add_message(request, messages.INFO, _('Erreur dans le formulaire'), extra_tags='safe')
            return render(request, self.template_name, {'form': form, 'tag' : "error"})



class ContactView(View):
    form_class = ContactForm
    template_name = 'contact_us/index.jade'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            subject = form.cleaned_data['category']
            message = form.cleaned_data['message']
            sender = form.cleaned_data['sender']
            cc_myself = form.cleaned_data['cc_myself']
            
            new_form = self.form_class()
            recipients = ['contact@e-loue.com']
            if cc_myself:
                recipients.append(sender)

            if subject and message and sender:
                try:
                    sujet = "Formulaire de contact : %s" % (subject)
                    send_mail(sujet, "Email de contact : %s\n\nMessage :\n%s" %(sender, message), "contact@e-loue.com", recipients) 
                except BadHeaderError:
                    messages.add_message(request, messages.INFO, _('Erreur dans le formulaire'), extra_tags='safe')
                    return render(request, self.template_name, {'form': form, 'tag' : "error"})
                messages.add_message(request, messages.INFO, _('Le message a ete envoye avec succes'), extra_tags='safe')
                return render(request, self.template_name, {'form': new_form, 'tag' : "success"})
            else:
                messages.add_message(request, messages.INFO, _('Erreur dans le formulaire'), extra_tags='safe')
                return render(request, self.template_name, {'form': form, 'tag' : "error"})
        
        else:
            messages.add_message(request, messages.INFO, _('Erreur dans le formulaire'), extra_tags='safe')
            return render(request, self.template_name, {'form': form, 'tag' : "error"})


# REST API 2.0


class UserViewSet(mixins.OwnerListPublicSearchMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = models.Patron.objects.select_related('default_address', 'default_number')
    serializer_class = serializers.UserSerializer
    #permission_classes = (permissions.UserPermissions,)
    filter_backends = (filters.HaystackSearchFilter, filters.DjangoFilterBackend, filters.OrderingFilter)
    owner_field = 'id'
    search_index = search.patron_search
    filter_fields = ('is_professional', 'is_active')
    ordering_fields = ('username', 'first_name', 'last_name')
    public_actions = ('retrieve', 'search', 'create', 'forgot_password', 'activation_mail', 'send_message')

    def initial(self, request, *args, **kwargs):
        pk_field = getattr(self, 'pk_url_kwarg', 'pk')
        if kwargs.get(pk_field, None) == USER_ME:
            user = self.request.user
            if not user.is_anonymous():
                self.kwargs[pk_field] = getattr(user, pk_field)
                kwargs[pk_field] = getattr(user, pk_field)
        return super(UserViewSet, self).initial(request, *args, **kwargs)

    @action(methods=['post', 'put'])
    def reset_password(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = serializers.PasswordChangeSerializer(
            instance=user, data=request.DATA, context=self.get_serializer_context())
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': _(u"Votre mot de passe à bien été modifié")})
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_action(methods=['post'])
    def forgot_password(self, request, *args, **kwargs):
        form = EmailPasswordResetForm(request.DATA)
        if form.is_valid():
            form.save(request=request, use_https=request.is_secure(), email_template_name='accounts/emails/password_reset_email', **kwargs)
            success_msg = _("We've e-mailed you instructions for setting your password to the e-mail address you submitted. You should be receiving it shortly.")
            return Response({'detail': success_msg})
        return Response({'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_action(methods=['post', 'get'])
    def activation_mail(self, request, *args, **kwargs):
        try:
            Patron.objects.get(email=request.GET['email']).send_activation_email()
        except Patron.DoesNotExist:
            return Response({'errors': _(u'User with this email not registered')}, status=status.HTTP_400_BAD_REQUEST)
        else:
            success_msg = _(u"We've e-mailed you instructions for activating your account to the e-mail address you submitted. You should be receiving it shortly.")
            return Response({'detail': success_msg})

    @link()
    def stats(self, request, *args, **kwargs):
        return Response(self.get_object().stats)

    @action(methods=['put', 'get'])
    @ignore_filters([filters.DjangoFilterBackend])
    def send_message(self, request, *args, **kwargs):
        serializer = serializers.ContactProSerializer(
            data=request.DATA,
            context={
                'request': request,
                'recipient': self.get_object()
            },
        )

        if not serializer.is_valid():
            raise ValidationException(serializer.errors)

        serializer.save()
        success_msg = _("Your message has been sent sucessfully.")
        return Response({'detail': success_msg})


class AddressViewSet(mixins.SetOwnerMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows addresses to be viewed or edited.
    """
    model = models.Address
    serializer_class = serializers.AddressSerializer
    filter_backends = (filters.OwnerFilter, filters.DjangoFilterBackend, filters.OrderingFilter) 
    filter_fields = ('patron', 'zipcode', 'city', 'country')
    ordering_fields = ('city', 'country')
    public_actions = ('retrieve', )

    def destroy(self, request, *args, **kwargs):
        address = self.get_object()
        if request.user.default_address == address:
            raise DocumentedServerException({
                'code': ServerErrorEnum.PROTECTED_ERROR[0],
                'description': ServerErrorEnum.PROTECTED_ERROR[1],
                'detail': _(u'The address is default address of current user')
            })
        elif address.products.exists():
            raise DocumentedServerException({
                'code': ServerErrorEnum.PROTECTED_ERROR[0],
                'description': ServerErrorEnum.PROTECTED_ERROR[1],
                'detail': _(u'The address is used in products')
            })
        else:
            return super(AddressViewSet, self).destroy(request, *args, **kwargs)


class PhoneNumberViewSet(mixins.SetOwnerMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows phone numbers to be viewed or edited.
    Phone numbers are sent to the borrower and to the owner for each booking.
    """
    model = models.PhoneNumber
    serializer_class = serializers.PhoneNumberSerializer
    filter_backends = (filters.OwnerFilter, filters.DjangoFilterBackend)
    filter_fields = ('patron',)
    public_actions = ('premium_rate_number',)

    @link()
    def premium_rate_number(self, request, *args, **kwargs):
        # get current object
        obj = self.get_object()
        # get call details by number and request parameters (e.g. REMOTE_ADDR)
        # note: request's exceptions will be handled in eloue.api.exception.api_exception_handler
        tags = viva_check_phone(obj.number, request=request)
        return Response(tags)

    def destroy(self, request, *args, **kwargs):
        phone = self.get_object()
        if request.user.default_number == phone:
            raise DocumentedServerException({
                'code': ServerErrorEnum.PROTECTED_ERROR[0],
                'description': ServerErrorEnum.PROTECTED_ERROR[1],
                'detail': _(u'The phone is default number of current user')
            })
        elif phone.products.exists():
            raise DocumentedServerException({
                'code': ServerErrorEnum.PROTECTED_ERROR[0],
                'description': ServerErrorEnum.PROTECTED_ERROR[1],
                'detail': _(u'The phone is used in products')
            })
        else:
            return super(PhoneNumberViewSet, self).destroy(request, *args, **kwargs)


class CreditCardViewSet(mixins.SetOwnerMixin, viewsets.NonEditableModelViewSet):
    """
    API endpoint that allows credit cards to be viewed or edited.
    Credit card is used to pay the booking. During the booking request pre-approval payment is done.
    After if the owner accept the booking we make the payment.
    """
    model = models.CreditCard
    serializer_class = serializers.CreditCardSerializer
    filter_backends = (filters.OwnerFilter, filters.DjangoFilterBackend)
    owner_field = 'holder'
    filter_fields = ('holder',)


class ProAgencyViewSet(mixins.SetOwnerMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows professional agencies to be viewed or edited.
    ProAgency lists all agencies of a pro renter.
    """
    model = models.ProAgency
    serializer_class = serializers.ProAgencySerializer
    filter_backends = (filters.OwnerFilter, filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('patron', 'zipcode', 'city', 'country')
    ordering_fields = ('city', 'country')
    public_actions = ('retrieve', 'list')


class ProPackageViewSet(viewsets.NonDeletableModelViewSet):
    """
    API endpoint that allows professional packages to be viewed or edited.
    ProPackage is subscribed by pro renter to access to e-loue and publish their goods online.
    """
    model = models.ProPackage
    permission_classes = (permissions.IsStaffOrReadOnly,)
    serializer_class = serializers.ProPackageSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('maximum_items', 'price', 'valid_from', 'valid_until')
    ordering_fields = ('name', 'maximum_items', 'price', 'valid_from', 'valid_until')
    public_actions = ('retrieve', 'list')


class SubscriptionViewSet(mixins.SetOwnerMixin, viewsets.NonDeletableModelViewSet):
    """
    API endpoint that allows subscriptions to be viewed or edited.
    Subcriptions are the means through what pro renters subscribe for ProPackages.
    """
    model = models.Subscription
    serializer_class = serializers.SubscriptionSerializer
    filter_backends = (filters.OwnerFilter, filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('patron', 'propackage', 'subscription_started', 'subscription_ended', 'payment_type')
    ordering_fields = ('subscription_started', 'subscription_ended', 'payment_type')


class BillingViewSet(mixins.SetOwnerMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows billings to be viewed or edited.
    """
    model = models.Billing
    serializer_class = serializers.BillingSerializer
    filter_backends = (filters.OwnerFilter, filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('patron',)
    ordering_fields = ('created_at',)


class BillingSubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows sbilling ubscriptions to be viewed or edited.
    """
    model = models.BillingSubscription
    serializer_class = serializers.BillingSubscriptionSerializer
    filter_backends = (filters.OwnerFilter, filters.DjangoFilterBackend, filters.OrderingFilter)
    owner_field = 'billing__patron'
    filter_fields = ('subscription', 'billing', 'price')
    ordering_fields = ('price',)


class SignUpLandingView(TemplateView):
    template_name = 'landing_pages/sign_in.jade'
    def get_context_data(self, **kwargs):
        context = super(SignUpLandingView, self).get_context_data(**kwargs)
        return context
