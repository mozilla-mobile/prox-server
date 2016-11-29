import re

from app.clients import yelp3Client
from app.util import slug

idPattern = re.compile("/([^/\?]*)(\?.*)?$")

def resolve(idObj):
    key = slug(idObj["url"])
    params = {
      "lang": "en"
    }
    key = key.encode('utf-8').strip()
    return yelp3Client.request("/businesses/{0}".format(key))