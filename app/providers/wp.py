import wikipedia

from app.util import slug

def resolve(idObj):
    pageID = slug(idObj["url"])
    page = wikipedia.page(pageID, preload=True)
    return {
      "url": page.url,
      "summary": page.summary,
      "images": page.images,
    }