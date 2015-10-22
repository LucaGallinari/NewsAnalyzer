
from google.appengine.ext import ndb


class DBUser(ndb.Model):
    """ Model for a simple User """
    email = ndb.StringProperty(indexed=True, required=True)
    display_name = ndb.StringProperty(required=True, indexed=False)
    img_profile = ndb.StringProperty(required=True, indexed=False)
    join_date = ndb.DateTimeProperty(auto_now_add=True, indexed=False)


class DBFilter(ndb.Model):
    """ Model of a filter, represented by some keywords (just a string, not a list) """
    owner = ndb.StringProperty(indexed=True, required=True)
    name = ndb.StringProperty(required=True, indexed=False)
    keywords = ndb.StringProperty(required=True, indexed=False)
    email_hour = ndb.IntegerProperty(required=True)


class DBFavorite(ndb.Model):
    """ Model of a favorite news """
    owner = ndb.StringProperty(indexed=True, required=True)
    title = ndb.StringProperty(required=True, indexed=False)
    kwic = ndb.StringProperty(required=True, indexed=False)
    url = ndb.StringProperty(required=True, indexed=False)
    iurl = ndb.StringProperty(required=True, indexed=False)
    author = ndb.StringProperty(required=True, indexed=False)
    domain = ndb.StringProperty(required=True, indexed=False)
    date = ndb.StringProperty(required=True, indexed=False)
    add_date = ndb.DateTimeProperty(auto_now_add=True)


class DBAnalyzedURL(ndb.Model):
    """
    Model for an analyzed URL, with owner and url explicitly inxdexed to allow
    search queries by those two properties.
    """
    owner = ndb.StringProperty(indexed=True, required=True)
    url = ndb.StringProperty(indexed=True, required=True)  # indexed because we search by URL
    add_date = ndb.DateTimeProperty(auto_now_add=True)


class DBEntityExtractedToday(ndb.Model):
    """
    Model for an extracted entity, with entity and url explicitly inxdexed to allow
    search queries by those two properties.
    """
    url = ndb.StringProperty(indexed=True, required=True)
    entity = ndb.StringProperty(indexed=True, required=True)  # indexed because we search by ENTITY
