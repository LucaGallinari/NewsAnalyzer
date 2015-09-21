""" classes for querying the dataTXT family
"""
from base import BaseDandelionRequest
from utils import AttributeDict

import urllib
import httplib
import json

class DataTXT(BaseDandelionRequest):
	""" class for accessing the dataTXT family
	"""
	def nex(self, text, **params):
		if 'min_confidence' not in params:
			params['min_confidence'] = 0.8

		url = "api.dandelion.eu/datatxt/nex/v1"
		params['$app_id'] = self.app_id
		params['$app_key'] = self.app_key
		params['url'] = text
		params = urllib.urlencode(params)
		headers = {"User-Agent": 'python-dandelion-eu/0.2.2'}

		c = httplib.HTTPSConnection(url)
		c.request("post", "", params, headers)
		response = c.getresponse()
		print response.status, response.reason
		data = response.read()
		data = json.loads(data, object_hook=AttributeDict)
		return data

		# req = urllib2.Request(url, params)
		# try:
		# 	response = urllib2.urlopen(req)
		# except urllib2.URLError, e:
		# 	print 'you got an error with the code', e
		# 	return None
		# return response
		# return self.do_request(dict(params, text=text), ('nex', 'v1'))

	def sim(self, text1, text2, **params):
		return self.do_request(
			dict(params, text1=text1, text2=text2), ('sim', 'v1')
		)

	def li(self, text, **params):
		return self.do_request(
			dict(params, text=text), ('li', 'v1')
		)

	def _get_uri_tokens(self):
		return 'datatxt',