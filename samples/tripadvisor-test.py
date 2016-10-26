import json
from pprint import pprint as pp
import re
import requests

from app.clients import tripadvisorkey

TRIP_ADVISOR_API = "https://api.tripadvisor.com/api/partner/2.0/location/{}"
params = { "key": tripadvisorkey }

TA_ids = ["d4868306", "d2701835", "d2368658"]

def fetchTABusiness(bizId):
    url = TRIP_ADVISOR_API.format(getNumId(bizId))
    r = requests.get(url, params)
    return r.json()

pattern = re.compile("^.??([0-9]*)$")
def getNumId(idStr):
    return pattern.search(idStr).groups(1)[0]

TAList = []
for i in TA_ids:
    TAList.append(fetchTABusiness(i))

print(json.dumps(TAList, indent=2))
