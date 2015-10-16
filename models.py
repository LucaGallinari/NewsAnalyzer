
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


class DBFavorite(ndb.Model):
    owner = ndb.StringProperty(indexed=True, required=True)
    title = ndb.StringProperty(required=True)
    kwic = ndb.StringProperty(required=True)
    url = ndb.StringProperty(required=True)
    iurl = ndb.StringProperty(required=True)
    author = ndb.StringProperty(required=True)
    domain = ndb.StringProperty(required=True)
    date = ndb.StringProperty(required=True)
    add_date = ndb.DateTimeProperty(auto_now_add=True)


class DBAnalyzedURL(ndb.Model):
    owner = ndb.StringProperty(indexed=True, required=True)
    url = ndb.StringProperty(indexed=True, required=True)  # indexed because we search by URL
    add_date = ndb.DateTimeProperty(auto_now_add=True)


class DBEntityExtractedToday(ndb.Model):
    url = ndb.StringProperty(indexed=True, required=True)
    entity = ndb.StringProperty(indexed=True, required=True)  # indexed because we search by ENTITY
