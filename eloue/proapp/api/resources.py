
import qsstats
import datetime

from collections import defaultdict

from django.conf.urls.defaults import *
from django.http import Http404
from django.db.models import Q
from tastypie import fields
from tastypie.api import Api
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource, Resource
from tastypie.utils import trailing_slash
from tastypie.authorization import Authorization


from eloue.proapp.analytics_api_v3_auth import GoogleAnalyticsSetStats
from eloue.proapp.api.authentication import SessionAuthentication
from eloue.proapp.forms import TimeSeriesForm
from eloue.products.models import Product, Category, Picture, Price, ProductTopPosition, ProductHighlight
from eloue.accounts.models import Patron, Address, PhoneNumber, Subscription, CreditCard, OpeningTimes, ProPackage, Billing


def get_time_series(request=None):
	"""Return time series for qsstats"""
	end_date = datetime.date.today()
	start_date = (end_date - datetime.timedelta(days=30))
	interval = 'days'

	if request.GET.get('start_date') or request.GET.get('end_date') or request.GET.get('interval'):
		form = TimeSeriesForm(request.GET)
		if form.is_valid():
			start_date = form.cleaned_data['start_date']
			end_date = form.cleaned_data['end_date']
			interval = form.cleaned_data['interval']
		else:
			raise Http404([(k, u'%s' % 
				v[0]) for k, v in form.errors.items()])

	return start_date, end_date, interval


def get_analytics_event_references(event_action, event_label):
	metrics = 'ga:totalEvents'
	dimensions = 'ga:pagePath,ga:eventAction,ga:eventLabel'
	filters = 'ga:eventLabel==%s;ga:eventAction==%s' % (event_label, event_action)

	return metrics, dimensions, filters	


#Products resources
class ProductResource(ModelResource):
	category = fields.ToOneField('eloue.proapp.api.resources.CategoryResource', 'category', related_name='categories', full=True)

	class Meta:
		queryset = Product.objects.all()
		resource_name = 'products/product'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get', 'post', 'put']
		excludes = ['currency', 'payment_type']
		ordering = ['created_at']
		authentication = SessionAuthentication()
		authorization = Authorization()
		limit = 0

	def apply_authorization_limits(self, request, object_list):
		return object_list.filter(owner=request.user)

	def obj_create(self, bundle, request=None, **kwargs):
		return super(EnvironmentResource, self).obj_create(bundle, request, owner=request.user)

	def dehydrate(self, bundle):
		try:
			bundle.data['day_price'] = Price.objects.get(product=bundle.data['id'], unit=1).amount
		except:
			bundle.data['day_price'] = None
		
		return bundle


class CategoryResource(ModelResource):
	parent = fields.ToOneField('eloue.proapp.api.resources.CategoryResource', 'parent', related_name='children', null=True)

	class Meta:
		queryset = Category.objects.all()
		resource_name = 'products/category'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get']
		excludes = ['tree_id', 'rght', 'lft']
		filtering = {"parent": ('exact',)}
		authentication = SessionAuthentication()


class PictureResource(ModelResource):
	product = fields.ToOneField('eloue.proapp.api.resources.ProductResource', 'product', related_name='pictures')

	class Meta:
		queryset = Picture.objects.all()
		resource_name = 'products/picture'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get', 'post', 'put', 'delete']
		ordering = ['created_at']
		filtering = {"product": ('exact',)}
		authentication = SessionAuthentication()

	def apply_authorization_limits(self, request, object_list):
		return object_list.filter(product__owner=request.user)

	def obj_create(self, bundle, request=None, **kwargs):
		return super(EnvironmentResource, self).obj_create(bundle, request, product__owner=request.user)


class PriceResource(ModelResource):
	product = fields.ToOneField('eloue.proapp.api.resources.ProductResource', 'product', related_name='prices')
	
	class Meta:
		queryset = Price.objects.all()
		resource_name = 'products/price'
		list_allowed_methods = ['get', 'post', 'put', 'delete']
		detail_allowed_methods = ['get', 'post', 'put', 'delete']
		filtering = {"product": ('exact',)}
		authentication = SessionAuthentication()

	def apply_authorization_limits(self, request, object_list):
		return object_list.filter(product__owner=request.user)


#Accounts resources
class PatronResource(ModelResource):
	class Meta:
		queryset = Patron.objects.all()
		resource_name = 'accounts/patron'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get', 'put']
		excludes = ['about', 'activation_key', 'affiliate', 'avatar', 'company_name', 'date_joined', 'date_of_birth', 'drivers_license_date', 'drivers_license_number', 'hobby', 'is_active', 'is_professional', 'is_staff', 'is_superuser', 'last_login', 'modified_at', 'new_messages_alerted', 'password', 'paypal_email', 'place_of_birth', 'rib', 'school', 'work', 'url']
		authentication = SessionAuthentication()
		authorization = Authorization()


	def apply_authorization_limits(self, request, object_list):
		return object_list.filter(pk=request.user.pk)


class ShopResource(ModelResource):
	opening_times = fields.ToOneField('eloue.proapp.api.resources.OpeningTimesResource', 'opening_times', full=True, null=True)
	default_address = fields.ToOneField('eloue.proapp.api.resources.AddressResource', 'default_address', full=True, null=True)
	default_number = fields.ToOneField('eloue.proapp.api.resources.PhoneNumberResource', 'default_number', full=True, null=True)

	class Meta:
		queryset = Patron.objects.all()
		resource_name = 'accounts/shop'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get', 'put']
		excludes = ['avatar', 'activation_key', 'affiliate', 'date_joined', 'date_of_birth', 'drivers_license_date', 'drivers_license_number', 'hobby', 'is_active', 'is_professional', 'is_staff', 'is_superuser', 'last_login', 'modified_at', 'new_messages_alerted', 'password', 'paypal_email', 'place_of_birth', 'rib', 'school', 'work', 'civility', 'email', 'first_name', 'is_subscribed', 'last_name', 'username']
		authentication = SessionAuthentication()
		authorization = Authorization()
		include_resource_uri = True

	def apply_authorization_limits(self, request, object_list):
		return object_list.filter(pk=request.user.pk)


class OpeningTimesResource(ModelResource):
	patron = fields.ToOneField('eloue.proapp.api.resources.ShopResource', 'patron')

	class Meta:
		queryset = OpeningTimes.objects.all()
		resource_name = 'accounts/opening_times'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get', 'post', 'put']
		authentication = SessionAuthentication()
		authorization = Authorization()
		include_resource_uri = True


class AddressResource(ModelResource):
	patron = fields.ToOneField('eloue.proapp.api.resources.ShopResource', 'patron')

	class Meta:
		queryset = Address.objects.all()
		resource_name = 'accounts/address'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get', 'post', 'put']
		include_resource_uri = True
		authentication = SessionAuthentication()
		authorization = Authorization()


class PhoneNumberResource(ModelResource):
	patron = fields.ToOneField('eloue.proapp.api.resources.ShopResource', 'patron')

	class Meta:
		queryset = PhoneNumber.objects.all()
		resource_name = 'accounts/phone_number'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get', 'post', 'put']
		include_resource_uri = True
		authentication = SessionAuthentication()
		authorization = Authorization()


class ProPackageResource(ModelResource):

	class Meta:
		queryset = ProPackage.objects.filter(
					Q(valid_until__isnull=True, valid_from__lte=datetime.datetime.now()) |
        			Q(valid_until__isnull=False, valid_until__gte=datetime.datetime.now()))
		resource_name = 'accounts/propackage'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get']
		authentication = SessionAuthentication()

	def dehydrate(self, bundle):
		patron = bundle.request.user
		if patron.current_subscription and int(bundle.data['id']) == patron.current_subscription.propackage.pk:
			bundle.data['is_current_subscription'] = True
		else:
			bundle.data['is_current_subscription'] = False

		return bundle


class SubscriptionResource(ModelResource):
	patron = fields.ToOneField('eloue.proapp.api.resources.PatronResource', 'patron')
	propackage = fields.ToOneField('eloue.proapp.api.resources.ProPackageResource', 'propackage', full=True)

	class Meta:
		queryset = Subscription.objects.all()
		resource_name = 'accounts/subscription'
		list_allowed_methods = ['get', 'post']
		detail_allowed_methods = ['get', 'post', 'put']
		authentication = SessionAuthentication()
		authorization = Authorization()

	def apply_authorization_limits(self, request, object_list):
		return object_list.filter(patron=request.user, subscription_ended=None)

	def is_valid(self, bundle, request=None):
		errors = {}

		return errors

	def obj_update(self, bundle, request=None, **kwargs):
		patron = request.user
		new_propackage = ProPackage.objects.get(pk=bundle.data['propackage']['id'])

		patron.subscribe(new_propackage)

		return bundle

	def obj_create(self, bundle, request=None, **kwargs):
		patron = request.user
		new_propackage = ProPackage.objects.get(pk=bundle.data['propackage']['id'])

		patron.subscribe(new_propackage)

		return bundle


class BillingResource(ModelResource):
	class Meta:
		queryset = Billing.objects.all()
		resource_name = 'accounts/billing'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get']


	def apply_authorization_limits(self, request, object_list):
		return object_list.filter(patron=request.user)

	
	def dehydrate(self, bundle):
		billing = Billing.objects.get(pk=int(bundle.data['id']))
		bundle.data['masked_credit_card_number'] = billing.payment.creditcard.masked_number

		return bundle

	
	def alter_list_data_to_serialize(self, request, data):
		patron = request.user
		to = datetime.datetime.now()
		_from = datetime.datetime.combine(patron.next_billing_date(), datetime.time())

		#Generate current billing
		(billing, highlights, subscriptions, toppositions, phonenotifications, 
		emailnotifications) = Billing.builder(patron, _from, to)
		
		current_billing = {
			'billing': billing.__dict__, 
			'highlights': list(highlights.values()),
			'highlights_sum': highlights.sum,
			'subscriptions': list(subscriptions.values()),
			'subscriptions_sum': subscriptions.sum,
        	'toppositions': list(toppositions.values()),
        	'toppositions_sum': toppositions.sum,
        	'phonenotifications': list(phonenotifications.values()),
        	'emailnotifications': list(emailnotifications.values()), 
        	'from': _from, 'to': to 
		}

		for subscription in current_billing['subscriptions']:
			sub = Subscription.objects.get(pk=subscription['id'])
			subscription['propackage'] = sub.propackage.name
			del subscription['propackage_id']
			if sub.subscription_started and sub.subscription_ended:
				subscription['price'] = sub.price(sub.subscription_started, sub.subscription_ended)
			else:
				subscription['price'] = None


		for topposition in current_billing['toppositions']:
			top = ProductTopPosition.objects.get(pk=topposition['id'])
			topposition['product'] = top.product.summary
			if top.started_at and top.ended_at:
				topposition['price'] = top.price(top.started_at, top.ended_at)
			del topposition['product_id']


		for highlight in current_billing['highlights']:
			hight = ProductHighlight.objects.get(pk=highlight['id'])
			highlight['product'] = top.product.summary
			if hight.started_at and hight.ended_at:
				topposition['price'] = hight.price(hight.started_at, hight.ended_at)
			del highlight['product_id']

		objects = data['objects']
		data['objects'] = {'billing_history': objects}

		data['objects'].update({'current_billing': current_billing})
		
		return data



class CreditCardResource(ModelResource):
	class Meta:
		queryset = CreditCard.objects.all()
		resource_name = 'accounts/credit_card'
		list_allowed_methods = ['get']
		detail_allowed_methods = ['get', 'post']
		excludes = ['card_number']
		authentication = SessionAuthentication()

	def apply_authorization_limits(self, request, object_list):
		return object_list.filter(holder=request.user)


#Google Analytics resources
class PageViewResource(Resource):
	class Meta:
		resource_name = 'pageviews'
		authentication = SessionAuthentication()

	def override_urls(self):
		return [
			url(r"^(?P<resource_name>%s)/analytics%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_analytics_pageviews'), name="api_get_analytics_pageviews"),
		]

	def get_analytics_pageviews(self, request, **kwargs):
		self.is_authenticated(request)
		self.method_check(request, allowed=['get'])
		self.throttle_check(request)
		
		patron = Patron.objects.get(slug='ma-petite-cuisine')#patron = request.user

		
		data = []
		details = []
		totalResults = 0

		#Time series
		start_date, end_date, interval = get_time_series(request=request)

		#Google Analytics References
		metrics = 'ga:pageviews'
		dimensions = 'ga:pagePath'
		filters = 'ga:pagePathLevel2==/%s/' % patron.slug

		#Google Analytics Query
		partial_data, partial_details, partial_totalResults = GoogleAnalyticsSetStats(metrics=metrics, dimensions=dimensions, filters=filters).time_serie(start_date, end_date, interval=interval)

		data += partial_data
		details += partial_details
		totalResults += partial_totalResults


		position = 0

		while (patron.products.all().count() != position):

			products = patron.products.all()[position:][:45]

			#Time series
			start_date, end_date, interval = get_time_series(request=request)

			#Google Analytics References
			metrics = 'ga:pageviews'
			dimensions = 'ga:pagePath'
			filters = '%s' % ",".join(["ga:pagePathLevel4=@-%s/" % (product.pk) for product in products])

			#Google Analytics Query
			partial_data, partial_details, partial_totalResults = GoogleAnalyticsSetStats(metrics=metrics, dimensions=dimensions, filters=filters).time_serie(start_date, end_date, interval=interval)

			data += partial_data
			details += partial_details
			totalResults += partial_totalResults
			position += products.count()


		group_by_data = defaultdict(int)

		for date, total in data:
			group_by_data[date] += total

		
		data = []
		for key in sorted(group_by_data.iterkeys()):
				data.append((key, group_by_data[key]))

		objects = {
			'data': data,
			'details': details,
			'start_date': start_date,
			'end_date': end_date,
			'interval': interval,
			'count': totalResults
		}

		object_list = {
			'objects': objects
		}

		self.log_throttled_access(request)
		return self.create_response(request, object_list)


class RedirectionEventResource(Resource):
	class Meta:
		resource_name = 'redirection_events'
		authentication = SessionAuthentication()

	def override_urls(self):
		return [
			url(r"^(?P<resource_name>%s)/analytics%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_analytics_redirections'), name="api_get_analytics_redirections"),
		]

	def get_analytics_redirections(self, request, **kwargs):
		self.is_authenticated(request)
		self.method_check(request, allowed=['get'])
		self.throttle_check(request)

		patron = Patron.objects.get(slug='ma-petite-cuisine')#request.user

		#Google Analytics References
		metrics, dimensions, filters = get_analytics_event_references(event_action="Redirection", event_label=patron.slug)

		#Time series
		start_date, end_date, interval = get_time_series(request=request)

		#Google Analytics Query
		data, details, totalResults = GoogleAnalyticsSetStats(metrics=metrics, dimensions=dimensions, filters=filters).time_serie(start_date, end_date, interval=interval)

		objects = {
			'data': data,
			'details': details,
			'start_date': start_date,
			'end_date': end_date,
			'interval': interval,
			'count': totalResults
		}

		object_list = {
			'objects': objects
		}

		self.log_throttled_access(request)
		return self.create_response(request, object_list)


class PhoneEventResource(Resource):
	class Meta:
		resource_name = 'phone_events'
		authentication = SessionAuthentication()

	def override_urls(self):
		return [
			url(r"^(?P<resource_name>%s)/analytics%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_analytics_phones'), name="api_get_analytics_phones"),
		]

	def get_analytics_phones(self, request, **kwargs):
		self.is_authenticated(request)
		self.method_check(request, allowed=['get'])
		self.throttle_check(request)

		patron = Patron.objects.get(slug='ma-petite-cuisine')#patron = request.user

		#Google Analytics References
		metrics, dimensions, filters = get_analytics_event_references(event_action="Phone", event_label=patron.slug)

		#Time series
		start_date, end_date, interval = get_time_series(request=request)

		#Google Analytics Query
		data, details, totalResults = GoogleAnalyticsSetStats(metrics=metrics, dimensions=dimensions, filters=filters).time_serie(start_date, end_date, interval=interval)

		objects = {
			'data': data,
			'details': details,
			'start_date': start_date,
			'end_date': end_date,
			'interval': interval,
			'count': totalResults
		}

		object_list = {
			'objects': objects
		}

		self.log_throttled_access(request)
		return self.create_response(request, object_list)


class AddressEventResource(Resource):
	class Meta:
		resource_name = 'address_events'
		authentication = SessionAuthentication()

	def override_urls(self):
		return [
			url(r"^(?P<resource_name>%s)/analytics%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_analytics_addresses'), name="api_get_analytics_addresses"),
		]

	def get_analytics_addresses(self, request, **kwargs):
		self.is_authenticated(request)
		self.method_check(request, allowed=['get'])
		self.throttle_check(request)

		patron = Patron.objects.get(slug='ma-petite-cuisine') #patron = request.user

		#Google Analytics References
		metrics, dimensions, filters = get_analytics_event_references(event_action="Address", event_label=patron.slug)

		#Time series
		start_date, end_date, interval = get_time_series(request=request)

		#Google Analytics Query
		data, details, totalResults = GoogleAnalyticsSetStats(metrics=metrics, dimensions=dimensions, filters=filters).time_serie(start_date, end_date, interval=interval)

		objects = {
			'data': data,
			'details': details,
			'start_date': start_date,
			'end_date': end_date,
			'interval': interval,
			'count': totalResults
		}

		object_list = {
			'objects': objects
		}

		self.log_throttled_access(request)
		return self.create_response(request, object_list)




api_v1 = Api(api_name='1.0')
api_v1.register(ProductResource())
api_v1.register(CategoryResource())
api_v1.register(PictureResource())
api_v1.register(PriceResource())
api_v1.register(PageViewResource())
api_v1.register(RedirectionEventResource())
api_v1.register(PhoneEventResource())
api_v1.register(AddressEventResource())
api_v1.register(PatronResource())
api_v1.register(ShopResource())
api_v1.register(OpeningTimesResource())
api_v1.register(AddressResource())
api_v1.register(PhoneNumberResource())
api_v1.register(SubscriptionResource())
api_v1.register(ProPackageResource())
api_v1.register(BillingResource())
api_v1.register(CreditCardResource())
