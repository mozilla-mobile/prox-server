import json
from factual import Factual

def getCredentials():
    json_data = open("keys.local.json")
    return json.load(json_data)

creds = getCredentials()
factual = Factual(creds["FACTUAL_KEY"], creds["FACTUAL_SECRET"])

def fetchData(lat, lon):
    from factual.utils import circle
    places = factual.table("places")
    data = places.search("beach").geo(circle(lat, lon, 1000)).data()
    print(json.dumps(data))
    return data

def fetchCrosswalk(factualIDs):
    oneOfFilter = [{ "name": {"$eq": f}} for f in factualIDs]
    print(json.dumps(oneOfFilter))

fetchData(19.915403, -155.887403)
#fetchCrosswalk([1,2,3])
