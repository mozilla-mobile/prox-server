def placeRecord(biz, crosswalk, **dataProviders):
  # biz is the response object from the Yelp Search API
  return {
    "version": 1.0,
    "id": biz.id,
    "geo": {
      "lat": biz.location.coordinate.latitude,
      "lon": biz.location.coordinate.longitude
    },
    "images": [],
    "address": biz.location.display_address,

    "pullQuote": biz.snippet_text,

    "providers": {
      "yelp": {
        "rating": biz.rating,
        "reviewCount": biz.review_count,
        "ratingMax": 5,
        "url": biz.url
      }
    }
  }