
def venueRecord(biz, **details):
    # biz is the response object from the Yelp Search API

    from collections import OrderedDict
    # h is derived from the providers, but for the main body of the record.
    # h is for header.
    h = {
      "url"        : "https://mozilla.org",
      "description": {},
      "categories" : OrderedDict(),
      "images"     : [],
      "hours"      : [],
    }
    providers = {}
    
    # Yelp.
    if "yelp" in details:
      info = details["yelp"]
      providers["yelp"] = {
        "rating"          : biz.rating,
        "totalReviewCount": biz.review_count,
        "ratingMax"       : 5,
        "description"     : biz.snippet_text,
        "url"             : biz.url
      }
      h["images"]      += info["photos"]
      h["hours"]       = info["hours"][0]["open"]
      h["description"] = _descriptionRecord("yelp", biz.snippet_text)
      h["categories"].update([ (c["title"], _categoryRecord(c["alias"], c["title"])) for c in info["categories"] if "title" in c])


    # Wikipedia.
    if "wikipedia" in details:
      info = details["wikipedia"]
      providers["wikipedia"] = {
        "url"        : info.url,
        "description": info.summary
      }
      h["description"] = _descriptionRecord("wikipedia", info.summary)
      h["images"]     += info.images

    # Ensure we're not getting SVG or other weird formats.
    h["images"] = [url for url in h["images"] if url.split(".")[-1] in ["jpg", "jpeg", "png"]]

    return {
      "version"    : 1,
      "id"         : biz.id,
      
      "name"       : biz.name,
      "description": h["description"],
      
      "url"        : h["url"],
      "phone"      : biz.display_phone,
      
      "address"    : biz.location.display_address,
      "coordinates": {
        "lat": biz.location.coordinate.latitude,
        "lng": biz.location.coordinate.longitude
      },

      "categories" : h["categories"].values(),
      "providers"  : providers,
      
      "images"     : h["images"],
      "hours"      : h["hours"],
    }

def _categoryRecord(id, text):
    return {
      "id"  : id,
      "text": text,
    }

def _descriptionRecord(provider, text, url = None):
    return {
      "text"    : text,
      "provider": provider,
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