import json
from app.clients import factualClient

def fetchData(lat, lon):
    from factual.utils import circle
    places = factualClient.table("places")
    data = places.search("bar").geo(circle(lat, lon, 1000)).data()
    return data

def fetchCrosswalk(factualIDs):
    namespaces = ["yelp", "tripadvisor", "wikipedia", "instagram_places"]
    oneOfFilter = [{ "factual_id": {"$eq": f}} for f in factualIDs]
    idFilter = { "$or": oneOfFilter }
    oneOfFilter = [ { "namespace": {"$eq": ns }} for ns in namespaces]
    namespaceFilter = { "$or": oneOfFilter }
    totalFilter = { "$and": [idFilter, namespaceFilter]}
    return factualClient.crosswalk().filters(totalFilter).data()


factualPlaces = fetchData(19.915403, -155.887403)
factualIDs = [ p["factual_id"] for p in factualPlaces ]
idArray = fetchCrosswalk(factualIDs)
print(json.dumps(idArray, indent=4))
#fetchCrosswalk([1,2,3])

def findFactualIDs(yelpBusinesses):
    totalFilter = {
      "$or": [ {"url": {"$eq": "https://yelp.com/biz/%s" % biz.id }} for biz in yelpBusinesses]
    }
    crosswalkObjects = factualClient.crosswalk().filters(totalFilter).data()
    return [biz["factual_id"] for biz in crosswalkObjects]    

#factualIDs = findFactualIDs(businesses)

def fetchCrosswalk(factualIDs):
    namespaces = ["tripadvisor", "wikipedia", "facebook"]
    oneOfFilter = [{ "factual_id": {"$eq": f}} for f in factualIDs]
    idFilter = { "$or": oneOfFilter }
    oneOfFilter = [ { "namespace": {"$eq": ns }} for ns in namespaces]
    namespaceFilter = { "$or": oneOfFilter }
    totalFilter = { "$and": [idFilter, namespaceFilter]}
    return factualClient.crosswalk().filters(totalFilter).data()

