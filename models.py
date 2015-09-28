
from google.appengine.ext import ndb


class DBUser(ndb.Model):
    email = ndb.StringProperty(indexed=True, required=True)
    display_name = ndb.StringProperty(required=True)
    img_profile = ndb.StringProperty(required=True)
    join_date = ndb.DateTimeProperty(auto_now_add=True)


class DBFilter(ndb.Model):
    owner = ndb.StringProperty(indexed=True, required=True)
    name = ndb.StringProperty(required=True)
    keywords = ndb.StringProperty(required=True)
    email_hour = ndb.IntegerProperty(required=True)
