# import required classes
import httplib2
import sys
import datetime
import calendar
from collections import defaultdict
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets, AccessTokenRefreshError
from oauth2client.file import Storage
from oauth2client.tools import run
from apiclient.errors import HttpError

from django.conf import settings

from qsstats.utils import get_bounds

# The file with the OAuth 2.0 Client details for authentication and authorization.
CLIENT_SECRETS = settings.GOOGLE_CLIENT_SECRETS

# A helpful message to display if the CLIENT_SECRETS file is missing.
MISSING_CLIENT_SECRETS_MESSAGE = '%s is missing' % CLIENT_SECRETS

# The Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/analytics.readonly',
    message=MISSING_CLIENT_SECRETS_MESSAGE)

# A file to store the access token
TOKEN_FILE_NAME = settings.GOOGLE_TOKEN_FILE_NAME


class GoogleAnalyticsSetStats(object):

	def __init__(self, metrics=None, dimensions=None, filters=None, *args, **kwargs):
		self.service = self._initialize_service()
		self.profile_id = self._get_eloue_profile_id()
		self.metrics = metrics
		self.dimensions = dimensions
		self.filters = filters



	def _prepare_credentials(self):
		# Retrieve existing credendials
		storage = Storage(TOKEN_FILE_NAME)
		credentials = storage.get()

		# If existing credentials are invalid and Run Auth flow
		# the run method will store any new credentials
		if credentials is None or credentials.invalid:
			credentials = run(FLOW, storage) #run Auth Flow and store credentials

		return credentials


	def _initialize_service(self):
		# 1. Create an http object
		http = httplib2.Http()

		# 2. Authorize the http object
		# In this tutorial we first try to retrieve stored credentials. If
		# none are found then run the Auth Flow. This is handled by the
		# prepare_credentials() function defined earlier in the tutorial
		credentials = self._prepare_credentials()
		http = credentials.authorize(http)  # authorize the http object

		# 3. Build the Analytics Service Object with the authorized http object
		return build('analytics', 'v3', http=http)


	def _get_eloue_profile_id(self):
		# Get a list of all Google Analytics accounts for this user
		accounts = self.service.management().accounts().list().execute()

		if accounts.get('items'):
			# Get the first Google Analytics account
			accountId = accounts.get('items')[1].get('id')

			# Get a list of all the Web Properties for the first account
			webproperties = self.service.management().webproperties().list(accountId=accountId).execute()

			if webproperties.get('items'):
				# Get the first Web Property ID
				webpropertyId = webproperties.get('items')[0].get('id')

				# Get a list of all Profiles for the first Web Property of the first Account
				profiles = self.service.management().profiles().list(
					accountId=accountId,
					webPropertyId=webpropertyId).execute()

				if profiles.get('items'):
					# return the first Profile ID
					return profiles.get('items')[0].get('id')

	  	return None


	def time_serie(self, start=None, end=None, interval='days'):
		result = self.service.data().ga().get(
      		ids='ga:' + self.profile_id,
      		start_date=u'%s' % start,
      		end_date=u'%s' % end,
      		metrics='%s' % self.metrics, 
      		dimensions='ga:date,ga:week,ga:month,ga:year,%s' % self.dimensions, 
      		filters='%s' % self.filters
      	).execute()
			


		data = defaultdict(int)
		stats = []

		try:
			for row in result['rows']:
				if interval == 'days':
					date = datetime.datetime.strptime(row[0], '%Y%m%d')
				elif interval == 'weeks':
					week = int(row[1])-1
					date = datetime.datetime.strptime('0%s%s' % (week, row[3]), '%w%U%Y')
				elif interval == 'months':
					date = datetime.datetime.strptime('%s%s' % (row[2], row[3]), '%m%Y')

				row.reverse()
				data[calendar.timegm(date.timetuple()) * 1000] += int(row[0])

			if interval == 'days':
				if not data[calendar.timegm(start.timetuple()) * 1000]:
					data[calendar.timegm(start.timetuple()) * 1000] = 0


			for key in sorted(data.iterkeys()):
				stats.append((key, data[key]))

			if interval == 'weeks' or interval == 'months':
				if stats[0][0] != calendar.timegm(start.timetuple()) * 1000 and stats[0][0] < calendar.timegm(start.timetuple()) * 1000:
					stats[0] = (calendar.timegm(start.timetuple()) * 1000, stats[0][1])
				if stats[0][0] != calendar.timegm(start.timetuple()) * 1000 and stats[0][0] > calendar.timegm(start.timetuple()) * 1000:
					stats.insert(0, (calendar.timegm(start.timetuple()) * 1000, 0))


			return stats, result['rows'], result['totalResults']

		except:
			stats.append((calendar.timegm(start.timetuple()) * 1000, 0))
			stats.append((calendar.timegm(end.timetuple()) * 1000, 0))

			return stats, [], 0

