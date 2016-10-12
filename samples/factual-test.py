import json
from factual import Factual

def getCredentials():
    json_data = open("keys.local.json")
    return json.load(json_data)


creds = getCredentials()
factualCreds = creds["factual"]
factual = Factual(factualCreds["key"], factualCreds["secret"])

def fetchData(lat, lon):
    from factual.utils import circle
    places = factual.table("places")
    data = places.search("bar").geo(circle(lat, lon, 1000)).data()
    return data

def fetchCrosswalk(factualIDs):
    namespaces = ["yelp", "tripadvisor", "wikipedia", "instagram_places"]
    oneOfFilter = [{ "factual_id": {"$eq": f}} for f in factualIDs]
    idFilter = { "$or": oneOfFilter }
    oneOfFilter = [ { "namespace": {"$eq": ns }} for ns in namespaces]
    namespaceFilter = { "$or": oneOfFilter }
    totalFilter = { "$and": [idFilter, namespaceFilter]}
    return factual.crosswalk().filters(totalFilter).data()


factualPlaces = fetchData(19.915403, -155.887403)
factualIDs = [ p["factual_id"] for p in factualPlaces ]
idArray = fetchCrosswalk(factualIDs)
print(json.dumps(idArray, indent=4))
#fetchCrosswalk([1,2,3])
