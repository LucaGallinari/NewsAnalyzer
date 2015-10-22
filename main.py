#!/usr/bin/env python

"""
This web application was developed for the course "Sistemi e Applicazioni di Rete" of the University
of Modena and Reggio Emilia.

News Analyzer is a cloud-based application that allows users to obtain more knowledge about
a specific news, by showing different informations of the main entities found in it.
It also works as a news provider and manager.
Take a look at the ABOUT page for more information.

Source: https://github.com/LucaGallinari/NewsAnalyzer
Online: https://news-manager.appspot.com/
"""

__author__ = "Luca Gallinari"

# Internal packages
import urllib
import httplib
import httplib2
import webapp2
import jinja2
import json
import datetime
import pytz
from collections import Counter

# Google App Engine or related packages
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import mail
from oauth2client.appengine import OAuth2Decorator
from oauth2client import client
from apiclient.discovery import build
from gaesessions import get_current_session
from models import *

# APIs
from API import faroo
from API.dandelion import DataTXT

# Initialize the decorator for the oauth2 authorization component
DECORATOR = OAuth2Decorator(
	client_id='99266390307-ic0seu51ghcq84m0bfhh3etdeafo81pl.apps.googleusercontent.com',
	client_secret='nfdBT_BReUhhiGrrsmJoe9WA',
	scope='https://www.googleapis.com/auth/plus.me')

# Use memcache
http = httplib2.Http(memcache)
# Retrieve g+ and youtube APIs helpers
gplusService = build("plus", "v1", http=http)
youtube = build('youtube', 'v3', developerKey='AIzaSyCWKe3sGVhfTmaYCvPf2jW-d_2QLEod7Rw')

# Setup jinja2 environment
JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.PackageLoader('main', 'templates'),
	extensions=['jinja2.ext.autoescape', 'jinja2.ext.loopcontrols'],
	autoescape=True)


def ccontains(value, arg):
	"""
	Jinja2 has no build-in methods to check if a string is within another.
	We extende Jinja2 funtionalities with this method

	@type   value:  basestring
	@param  value:  string in which we seek
	@type   arg:    basestring
	@param  arg:    string to seek for
	@rtype:         bool
	@return:        if arg within value or not
	"""
	return arg in value
JINJA_ENVIRONMENT.filters['ccontains'] = ccontains


def is_logged():
	"""
	Use gaessesions to check if logged

	@rtype:         bool
	@return:        if logged or not
	"""
	session = get_current_session()
	try:
		email = session['email']
		return True
	except KeyError:
		return False


def get_person_session_values():
	"""
	Get all the information regarding the (logged) user from the session,
	plus the logout url.

	@rtype:         dict
	@return:        user session values
	"""
	session = get_current_session()
	values = {
		'email': session['email'],
		'img_profile': session['img_profile'],
		'display_name': session['display_name'],
		'url_logout': '/logout'
	}
	return values


################
# # HANDLERS # #
################
class IndexHandler(webapp2.RequestHandler):
	"""
	Handler for the homepage that call the NewsHandler to get the latest news.
	If the user is logged it retrieves his filters.
	"""
	def get(self):
		template_values = {}

		if is_logged():
			template_values = get_person_session_values()

			# Retrieve filters from DB
			q = DBFilter.query(DBFilter.owner == template_values['email']).fetch()
			filters = []
			for f in q:
				fil = {
					'id': f.key.id(),
					'name': f.name,
					'keywords': f.keywords,
					'email_hour': f.email_hour,
				}
				filters.append(fil)
			template_values['filters'] = filters

		else:
			template_values['url_login'] = users.create_login_url("/auth_google")

		# Search by keywords?
		search = self.request.get('search')
		if search != '':
			template_values['search'] = search
		nh = NewsHandler(False)
		template_values['news'] = nh.get_news(search)

		# Render template and return
		template_values['page'] = "index"
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


class FiltersHandler(webapp2.RequestHandler):
	"""
	Handler that manage filters's CRUD (create, read, update, delete).
	"""
	def get(self):
		"""
		Retrieve filters from the datastore and render them into a template.
		"""
		if not is_logged():
			self.redirect(users.create_login_url("/auth_google"))
		else:
			template_values = get_person_session_values()

			# Retrieve filters from DB
			q = DBFilter.query(DBFilter.owner == template_values['email']).fetch()
			filters = []
			for f in q:
				fil = {
					'id': f.key.id(),
					'name': f.name,
					'keywords': f.keywords,
					'email_hour': f.email_hour,
				}
				filters.append(fil)
			template_values['filters'] = filters

			# Render template and return
			template_values['page'] = "filters"
			template = JINJA_ENVIRONMENT.get_template('filters.html')
			self.response.write(template.render(template_values))

	def post(self):
		"""
		Insert a filter into the datastore.
		Writes "Ok: [ID]" if success, "[error]" if not
		"""
		if not is_logged():
			self.response.write("You are not logged!")
		else:
			# Retrieve data
			session = get_current_session()
			name = self.request.get('name')
			keywords = self.request.get('keywords')
			email_hour = self.request.get('email_hour', -1)

			# Some checks
			if name == "":
				self.response.write("Name field is empty!")
				return
			try:
				email_hour = int(email_hour)
			except ValueError:
				email_hour = -1

			# Save the filter
			my_filter = DBFilter(
				owner=session['email'],
				name=name,
				keywords=keywords,
				email_hour=email_hour
			)
			key = my_filter.put()
			self.response.write("Ok: " + str(key.id()))

	def put(self):
		"""
		Update a filter.
		Writes "Ok" if success, "[error]" if not
		"""
		if not is_logged():
			self.response.write("You are not logged!")
		else:
			# Retrieve data
			session = get_current_session()
			filter_id = self.request.get('id')
			name = self.request.get('name')
			keywords = self.request.get('keywords')
			email_hour = self.request.get('email_hour')

			# Some checks - ID
			if filter_id is None:
				self.response.write("ID not specified!")
				return
			if filter_id == "":
				self.response.write("ID is empty!")
				return
			try:
				filter_id = long(filter_id)
			except ValueError:
				self.response.write("ID is not a valid integer!")
				return
			# Some checks - OTHERS
			if name == "":
				self.response.write("Name field is empty!")
				return
			if keywords is None:
				keywords = ""
			if email_hour == "":
				email_hour = -1
			else:
				try:
					email_hour = int(email_hour)
				except ValueError:
					email_hour = -1

			# Update the filter
			my_filter = DBFilter(id=filter_id, owner=session['email']).key.get()
			my_filter.name = name
			my_filter.keywords = keywords
			my_filter.email_hour = email_hour
			my_filter.put()
			self.response.write("Ok")

	def delete(self):
		"""
		Delete a filter by ID.
		Writes "Ok" if success, "[error]" if not
		"""
		if not is_logged():
			self.response.write("You are not logged!")
		else:
			session = get_current_session()
			# various checks
			filter_id = self.request.get('id')
			if filter_id is None:
				self.response.write("ID not specified!")
				return
			if filter_id == "":
				self.response.write("ID is empty!")
				return

			try:
				filter_id = long(filter_id)
			except ValueError:
				self.response.write("ID is not a valid integer!")
				return
			# delete from DB
			DBFilter(id=filter_id, owner=session['email']).key.delete()
			self.response.write("Ok")


class FavoritesHandler(webapp2.RequestHandler):
	"""
	Handler that manage insert and delete of a favorite news
	"""
	def get(self):
		"""
		Simply retrieve favorites and render them
		"""
		if not is_logged():
			self.redirect(users.create_login_url("/auth_google"))
		else:
			template_values = get_person_session_values()

			# Retrieve favorites from DB ordered by add_date DESC
			q = DBFavorite.query(DBFavorite.owner == template_values['email']).order(-DBFavorite.add_date).fetch()
			favs = []
			for f in q:
				fav = {
					'id': f.key.id(),
					'title': f.title,
					'kwic': f.kwic,
					'url': f.url,
					'imgurl': f.iurl,
					'author': f.author,
					'domain': f.domain,
					'date': f.date,
					'add_date': f.add_date
				}
				favs.append(fav)
			template_values['favs'] = favs

			# Render template and return
			template_values['page'] = "favs"
			template = JINJA_ENVIRONMENT.get_template('favorites.html')
			self.response.write(template.render(template_values))

	def post(self):
		"""
		Insert a favorite into the datastore.
		Writes "Ok: [ID]" if success, "[error]" if not
		"""
		if not is_logged():
			self.response.write("You are not logged!")
		else:
			# Retrieve data
			session = get_current_session()
			title = self.request.get('title')
			kwic = self.request.get('kwic')
			url = self.request.get('url')
			iurl = self.request.get('iurl')
			author = self.request.get('author')
			domain = self.request.get('domain')
			date = self.request.get('date')

			# Some checks
			if title == "" or kwic == "" or url == "":
				self.response.write("One or more required field/s is/are empty!")
				return
			if date != "":
				try:
					# date is a long number? so it's a timestamp
					date_l = long(date)
					date = datetime.datetime.fromtimestamp(date_l / 1e3).strftime('%Y-%m-%d %H:%M:%S')  # true division
				except ValueError:
					# it's a string, useless command below
					date = str(date)

			# Save the favorite
			my_fav = DBFavorite(
				owner=session['email'],
				title=title,
				kwic=kwic,
				url=url,
				iurl=iurl,
				author=author,
				domain=domain,
				date=date
			)
			key = my_fav.put()
			self.response.write("Ok: " + str(key.id()))

	def delete(self):
		"""
		Delete a favorite by ID.
		Writes "Ok" if success, "[error]" if not
		"""
		if not is_logged():
			self.response.write("You are not logged!")
		else:
			session = get_current_session()
			# some checks
			fav_id = self.request.get('id')
			if fav_id == "":
				self.response.write("ID not specified!")
				return

			try:
				fav_id = long(fav_id)
			except ValueError:
				self.response.write("ID is not a valid integer!")
				return
			# remove from the DB
			DBFavorite(id=fav_id, owner=session['email']).key.delete()
			self.response.write("Ok")


class NewsHandler:
	"""
	This class uses FAROO APIs interface to retrieve latest news.
	If the json variable is set to true, FAROO response will be in JSON format
	and data must be decode before cheking favorites and datetime. If json is False,
	FARRO response data will be accessed as a simple dict.
	"""
	# we are serving a json request?
	json = False

	def __init__(self, retjson):
		"""
		Setup

		@type   retjson:  bool
		@param  retjson:  want a JSON reponse
		"""
		self.json = retjson

	def get_news(self, search='', start=1):
		"""
		Call FAROO APIs, check favorites and datetimes.
		"""
		favs = []

		# Retrieve favorites from DB
		if is_logged():
			session = get_current_session()
			q = DBFavorite.query(DBFavorite.owner == session['email']).fetch()
			for f in q:
				favs.append({'id': f.key.id(), 'url': f.url})

		# Retrieve news
		freq = faroo.Faroo()
		data = freq.param('src', 'news').param('start', start).query(self.json, search)

		# if retrieved data are in json format, decode them
		if self.json:
			# Data is a DICT
			data = json.loads(data)
			# No news found?
			if 'results' in data:
				news = data['results']
				for n in news:
					# check if favorite
					if len(favs) != 0:
						for f in favs:
							if f['url'] == n['url']:
								n['favorite'] = f['id']
					# adjust datetime if it's a timestamp
					if type(n['date']) is not datetime.datetime:
						try:
							# date is a long number? so it's a timestamp
							date_i = int(n['date'])
							n['date'] = datetime.datetime.fromtimestamp(date_i / 1e3).strftime('%Y-%m-%d %H:%M:%S')  # true division
						except ValueError:
							# it's a string, useless command below
							n['date'] = str(n['date'])
			else:
				news = []
		else:
			# Data is a LIST
			# No news found?
			if hasattr(data, 'results'):
				if data.results is None:
					news = []
				else:
					news = data.results
					for n in news:
						# check if favorite
						if len(favs) != 0:
							for f in favs:
								if f['url'] == n.url:
									n.favorite = f['id']
						# adjust datetime if it's a timestamp
						if type(n.date) is not datetime.datetime:
							try:
								# date is a long number? so it's a timestamp
								date_l = int(n.date)
								n.date = datetime.datetime.fromtimestamp(date_l / 1e3).strftime('%Y-%m-%d %H:%M:%S')  # true division
							except ValueError:
								# it's a string, useless command below
								n.date = str(n.date)
			else:
				news = []

		# must return json formatted data
		if self.json:
			# add logged check in the reponse
			news = json.dumps({'data': data, 'logged': is_logged()})

		return news


class AnalyzeHandler(webapp2.RequestHandler):
	"""
	This class manage analysis.
	"""
	def get(self):
		"""
		Show analyzed url if no url was passed, otherwise extract entities with Dandelion APIs
		and put a "category" field based on the "types" of the entity.
		Save entity extracted in the DB for external APIs.
		"""
		template_values = {}
		url = self.request.get('url')

		if is_logged():
			template_values = get_person_session_values()
			# save the analyzation if url not empty
			if url != '':
				analysis = DBAnalyzedURL(owner=template_values['email'], url=url)
				analysis.put()

			# Retrieve previous analizations from DB
			q = DBAnalyzedURL.query(DBAnalyzedURL.owner == template_values['email']).order(-DBAnalyzedURL.add_date).fetch()
			analiz = []
			for a in q:
				analiz.append({'url': a.url, 'add_date': a.add_date.strftime('%Y-%m-%d %H:%M:%S')})
			template_values['analiz'] = analiz

		if url != '':
			# some url checks
			datatxt = DataTXT(app_id='ff66f767', app_key='e22401da7ae5647cb5b7070dea5e0e7f')
			try:
				data = datatxt.nex(
					url,
					# include_categories=True,
					include_types=True,
					include_abstract=True,
					include_image=True
				)
				if hasattr(data, 'annotations'):
					data = data.annotations
					idlist = []
					newdata = []
					# loop entities
					for e in data:
						# if already present in the new list don't add again
						# so i get rid of duplicates that Dandelion put in the list
						add = True
						if hasattr(e, 'id'):
							if e.id in idlist:
								add = False
							else:
								add = True
								idlist.append(e.id)
						if add:
							# loop types
							if hasattr(e, 'types'):
								if len(e.types) != 0:
									for t in e.types:
										if 'Person' in t:
											e.categ = 'Person'
											break
										elif 'Organisation' in t:
											e.categ = 'Organisation'
											break
										elif 'Place' in t:
											e.categ = 'Place'
											break
										elif 'CelestialBody' in t:
											e.categ = 'Space'
											break
										elif 'Event' in t:
											e.categ = 'Event'
											break
										elif 'Film' in t:
											e.categ = 'Film'
											break
										elif 'Software' in t:
											e.categ = 'Software'
											break
										else:
											e.categ = 'Concept'
								else:
									e.categ = 'Concept'
							else:
								e.categ = 'Concept'
							newdata.append(e)
							ent = DBEntityExtractedToday(
								url=url,
								entity=e.label
							)
							ent.put()
					template_values['data'] = newdata
				else:
					template_values['data'] = []
				template_values['url'] = url

			except httplib.HTTPException:
				# deadline response reached, so i signal to redo the request
				template_values['error'] = 1

		# Render template and return
		template_values['page'] = "analyze"
		template = JINJA_ENVIRONMENT.get_template('analyze.html')
		self.response.write(template.render(template_values))

	def delete(self):
		"""
		Remove all analysis of this user.
		"""
		if not is_logged():
			self.response.write("You are not logged!")
		else:
			session = get_current_session()
			ndb.delete_multi(DBAnalyzedURL.query(DBAnalyzedURL.owner == session['email']).fetch(keys_only=True))
			self.response.write("Ok")


class AboutHandler(webapp2.RequestHandler):
	"""
	Rendere the About page
	"""
	def get(self):
		template_values = {}

		if is_logged():
			template_values = get_person_session_values()
		else:
			template_values['url_login'] = users.create_login_url("/auth_google")

		# Render template and return
		template_values['page'] = "about"
		template = JINJA_ENVIRONMENT.get_template('about.html')
		self.response.write(template.render(template_values))


############
# # APIs # #
############
class FarooAPI(webapp2.RequestHandler):
	"""
	This class is used to call FAROO APIs asynchronously with AJAX and
	return a JSON response.
	"""
	def get(self):
		search = self.request.get('search')
		start = self.request.get('start', 0)
		nh = NewsHandler(True)
		data = nh.get_news(search, start)
		self.response.write(data)


class FlickrAPI(webapp2.RequestHandler):
	"""
	This class is used to call Flickr APIs asynchronously with AJAX and
	return a JSON response.
	"""
	def get(self):
		# gets
		label = self.request.get('label')
		per_page = self.request.get('per_page', 5)
		page = self.request.get('page', 1)

		if label != '':
			params = {
				'method': 'flickr.photos.search',
				'api_key': '902df328add6e1df503ca3c61f146216',
				'sort': 'relevance',
				'format': 'json',
				'nojsoncallback': '1',
				'text': label.encode('utf-8'),
				'page': page,
				'per_page': per_page
			}

			url = 'https://api.flickr.com/services/rest/'
			params = urllib.urlencode(params)
			url = '?'.join([url, params])
			resp = urllib.urlopen(url)
			data = resp.read().decode('utf-8')
			self.response.write(data)
		else:
			self.response.write("")


class YoutubeAPI(webapp2.RequestHandler):
	"""
	This class is used to call Youtube APIs asynchronously with AJAX and
	return a JSON response.
	"""
	def get(self):
		# gets
		search = self.request.get('search')
		if search != '':
			search_response = youtube.search().list(
				q=search,
				part="id",
				maxResults=3,
				type="video"
			).execute()
			data = json.dumps(search_response.get("items", []))
			self.response.write(data)
		else:
			self.response.write('[]')

"""
class RottenTomatoesAPI(webapp2.RequestHandler):
	def get(self):
		# gets
		search = self.request.get('search')

		if search != '':
			params = {
				'api_key': 'x57tfeabdkmgfkafhesva8ww',
				'q': search,
				'page': 1,
				'page_limit': 1
			}

			url = 'http://api.rottentomatoes.com/api/public/v1/movies.json'
			params = urllib.urlencode(params)
			url = '?'.join([url, params])
			resp = urllib.urlopen(url)
			data = resp.read().decode('utf-8')
			self.response.write(data)
		else:
			self.response.write('{}')
"""


################
# # OUT APIs # #
################
class ListUsersByEntityAnalyzeAPI(webapp2.RequestHandler):
	"""
	Exported API used to retrieve the list of users that extracted a given entity today.
	"""
	def get(self):
		# gets
		entity = self.request.get('entity')
		if entity != '':
			# Retrieve URLs by ENTITY
			q = DBEntityExtractedToday.query(DBEntityExtractedToday.entity == entity).fetch()
			users_list = []
			# loop
			for a in q:
				# retrieve all users by URL and group by users
				# so we get rid of duplicated
				q2 = DBAnalyzedURL.query(
					DBAnalyzedURL.url == a.url,
					projection=[DBAnalyzedURL.owner],
					distinct=True
				)
				q2.fetch()
				for b in q2:
					if b.owner not in users_list:
						users_list.append(b.owner)
			data = json.dumps(users_list)
			self.response.write(data)
		else:
			self.response.write('[]')


class ListUsersByUrlAnalyzeAPI(webapp2.RequestHandler):
	"""
	Exported API used to retrieve the list of users that extracted a given URL.
	"""
	def get(self):
		# gets
		url = self.request.get('url')
		order = self.request.get('order')
		if url != '':
			# Retrieve owner and email by url
			q = DBAnalyzedURL.query(DBAnalyzedURL.url == url)
			if order == 't':
				q = q.order(-DBAnalyzedURL.add_date)
			elif order == 'u':
				q = q.order(-DBAnalyzedURL.owner)
			q = q.fetch()
			analiz = []
			for a in q:
				analiz.append({'email': a.owner, 'timestamp': a.add_date.strftime('%Y-%m-%d %H:%M:%S')})
			data = json.dumps(analiz)
			self.response.write(data)
		else:
			self.response.write('[]')


class ListTopTenEntitiesAnalyzeAPI(webapp2.RequestHandler):
	"""
	Exported API used to retrieve the list of the 10 most extracted entities today.
	"""
	def get(self):
		# Retrieve ENTITIES
		q = DBEntityExtractedToday.query().fetch()
		q = (o.entity for o in q)
		entities = Counter(q).most_common(10)
		data = json.dumps(entities)
		self.response.write(data)


##############
# # GOOGLE # #
##############
class GoogleAuthorization(webapp2.RequestHandler):
	"""
	This class manage the Oauth2Authorization through Google+.
	If the User is not in the datastore, he will be added. If already present, he will be updated.
	"""
	@DECORATOR.oauth_aware
	def get(self):

		google_user = users.get_current_user()
		if google_user:

			email = google_user.email()
			# Logged
			# has credentials?
			if DECORATOR.has_credentials():
				print "Has credentials"

				try:
					# OAtuh2 call to google+ person
					httpd = DECORATOR.http()
					gplus_user = gplusService.people().get(userId='me').execute(http=httpd)
					session = get_current_session()
					session['email'] = email
					session['img_profile'] = gplus_user['image']['url']
					session['display_name'] = gplus_user['displayName']

					# Save the user, if already present it get updated
					my_user = DBUser.query(DBUser.email == email).get()
					if not my_user:
						print "- User not in db"

						# render template
						template_values = {'display_name': session['display_name']}
						template = JINJA_ENVIRONMENT.get_template('email_welcome.html')

						# send email
						message = mail.EmailMessage(
							sender="News Analyzer <support@news-manager.appspotmail.com>",
							subject="Welcome to News Analyzer"
						)
						message.to = email+" <"+email+">"
						message.html = template.render(template_values)
						message.send()
						print "Email inviata"
					else:
						print "- Already present"

					my_user = DBUser(
						email=email,
						display_name=session['display_name'],
						img_profile=session['img_profile']
					)
					my_user.put()

					self.redirect('/')

				except client.AccessTokenRefreshError:
					print "Access token expired."
					self.redirect('/auth_google')

			else:
				# No credentials, show credentials page
				print "No credentials"
				template_values = {
					'login_url': DECORATOR.authorize_url(),
				}
				template = JINJA_ENVIRONMENT.get_template('login.html')
				self.response.write(template.render(template_values))
		else:
			# Not logged, show google login
			self.redirect(users.create_login_url("/auth_google"))


class Logout(webapp2.RequestHandler):
	"""
	Logout from your Google account and remove credentials.
	"""
	def get(self):
		if is_logged():
			print "Logging out"
			session = get_current_session()
			if session.is_active():
				session.terminate()
				DECORATOR.set_credentials(None)
			self.redirect(users.create_logout_url('/'))
		else:
			self.redirect('/')


class OAuth2DecoratorMod(OAuth2Decorator):
	"""
	OAuth2DecoratorMod override OAuth2Decorator so that user do not get redirected
	"""
	def __init__(self, *args, **kwargs):
		super(OAuth2Decorator, self).__init__(*args, **kwargs)

	def oauth_aware(self, method):
		def setup_oauth(request_handler, *args, **kwargs):
			if self._in_error:
				self._display_error_message(request_handler)
				return

			user = users.get_current_user()
			# Don't use @login_decorator as this could be used in a POST request.
			if not user:
				request_handler.redirect(users.create_login_url(
					request_handler.request.uri))
				return

			self._create_flow(request_handler)

			self.flow.params['state'] = self._build_state_value(request_handler, user)
			self.credentials = self._storage_class(
				self._credentials_class, None,
				self._credentials_property_name, user=user).get()
			try:
				resp = method(request_handler, *args, **kwargs)
			finally:
				self.credentials = None
			return resp
		return setup_oauth


############
# # CRON # #
############
class SubmitEmailsCRON(webapp2.RequestHandler):
	"""
	CRON class that send emails with news based on users's filters.
	This can be called from outside for debugging purposes.
	"""
	def get(self):

		# Retrieve filters from DB for each users
		filters = DBFilter.query(DBFilter.email_hour != -1).fetch()
		for f in filters:
			tz = pytz.timezone('Europe/Rome')
			hour = datetime.datetime.now(tz).hour
			# Is this the correct hour of the day?
			if f.email_hour == hour:
				# retrieve news by keywords
				nh = NewsHandler(False)
				news = nh.get_news(f.keywords)

				# render template
				template_values = {'news': news, 'keywords': f.keywords}
				template = JINJA_ENVIRONMENT.get_template('email_news.html')

				# send email
				message = mail.EmailMessage(
					sender="News Analyzer <support@news-manager.appspotmail.com>",
					subject="News Analyzer Daily Filter Email"
				)
				message.to = f.owner+" <"+f.owner+">"
				message.html = template.render(template_values)
				message.send()
		self.response.write("ok")


class ClearTodayEntitiesCRON(webapp2.RequestHandler):
	"""
	CRON class that clear the datastore entity of today extracted entities.
	This can be called from outside for debugging purposes.
	"""
	def get(self):
		ndb.delete_multi(DBEntityExtractedToday.query().fetch(keys_only=True))
		self.response.write("ok")


class EmailWelcome(webapp2.RequestHandler):
	"""
	FOR DEBUG: a simple page where you can see the Welcome Email template.
	"""
	def get(self):
		template_values = {'display_name': 'Luca Gallinari'}
		template = JINJA_ENVIRONMENT.get_template('email_welcome.html')
		self.response.write(template.render(template_values))


class EmailNews(webapp2.RequestHandler):
	"""
	FOR DEBUG: a simple page where you can see the News Filters Email template.
	"""
	def get(self):
		nh = NewsHandler(False)
		template_values = {'news': nh.get_news()}
		template = JINJA_ENVIRONMENT.get_template('email_news.html')
		self.response.write(template.render(template_values))

# connect each route with the apppropriate controller (class)
routes = [
	('/', IndexHandler),
	('/filters', FiltersHandler),
	('/favorites', FavoritesHandler),
	('/analyze', AnalyzeHandler),
	('/about', AboutHandler),
	('/api/faroo', FarooAPI),
	('/api/flickr', FlickrAPI),
	('/api/youtube', YoutubeAPI),
	('/email_welcome', EmailWelcome),
	('/email_news', EmailNews),
	('/api/analyze/list_users_by_entity', ListUsersByEntityAnalyzeAPI),
	('/api/analyze/list_users_by_url', ListUsersByUrlAnalyzeAPI),
	('/api/analyze/list_top_ten_entities', ListTopTenEntitiesAnalyzeAPI),
	('/cron/submit_emails', SubmitEmailsCRON),
	('/cron/clear_today_entities', ClearTodayEntitiesCRON),
	('/logout', Logout),
	('/auth_google', GoogleAuthorization),
	(DECORATOR.callback_path, DECORATOR.callback_handler())]

app = webapp2.WSGIApplication(routes=routes, debug=True)
