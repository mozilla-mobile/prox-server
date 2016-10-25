from app.clients   import factualClient
from app.util      import log
from factual       import APIException

CROSSWALK_CACHE_VERSION = 1

def getVenueIdentifiers(yelpID):
    yelpURL = "https://yelp.com/biz/%s" % yelpID
    mapping = {
      "id": yelpID,
      "version": CROSSWALK_CACHE_VERSION,
      "yelp": {
        "url": yelpURL
      }
    }
    try:
        obj = factualClient.crosswalk().filters({"url": yelpURL}).data()

        if len(obj) == 0:
            return mapping, True

        factualID = obj[0]["factual_id"]
        mapping["factualID"] = factualID

        idList = factualClient.crosswalk().filters({"factual_id": factualID}).data()

        for idObj in idList:
            namespace = idObj["namespace"]
            del idObj["factual_id"]
            del idObj["namespace"]
            mapping[namespace] = idObj
        return mapping, True
    except APIException:
        log.error("Factual API failed again")
    except Exception:
        log.exception("Factual problem " + yelpID)
    return mapping, False