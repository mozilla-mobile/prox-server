import datetime
import app.events as events
import app.request_handler as request_handler
import json

'''
def testGcalEventLoad():
    request_handler.loadCalendarEvents(30, datetime.timedelta(days=5))

testGcalEventLoad()
'''

CAL_ID = 'hawaii247.com_dm8m04hk9ef3cc81eooerh3uos@group.calendar.google.com'

def fetchGcalEvents():
    eventsList = events.fetchEventsFromGcal(CAL_ID, 1000, datetime.timedelta(days=5), datetime.datetime.strptime("2016-12-05", "%Y-%m-%d"))
    return [ events.getGcalEventObj(event) for event in eventsList if 'location' in event ]

print(json.dumps(fetchGcalEvents(), indent=2))
