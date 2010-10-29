# -*- coding: utf-8 -*-
import datetime
import hashlib
import random
import re

from django.contrib.auth.models import UserManager

SHA1_RE = re.compile('^[a-f0-9]{40}$')


class PatronManager(UserManager):
    def exists(self, **kwargs):
        try:
            self.get(**kwargs)
            return True
        except self.model.DoesNotExist:
            return False
    
    def activate(self, activation_key):
        """
        Validate an activation key and activate the corresponding
        ``Patron`` if valid.
        
        If the key is valid and has not expired, return the ``Patron``
        after activating.
        
        If the key is not valid or has expired, return ``False``.
        
        If the key is valid but the ``Patron`` is already active,
        return ``False``.
        
        To prevent reactivation of an account which has been
        deactivated by site administrators, the activation key is
        reset to None after successful activation.
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search(activation_key):
            try:
                patron = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not patron.is_expired():
                patron.is_active = True
                patron.activation_key = None
                patron.save()
                return patron
        return False
    
    def create_user(self, username, email, password=None, pk=None):
        """
        Creates and saves a User with the given username, e-mail and password.
        """
        now = datetime.datetime.now()
           
        # Normalize the address by lowercasing the domain part of the email
        # address.
        try:
            email_name, domain_part = email.strip().split('@', 1)
        except ValueError:
            pass
        else:
            email = '@'.join([email_name, domain_part.lower()])
        
        user = self.model(username=username, email=email, is_staff=False,
                            is_active=True, is_superuser=False, last_login=now,
                            date_joined=now, id=pk)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
    
    def create_inactive(self, username, email, password, send_email=True, pk=None):
        """
        Create a new, inactive ``Patron`` and email its activation key to the
        ``Patron``, returning the new ``Patron``.
        
        To disable the email, call with ``send_email=False``.
        """
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        activation_key = hashlib.sha1(salt + email).hexdigest()
        
        new_patron = self.create_user(username, email, password, pk=pk)
        new_patron.is_active = False
        new_patron.activation_key = activation_key
        new_patron.save()
        
        if send_email:
            new_patron.send_activation_email()
        return new_patron
    
    def delete_expired(self):
        """
        Remove expired instances of ``Patron``s.
        """
        for patron in self.filter(is_active=False):
            if patron.is_expired():
                patron.delete()
    
