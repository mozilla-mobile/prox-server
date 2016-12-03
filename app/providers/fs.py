from app.clients import foursquareClient
from app.util import slug

MAX_PHOTOS = 5
PHOTO_SIZE = "cap500"

def resolve(idObj):
    fsId = slug(idObj["url"])
    fsObj = foursquareClient.venues(fsId)["venue"]
    photoGroups = fsObj["photos"]["groups"]
    if len(photoGroups) > 0:
        photos = photoGroups[0]["items"]
        photoUrls = [ photos[i]["prefix"] + PHOTO_SIZE + photos[i]["suffix"]
                      for i in range(MAX_PHOTOS)
                      if i < len(photos) ]
        return { "url": fsObj["canonicalUrl"],
                 "images": photoUrls }
    else: return None
