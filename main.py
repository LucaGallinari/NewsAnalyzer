#!/usr/bin/env python

# SYSTEM
# import os
import urllib
import httplib2
import webapp2
import jinja2
import json
import datetime

# GOOGLE
from google.appengine.api import users
from google.appengine.api import memcache
from oauth2client.appengine import OAuth2Decorator
from oauth2client import client
from apiclient.discovery import build
from gaesessions import get_current_session

# API + LIBS
from models import *
from libs import feedparser
from API import faroo
from API.dandelion import DataTXT


http = httplib2.Http(memcache)
DECORATOR = OAuth2Decorator(
	client_id='99266390307-ic0seu51ghcq84m0bfhh3etdeafo81pl.apps.googleusercontent.com',
	client_secret='nfdBT_BReUhhiGrrsmJoe9WA',
	scope='https://www.googleapis.com/auth/plus.me')

gplusService = build("plus", "v1", http=http)
youtube = build('youtube', 'v3', developerKey='AIzaSyCWKe3sGVhfTmaYCvPf2jW-d_2QLEod7Rw')

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.PackageLoader('main', 'templates'),
	extensions=['jinja2.ext.autoescape', 'jinja2.ext.loopcontrols'],
	autoescape=True)


# Jinja Filter Extension
def ccontains(value, arg):
	return arg in value
JINJA_ENVIRONMENT.filters['ccontains'] = ccontains


# Check if logged by using sessions
def is_logged():
	session = get_current_session()
	try:
		email = session['email']
		return True
	except KeyError:
		return False


# Get person session values
def get_person_session_values():
	session = get_current_session()
	values = {
		'email': session['email'],
		'img_profile': session['img_profile'],
		'display_name': session['display_name'],
		'url_logout': '/logout'
	}
	return values


# OAuth2DecoratorMod override OAuth2Decorator so that user do not get redirected
# if not logged TODO: ?
class OAuth2DecoratorMod(OAuth2Decorator):

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


class IndexHandler(webapp2.RequestHandler):

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
	def get(self):
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

	# POST for INSERT
	def post(self):
		if not is_logged():
			self.response.write("You are not logged!")
		else:
			# Retrieve data
			session = get_current_session()
			name = self.request.get('name')
			keywords = self.request.get('keywords')
			email_hour = self.request.get('email_hour')

			# Some checks
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

			# Save the filter
			my_filter = DBFilter(
				owner=session['email'],
				name=name,
				keywords=keywords,
				email_hour=email_hour
			)
			key = my_filter.put()
			self.response.write("Ok: " + str(key.id()))

	# PUT for MODIFICATION
	def put(self):
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

	# DELETE for DELETE
	def delete(self):
		if not is_logged():
			self.response.write("You are not logged!")
		else:
			session = get_current_session()
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
			DBFilter(id=filter_id, owner=session['email']).key.delete()
			self.response.write("Ok")


class FavoritesHandler(webapp2.RequestHandler):
	def get(self):
		if not is_logged():
			self.redirect(users.create_login_url("/auth_google"))
		else:
			template_values = get_person_session_values()

			# Retrieve favorites from DB
			q = DBFavorite.query(DBFavorite.owner == template_values['email']).fetch()
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

	# POST for INSERT
	def post(self):
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
					date = datetime.datetime.fromtimestamp(date_l).strftime('%Y-%m-%d %H:%M:%S')
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

	# DELETE for DELETE
	def delete(self):
		if not is_logged():
			self.response.write("You are not logged!")
		else:
			session = get_current_session()
			fav_id = self.request.get('id')
			if fav_id is None:
				self.response.write("ID not specified!")
				return
			if fav_id == "":
				self.response.write("ID is empty!")
				return

			try:
				fav_id = long(fav_id)
			except ValueError:
				self.response.write("ID is not a valid integer!")
				return
			DBFavorite(id=fav_id, owner=session['email']).key.delete()
			self.response.write("Ok")


class NewsHandler:
	json = False

	def __init__(self, retjson):
		self.json = retjson

	def get_news(self, search='', start=0):
		favs = []

		# Retrieve favorites from DB
		if is_logged():
			session = get_current_session()
			q = DBFavorite.query(DBFavorite.owner == session['email']).fetch()
			for f in q:
				favs.append({'id': f.key.id(), 'url': f.url})

		# Search by keywords?
		if search == '':
			search = None
		if start == '':
			start = 0
		# Retrieve news
		freq = faroo.Faroo()
		data = freq.param('src', 'news').param('start', start).query(self.json, search)

		# if the data retrieved are in json format, decode them
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
							date_l = long(n['date'])
							n['date'] = datetime.datetime.fromtimestamp(date_l).strftime('%Y-%m-%d %H:%M:%S')
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
								date_l = long(n.date)
								n.date = datetime.datetime.fromtimestamp(date_l).strftime('%Y-%m-%d %H:%M:%S')
							except ValueError:
								# it's a string, useless command below
								n.date = str(n.date)
			else:
				news = []

		# must return json formatted data
		if self.json:
			news = json.dumps(data)

		return news


class FarooAPI(webapp2.RequestHandler):
	def get(self):
		search = self.request.get('search')
		start = self.request.get("start")
		nh = NewsHandler(True)
		data = nh.get_news(search, start)
		self.response.write(data)


class AnalyzeHandler(webapp2.RequestHandler):
	def get(self):
		template_values = {}

		if is_logged():
			template_values = get_person_session_values()

		url = self.request.get('url')
		if url is not None:
			if url != '':
				# if url != '':
				# some url checks
				datatxt = DataTXT(app_id='ff66f767', app_key='e22401da7ae5647cb5b7070dea5e0e7f')
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
										else:
											e.categ = 'Concept'
								else:
									e.categ = 'Concept'
							else:
								e.categ = 'Concept'
							newdata.append(e)
					template_values['data'] = newdata
				else:
					template_values['data'] = []
				template_values['url'] = url

		# Render template and return
		template_values['page'] = "analyze"
		template = JINJA_ENVIRONMENT.get_template('analyze.html')
		self.response.write(template.render(template_values))


# OTHERS

class Flickr(webapp2.RequestHandler):
	def get(self):
		params = {
			'method': 'flickr.photos.search',
			'api_key': '902df328add6e1df503ca3c61f146216',
			# 'secret': '26bd5a1a656ee460',
			'text': 'Linkin Park',
			# 'tag_mode ': 'all',
			'sort': 'relevance',
			'per_page': '10',
			'format': 'json',
			'nojsoncallback': '1'
		}

		url = 'https://api.flickr.com/services/rest/'
		params = urllib.urlencode(params)
		url = '?'.join([url, params])
		resp = urllib.urlopen(url)
		data = resp.read().decode('utf-8')
		data = json.loads(data)

		template_values = {
			'imgs': data
		}
		template = JINJA_ENVIRONMENT.get_template('flickr.html')
		self.response.write(template.render(template_values))


class Youtube(webapp2.RequestHandler):
	def get(self):

		search_response = youtube.search().list(
			q="Linkin Park",
			part="id,snippet",
			maxResults=5
		).execute()

		videos = []

		for search_result in search_response.get("items", []):
			if search_result["id"]["kind"] == "youtube#video":
				videos.append({
					'title': search_result["snippet"]["title"],
					'id': search_result["id"]["videoId"]
				})

		template_values = {
			'videos': videos
		}
		template = JINJA_ENVIRONMENT.get_template('youtube.html')
		self.response.write(template.render(template_values))


class GoogleNews(webapp2.RequestHandler):
	def get(self):
		params = {
			'q': 'pechino atletica',
			'output': 'rss',
			'num': 10,
			'hl': 'it',
		}
		url = 'http://news.google.com/news'
		params = urllib.urlencode(params)
		url = '?'.join([url, params])
		resp = urllib.urlopen(url)
		data = resp.read().decode('utf-8')
		data = feedparser.parse(data)
		template_values = {
			'resp': data['entries']
		}
		template = JINJA_ENVIRONMENT.get_template('home.html')
		self.response.write(template.render(template_values))


class Logout(webapp2.RequestHandler):
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


class GoogleAuthorization(webapp2.RequestHandler):
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
						# print "   inserted"
						# TODO: Email
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


routes = [
	('/', IndexHandler),
	('/filters', FiltersHandler),
	('/favorites', FavoritesHandler),
	('/api/faroo', FarooAPI),
	('/analyze', AnalyzeHandler),

	('/flickr', Flickr),
	('/youtube', Youtube),
	('/logout', Logout),
	('/auth_google', GoogleAuthorization),
	(DECORATOR.callback_path, DECORATOR.callback_handler())]

app = webapp2.WSGIApplication(routes=routes, debug=True)
