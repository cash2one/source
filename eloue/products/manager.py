# -*- coding: utf-8 -*-
from django.db.models import Manager

class ProductManager(Manager):
    def active(self):
        return self.filter(archived=False)
    
    def archived(self):
        return self.filter(archived=True)
    
