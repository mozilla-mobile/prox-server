import json
from pprint import pprint

from factual import Factual

def getCredentials():
    json_data = open("keys.local.json")
    return json.load(json_data)

def fetchData(lat, lon):
    creds = getCredentials()
    factual = Factual(creds["FACTUAL_KEY"], creds["FACTUAL_SECRET"])
    places = factual.table("places")
    pprint(places.schema())

fetchData(0, 0)