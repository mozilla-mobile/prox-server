import re

from app.clients import yelpClient
from app.util import slug

idPattern = re.compile("/([^/\?]*)(\?.*)?$")

def resolve(idObj):
    id = slug(idObj["url"])
    params = {
      "lang": "en"
    }
    return yelpClient.get_business(id, **params)