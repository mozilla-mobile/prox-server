from app.clients import foursquareClient

MAX_PHOTOS = 5
PHOTO_SIZE = "cap500"

def resolve(idObj):
    fsId = idObj["namespace_id"]
    fsObj = foursquareClient.venues(fsId)["venue"]
    photos = fsObj["photos"]["groups"][0]["items"]
    photoUrls = [ photos[i]["prefix"] + PHOTO_SIZE + photos[i]["suffix"]
                  for i in range(MAX_PHOTOS)
                  if i < len(photos) ]
    return { "url": fsObj["canonicalUrl"],
             "images": photoUrls }
