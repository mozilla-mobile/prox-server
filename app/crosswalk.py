from app.constants import _tablePrefix as deployment
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
        if deployment == "production/":
            crosswalk = factualClient.table("crosswalk-us")
        else:
            crosswalk = factualClient.crosswalk()

        obj = crosswalk.filters({"url": yelpURL}).data()

        if len(obj) == 0:
            log.debug("Crosswalk empty for Yelp -> Factual " + yelpID)
            return mapping, True

        factualID = obj[0]["factual_id"]
        mapping["factualID"] = factualID
        mapping["factual"] = { "id": factualID }

        idList = crosswalk.filters({"factual_id": factualID}).data()
        
        if len(idList) == 0:
            log.warn("Crosswalk empty for Factual -> * " + yelpID + " " + factualID)
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