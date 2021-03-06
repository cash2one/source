from datetime import datetime
from django.db import models
from django.utils.encoding import smart_unicode

from products.models import Product
from accounts.models import Patron


class Gamer(models.Model):
	patron = models.ForeignKey(Patron)
	birthday = models.DateTimeField(null=True)
	like_facebook = models.BooleanField(default=False)
	created_at = models.DateTimeField(editable=False)

	def __unicode__(self):
		return smart_unicode(self.patron)
	
	def save(self, *args, **kwargs):
		if not self.created_at:
			self.created_at = datetime.now()
		super(Gamer, self).save(*args, **kwargs)


class ProductGamer(models.Model):
	gamer = models.ForeignKey(Gamer)
	product = models.ForeignKey(Product)
	created_at = models.DateTimeField(editable=False)
	
	def save(self, *args, **kwargs):
		if not self.created_at:
			self.created_at = datetime.now()
		super(ProductGamer, self).save(*args, **kwargs)