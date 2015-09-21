
from google.appengine.ext import ndb


class DBUser(ndb.Model):
    email = ndb.StringProperty(indexed=True, required=True)
    nickname = ndb.StringProperty(indexed=False)
    join_date = ndb.DateTimeProperty(auto_now_add=True)
