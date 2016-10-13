from pprint import pprint as pp
import requests

from app.clients import googleapikey

CAL_ID = "hawaii247.com_dm8m04hk9ef3cc81eooerh3uos@group.calendar.google.com"
CALENDAR_URL = "https://www.googleapis.com/calendar/v3/calendars/{}/events?key={}"

def fetch(calId, maxResults):
    r = requests.get(CALENDAR_URL.format(CAL_ID, googleapikey), params={"maxResults": maxResults})
    pp(r.json())

fetch(CAL_ID, 5)
