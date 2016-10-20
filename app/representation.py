def venueRecord(biz, **details):
    # biz is the response object from the Yelp Search API
    providers = {}
    images = []
    hours = []
    categories = set()
    if "yelp" in details:
      info = details["yelp"]
      providers["yelp"] = {
        "rating": biz.rating,
        "totalReviewCount": biz.review_count,
        "ratingMax": 5,
        "summary": biz.snippet_text,
        "url": biz.url
      }
      images = images + info["photos"]
      hours = info["hours"][0]["open"]
      categories |= set([ c["title"] for c in info["categories"] if "title" in c])

    if "wikipedia" in details:
      info = details["wikipedia"]
      providers["wikipedia"] = {
        "url": info.url,
        "summary": info.summary
      }
      images = images + info.images

    # Ensure we're not getting SVG or other weird formats.
    images = [url for url in images if url.split(".")[-1] in ["jpg", "jpeg", "png"]]

    return {
      "id": biz.id,
      "name": biz.name,
      "hours": hours,
      "url": "https://mozilla.org", # TODO
      "categories": list(categories),
      "coordinates": {
        "lat": biz.location.coordinate.latitude,
        "lon": biz.location.coordinate.longitude
      },
      "images": images,
      "address": biz.location.display_address,
      "summary": biz.snippet_text,
      "providers": providers,
      "version": 1.0
    }

def createKey(biz):
    return biz.id

def geoRecord(biz):
    return _geoRecord(biz.location.coordinate.latitude, biz.location.coordinate.longitude)

def _geoRecord(lat, lon):
    import pygeohash as pgh
    return {
       "g": pgh.encode(lat, lon, precision=8),
       "l": [lat, lon]
    }