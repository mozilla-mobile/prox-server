import re

from app.clients import yelp3Client
from app.util import slug

idPattern = re.compile("/([^/\?]*)(\?.*)?$")

def resolve_with_key(key):
    return yelp3Client.request("/businesses/{0}".format(key))

def resolve(idObj):
    key = slug(idObj["url"])
    return resolve_with_key(key)
