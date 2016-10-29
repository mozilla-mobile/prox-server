import json
import string
import sys
import time

from app.clients import yelp3Client

# Excercises the Yelp Business API to download upto 1000 businesses
# Outputs progress to stderr
# Outputs raw JSON to stdout
# Once the raw JSON is available, use jq to process.
# % brew install jq 
# % python -m samples.crawl_yelp > top1000.json
# % jq '[.[] | { name: .name, rating: .rating, review_count: .review_count, categories: [.categories[] | .alias], distance: .distance, coord: [ .coordinates.latitude,  .coordinates.longitude] } ]' top1000.json

lat, lon = 19.915403, -155.8961577 # Waikaloa
categories=None # ["beaches", "hotels"]
radius = 40000 # metres

def getLocality(lat, lon, radius_filter=40000, offset=0, **kwargs):
    from app.clients import yelp3Client
    queryParams = "latitude=" + str(lat) + "&longitude=" + str(lon) + "&limit=50&offset=" + str(offset) + "&radius=" + str(radius_filter) + "&sort_by=review_count")
    if categories is not None:
        queryParams += "&categories=" + string.join(categories, ",")

    return yelp3Client.request("/businesses/search?" + queryParams)

locality = getLocality(lat, lon, 
  radius_filter=radius, 
  offset=0,
)

max=min(1000, locality["total"])
all = []

sys.stderr.write("Downloading " + str(max) + " businesses: ")

for offset in range(0, max, 50):
    res = None
    errCount = 0
    while res is None:
        sys.stderr.write(str(offset) + ", ")
        try:
            res = getLocality(lat, lon, # Waikaloa
              radius_filter=radius, 
              offset=offset, 
              limit=50, 
              # category_filter=categories
            )
        except KeyboardInterrupt:
            break
        except Exception:
            errCount += 1
            
            if errCount > 3:
                break
            try:
                time.sleep(5)
            except KeyboardInterrupt:
                break

    if res is None:
        break

    all += res["businesses"]
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        break

print(json.dumps(all, indent=2))
