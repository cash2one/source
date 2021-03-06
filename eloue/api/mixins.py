# -*- coding: utf-8 -*-
import logging
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import patch_cache_control
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
import sys
from rest_framework.permissions import SAFE_METHODS
from eloue.api.permissions import PublicAccessPermission
from eloue.api.serializers import NestedModelSerializerMixin

from .filters import OwnerFilter
from .permissions import IsOwnerOrReadOnly

class LocationHeaderMixin(object):
    def get_success_headers(self, data):
        try:
            return {'Location': self.get_location_url()}
        except (TypeError, KeyError):
            return {}

    def get_location_url(self):
        obj = self.object
        return reverse('%s-detail' % obj._meta.model_name, args=(obj.pk,))

class ErrorMixin(object):
    """
    View set with ability to return error messages according to
    api 2.0 spec requirements.
    """
    validation_exception_expected = True

    def get_serializer_context(self):
        """
        Add to serializer context flag designated whether exception on
        validation errors must be raised.
        """
        context = super(ErrorMixin, self).get_serializer_context()
        context['suppress_exception'] = not self.validation_exception_expected
        return context

    def initialize_request(self, request, *args, **kwargs):
        """
        Enable exception raising on validation errors.
        """
        self.validation_exception_expected = True
        return super(ErrorMixin, self).initialize_request(
            request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Disable exception raising on validation errors.

        It is necessary for correct work of Django REST Framework GUI.
        """
        self.validation_exception_expected = False
        return super(ErrorMixin, self).finalize_response(
            request, response, *args, **kwargs)

    def handle_exception(self, exc):
        response = super(ErrorMixin, self).handle_exception(exc)
        if response.status_code == HTTP_500_INTERNAL_SERVER_ERROR:
            logger = logging.getLogger('django.request')
            logger.error(
                'Internal Server Error: %s',
                self.request.path,
                exc_info=sys.exc_info(),
                extra={
                    'status_code': 500,
                    'request': self.request
                }
            )
        return response


class PermissionMixin(object):

    def initial(self, request, *args, **kwargs):
        # We must distinguish `list` and `search` but they are the same action by implementation.
        action = self.action
        if request.method == 'GET' and action == 'list' and request.QUERY_PARAMS:
            action = 'search'

        self.public_mode = True
        if request.user.is_staff or request.user.is_superuser:
            self.public_mode = False
        elif action not in getattr(self, 'public_actions', ()):
            self.public_mode = False

        super(PermissionMixin, self).initial(request, *args, **kwargs)

        self.owner_mode = False
        if 'pk' in kwargs:
            instance = self.get_object(self.get_queryset())
            if not request.user.is_anonymous():
                owner_fields = getattr(self, 'owner_field', None)
                if owner_fields:
                    if isinstance(owner_fields, basestring):
                        owner_fields = [owner_fields]
                    for owner_field in owner_fields:
                        owner_field = getattr(instance, owner_field, None)
                        if isinstance(owner_field, int):
                            self.owner_mode = (owner_field == request.user.pk)
                        else:
                            self.owner_mode = (owner_field == request.user)
                        if self.owner_mode:
                            break
        elif action == 'create':
            self.owner_mode = True

    def get_permissions(self):
        permissions = super(PermissionMixin, self).get_permissions()
        permissions.append(PublicAccessPermission())
        return permissions

    def check_permissions(self, request):
        """
        Allow permission checker to pass making a decision (return None). If there was not at least one positive
        decision it is assumed that access is denied.
        """
        permissions = []
        for permission in self.get_permissions():
            has_pemission = permission.has_permission(request, self)
            permissions.append(has_pemission)
            # check if decision has been passed
            if has_pemission is None:
                continue
            # deny access if forbidden
            if not has_pemission:
                self.permission_denied(request)

        # if iteration has finished, and there were no permission exceptions,
        # rise one if there were no positive decisions made (all checkers have returned None)
        if permissions and not any(permissions):
            self.permission_denied(request)

    def get_serializer_context(self):
        """
        Add to serializer context flag designated whether one can access to all fields or to only public fields.
        """
        context = super(PermissionMixin, self).get_serializer_context()
        context['public_mode'] = self.public_mode
        context['owner_mode'] = self.owner_mode
        return context


class OwnerListMixin(object):
    owner_filter_class = OwnerFilter

    def paginate_queryset(self, queryset, page_size=None):
        if self.owner_filter_class not in self.get_filter_backends():
            self.object_list = self.owner_filter_class().filter_queryset(self.request, queryset, self)
        return super(OwnerListMixin, self).paginate_queryset(self.object_list, page_size=page_size)

class OwnerListPublicSearchMixin(OwnerListMixin):
    owner_filter_class = OwnerFilter

    def paginate_queryset(self, queryset, page_size=None):
        if getattr(self, '_haystack_filter', False):
            # we should not filter out records by owner if there are search results
            return super(OwnerListMixin, self).paginate_queryset(self.object_list, page_size=page_size)
        return super(OwnerListPublicSearchMixin, self).paginate_queryset(self.object_list, page_size=page_size)

class SetOwnerMixin(OwnerListMixin):
    owner_field = 'patron'
    permission_classes = (IsOwnerOrReadOnly,)

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.

        The currently authenticated user will be set as the default value for
        the serializer's 'owner_field'. This will allow optional providing of
        values for such fields from the client side.
        """
        serializer = super(SetOwnerMixin, self).get_serializer(*args, **kwargs)
        user = self.request.user
        if not user.is_anonymous():
            owner_field = getattr(self, 'owner_field', None)
            if owner_field:
                if not isinstance(owner_field, basestring):
                    owner_field = iter(owner_field).next()
                owner_field = serializer.fields[owner_field]
                if isinstance(owner_field, NestedModelSerializerMixin):
                    owner_field.default = owner_field.to_hyperlink(user)
                else:
                    owner_field.default = owner_field.to_native(user)
        return serializer

    def pre_save(self, obj):
        user = self.request.user
        if not user.is_anonymous():
            owner_field = getattr(self, 'owner_field', None)
            if owner_field:
                if not isinstance(owner_field, basestring):
                    owner_field = iter(owner_field).next()
                owner_field_attname = obj._meta.get_field(owner_field).attname
                owner_id = getattr(obj, owner_field_attname)
                if not (user.is_staff and owner_id):

                    if settings.DEBUG and owner_id:
                        assert owner_id == user.id, \
                            'Changing owner from %s to %s' % (
                            owner_id, user.id)

                    setattr(obj, owner_field, user)
                    if owner_field in getattr(obj, '_nested_forward_relations', {}):
                        obj._nested_forward_relations[owner_field] = user
        return super(SetOwnerMixin, self).pre_save(obj)

class CacheControlMixin(object):
    # FIXME: Django internal cache don't understand 'no-cache', only 'max-age'
    cache_control = {'no-cache': True, 'max-age': 0}

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        response = super(CacheControlMixin, self).dispatch(request, *args, **kwargs)
        cache_control = self.cache_control.copy()
        if 'private' not in cache_control and 'public' not in cache_control:
            key = 'public' if request.user.is_anonymous() else 'private'
            cache_control[key] = True
        patch_cache_control(response, **cache_control)
        return response


class IgnoreFilterMixin(object):
    ignore_filters = []

    def get_filter_backends(self):
        backends = super(IgnoreFilterMixin, self).get_filter_backends()
        if self.ignore_filters:
            backends = filter(lambda x: x not in self.ignore_filters, backends)
        return backends
