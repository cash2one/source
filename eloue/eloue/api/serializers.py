# -*- coding: utf-8 -*-
import copy
import base64
from posixpath import basename
from urllib2 import urlparse

import requests

from django.core.files.base import ContentFile
from django.utils.datastructures import SortedDict

from rest_framework import serializers, status
from eloue.api.exceptions import ValidationExceptions


def raise_on_validate(cls):
    """Decorate serializer with ability to raise on validation errors."""

    class RaiseOnValidateSerializer(cls):
        """Serializer that has ability to raise on validation errors."""

        def __init__(self, instance=None, data=None, files=None,
                     context=None, partial=False, many=None,
                     allow_add_remove=False, **kwargs):
            super(RaiseOnValidateSerializer, self).__init__(
                instance, data, files, context, partial, many,
                allow_add_remove, **kwargs)
            if context:
                self.suppress_exception = context.get(
                    'suppress_exception', False)

        def is_valid(self):
            super(RaiseOnValidateSerializer, self).is_valid()
            if self._errors and not self.suppress_exception:
                raise ValidationExceptions(self._errors)

    return RaiseOnValidateSerializer


class NullBooleanField(serializers.BooleanField):
    def from_native(self, value):
        return value if value is None else super(NullBooleanField, self).from_native(value)

class EncodedImageField(serializers.ImageField):
    empty = None
    _generated_image_names = None

    def __init__(self, generated_image_names=None, *args, **kwargs):
        if generated_image_names:
            # Ensure that 'generated_image_names' is an iterable
            assert isinstance(generated_image_names, (list, tuple)), '`generated_image_names` must be a list or tuple'
        self._generated_image_names = generated_image_names
        super(EncodedImageField, self).__init__(*args, **kwargs)

    def from_native(self, value):
        if type(value) is dict:
            encoding = value.get('encoding', 'base64')
            filename = value.get('filename', '')
            content = value['content']
            if encoding == 'base64':
                content = base64.b64decode(content)
            elif encoding == 'url':
                res = requests.get(content, stream=True)
                if status.is_success(res.status_code):
                    if not filename:
                        filename = basename(urlparse.urlsplit(content)[2])
                    content = res.content
            value = ContentFile(content, name=filename)
        return super(EncodedImageField, self).from_native(value)

    def field_to_native(self, obj, field_name):
        value = super(EncodedImageField, self).field_to_native(obj, field_name)
        if value and self._generated_image_names:
            value = {
                k: self.to_native(getattr(obj, k))
                for k in self._generated_image_names
            }
        return value

    def to_native(self, value):
        try:
            return value.url
        except ValueError:
            # if image file is missed and couldn't be reconstructed on the fly
            return self.empty

class ObjectMethodBooleanField(serializers.BooleanField):
    """
    A field that gets its value by calling a method on the object.
    """
    _method_name = None

    def __init__(self, method_name, *args, **kwargs):
        assert isinstance(method_name, basestring) and method_name, '`method_name` must be a non-empty string'
        self._method_name = method_name
        super(ObjectMethodBooleanField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        if obj is None:
            return self.empty
        value = getattr(obj, self._method_name)()
        return self.to_native(value)

class ModelSerializerOptions(serializers.HyperlinkedModelSerializerOptions):
    """
    Meta class options for ModelSerializer which supports `immutable_fields`
    """
    def __init__(self, meta):
        super(ModelSerializerOptions, self).__init__(meta)
        self.immutable_fields = getattr(meta, 'immutable_fields', ())


@raise_on_validate
class ModelSerializer(serializers.HyperlinkedModelSerializer):
    """
    A serializer that deals with model instances and querysets, and
    supports `immutable_fields`
    """
    _options_class = ModelSerializerOptions

    def get_fields(self):
        """
        Returns the complete set of fields for the object as a dict.

        This will be the set of any explicitly declared fields,
        plus the set of fields returned by get_default_fields().
        """
        ret = SortedDict()

        # Get the explicitly declared fields
        base_fields = copy.deepcopy(self.base_fields)
        for key, field in base_fields.items():
            ret[key] = field

        # Add in the default fields
        default_fields = self.get_default_fields()
        for key, val in default_fields.items():
            if key not in ret:
                ret[key] = val

        # If 'fields' is specified, use those fields, in that order.
        if self.opts.fields:
            assert isinstance(self.opts.fields, (list, tuple)), '`fields` must be a list or tuple'
            new = SortedDict()
            for key in self.opts.fields:
                new[key] = ret[key]
            ret = new

        # Remove anything in 'exclude'
        if self.opts.exclude:
            assert isinstance(self.opts.exclude, (list, tuple)), '`exclude` must be a list or tuple'
            for key in self.opts.exclude:
                ret.pop(key, None)

        # Mark immutable fields as read-only if there was an object instance provided
        if self.object:
            # Ensure that 'immutable_fields' is an iterable
            assert isinstance(self.opts.immutable_fields, (list, tuple)), '`immutable_fields` must be a list or tuple'

            # Set the `read_only` flag to any fields that have been specified
            # in the `immutable_fields` option
            for field_name in self.opts.immutable_fields:
                assert field_name in ret, (
                    "Non-existant field '%s' specified in `immutable_fields` "
                    "on serializer '%s'." %
                    (field_name, self.__class__.__name__))
                ret[field_name].read_only = True

        for key, field in ret.items():
            field.initialize(parent=self, field_name=key)

        return ret

class NestedModelSerializerMixin(object):
    def from_native(self, value, files=None):
        if value is not None:
            return self._hyperlink_field_class(
                view_name=self.opts.view_name,
                queryset=self.opts.model.objects.all()
            ).from_native(value)
