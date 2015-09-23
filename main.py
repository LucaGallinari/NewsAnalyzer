#!/usr/bin/env python

# SYSTEM
# import os
import urllib
import httplib2
import webapp2
import jinja2
import json

# GOOGLE
from google.appengine.api import users
from google.appengine.api import memcache
from oauth2client.appengine import OAuth2Decorator
from oauth2client import client
from apiclient.discovery import build

# API + LIBS
# from models import *
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
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)


# Jinja Filter Extension
def ccontains(value, arg):
	return arg in value
JINJA_ENVIRONMENT.filters['ccontains'] = ccontains


class OAuth2DecoratorMod(OAuth2Decorator):

	def __init__(self, *args, **kwargs):
		super(OAuth2Decorator, self).__init__(*args, **kwargs)

	def oauth_aware(self, method):
		"""Decorator that sets up for OAuth 2.0 dance, but doesn't do it.

		Does all the setup for the OAuth dance, but doesn't initiate it.
		This decorator is useful if you want to create a page that knows
		whether or not the user has granted access to this application.
		From within a method decorated with @oauth_aware the has_credentials()
		and authorize_url() methods can be called.

		Args:
			method: callable, to be decorated method of a webapp.RequestHandler
			instance.
		"""

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


class MainHandler(webapp2.RequestHandler):
	"""
		This trick allows non authenticated user to access this page
		without having to login with a google account. Login is required
		by default in the "oauth_aware" method.
	"""
	@DECORATOR.oauth_aware
	def get_httpd_decorator(self):
		httpd = DECORATOR.http()
		if httpd is None:
			raise client.AccessTokenRefreshError
		return httpd

	def get(self):
		template_values = {}
		google_user = users.get_current_user()
		if google_user:
			try:
				# OAtuh2 call to google+ person
				httpd = self.get_httpd_decorator()
				people_resource = gplusService.people()
				people_document = people_resource.get(userId='me').execute(http=httpd)

				google_user = users.get_current_user()
				email = google_user.email()

				# person related info
				template_values['person_name'] = people_document['displayName']
				template_values['person_image_url'] = people_document['image']['url']
				template_values['person_email'] = email
				template_values['url_logout'] = users.create_logout_url('/')

			except client.AccessTokenRefreshError:
				print "Access token expired."
				self.redirect('/auth_google')

		else:
			template_values['url_login'] = users.create_login_url("/auth_google")

		# Search by keywords?
		search = self.request.get('search')
		if search == '':
			search = None
		else:
			template_values['search'] = search

		# Retrieve news
		freq = faroo.Faroo()
		data = freq.param('src', 'news').query(False, search)

		# No news found?
		if hasattr(data, 'results'):
			if data.results is None:
				template_values['news'] = []
			else:
				template_values['news'] = data.results
		else:
			template_values['news'] = []
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


class FarooAPI(webapp2.RequestHandler):
	def get(self):
		# Get params
		search = self.request.get('search')
		start = self.request.get("start")
		if search == '':
			search = None

		# Retrieve news
		freq = faroo.Faroo()
		data = freq.param('src', 'news').param('start', start).query(True, search)

		self.response.write(data)


class Dandelion(webapp2.RequestHandler):
	def get(self):
		datatxt = DataTXT(app_id='ff66f767', app_key='e22401da7ae5647cb5b7070dea5e0e7f')
		data = datatxt.nex(
			'http://www.inquisitr.com/2376034/hurricane-season-2015-predictions-hurricane-erikas-path-will-dump-rain-on-florida/',
			include_categories=True,
			include_types=True
		)
		template_values = {
			'news': data.annotations
		}
		template = JINJA_ENVIRONMENT.get_template('dandelion.html')
		self.response.write(template.render(template_values))


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


class GoogleAuthorization(webapp2.RequestHandler):
	@DECORATOR.oauth_aware
	def get(self):
		# has credentials? redir to internal page
		if DECORATOR.has_credentials():
			try:
				print "Has credentials"
				self.redirect('/')
			except client.AccessTokenRefreshError:
				# TODO: ?
				print "Access token expired."
				self.redirect('/auth_google')
		else:
			# no credentials
			template_values = {
				'login_url': DECORATOR.authorize_url(),
			}
			template = JINJA_ENVIRONMENT.get_template('login.html')
			self.response.write(template.render(template_values))

'''
if google_user:
	email = google_user.email()

	my_user = DBUser.query(DBUser.email == email).get()
	if not my_user:
		print "- User not in db"

		my_user = DBUser(email=email, nickname=google_user.nickname())
		my_user.put()
		print "   inserito"

		# TODO: Email
	else:
		print "- Already present"

	url_log = users.create_logout_url(self.request.uri)
	url_linktext = 'Logout'

else:
	email = 'NONE'
	url_log = users.create_login_url(self.request.uri)
	url_linktext = 'Login'

'''


routes = [
	('/', MainHandler),
	('/api/faroo', FarooAPI),
	('/flickr', Flickr),
	('/youtube', Youtube),
	('/dandelion', Dandelion),
	('/auth_google', GoogleAuthorization),
	(DECORATOR.callback_path, DECORATOR.callback_handler())]

app = webapp2.WSGIApplication(routes=routes, debug=True)
