# coding=utf-8
from functools import wraps
from eloue.api import exceptions


def user_required(attname):
    def user_required_inner(f):
        @wraps(f)
        def wrapper(self, request, *args, **kwargs):
            obj = self.get_object()
            if getattr(obj, attname) != request.user:
                error = getattr(exceptions.PermissionErrorEnum, 'ACTION_%s_REQUIRED' % attname.upper())
                raise exceptions.PermissionException(error)
            return f(self, request, *args, **kwargs)
        return wrapper
    return user_required_inner


def ignore_filters(filter_list):
    def ignore_filters_inner(f):
        def wrapper(self, request, *args, **kwargs):
            self.ignore_filters = filter_list
            try:
                result = f(self, request, *args, **kwargs)
            except:
                raise
            finally:
                self.ignore_filters = []
            return result
        return wrapper
    return ignore_filters_inner
