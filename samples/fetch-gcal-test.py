import datetime
import app.events as events
from pprint import pprint as pp

CAL_ID = 'hawaii247.com_dm8m04hk9ef3cc81eooerh3uos@group.calendar.google.com'
eventsList = events.fetchEventsFromGcal(CAL_ID, 45, datetime.timedelta(days=10))
for event in eventsList:
    if 'location' in event:
        eventObj = events.getGcalEventObj(event)
        pp(eventObj)
