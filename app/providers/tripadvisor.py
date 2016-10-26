import re
import requests

from app.clients import tripadvisorkey

idPattern = re.compile("-d([0-9]*)-")

def getNumId(idStr):
    return idPattern.search(idStr).groups(1)[0]

TRIP_ADVISOR_API = "https://api.tripadvisor.com/api/partner/2.0/location/{}"
params = { "key": tripadvisorkey }

def resolve(idObj):
    url = idObj["url"]
    taId = getNumId(url)
    apiUrl = TRIP_ADVISOR_API.format(taId)
    return requests.get(apiUrl, params).json()
