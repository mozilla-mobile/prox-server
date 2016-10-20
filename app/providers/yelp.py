import re

from app.clients import yelp3Client
from app.util import slug

idPattern = re.compile("/([^/\?]*)(\?.*)?$")

def resolve(idObj):
    key = slug(idObj["url"])
    params = {
      "lang": "en"
    }
    return yelp3Client.request("/businesses/%s" % key)