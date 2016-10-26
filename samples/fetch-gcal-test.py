import datetime
import app.events as events
import app.request_handler as request_handler
from pprint import pprint as pp

def testGcalEventLoad():
    request_handler.loadCalendarEvents(30, datetime.timedelta(days=5))

testGcalEventLoad()

'''
eventsList = events.fetchEventsFromGcal(CAL_ID, 45, datetime.timedelta(days=10))
for event in eventsList:
    if 'location' in event:
        eventObj = events.getGcalEventObj(event)
        pp(eventObj)
'''
