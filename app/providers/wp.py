import wikipedia

from app.util import slug

def resolve(idObj):
  pageID = slug(idObj["url"])
  return wikipedia.page(pageID, preload=True)