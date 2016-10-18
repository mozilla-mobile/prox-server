import requests
from pprint import pprint as pp

from app.clients import eventfulkey
import app.search as search

EVENTFUL_URL = 'https://api.eventful.com/json/events/search'
SF_LATLONG = "37.789225, -122.389521"
NUM_RESULTS = 10

params = { 'app_key': eventfulkey,
           'units': 'mi',
           'date': 'Today',
           'sort_order': 'relevance' }

def fetchEventsFromLocation(latlong, maxResults, radius):
    params['location'] = latlong
    params['page_size'] = maxResults
    params['within'] = radius

    r = requests.get(EVENTFUL_URL, params)
    eventList = r.json()['events']['event']
    return eventList

def getEventfulEventObj(event):
    location = { 'lat': event['latitude'], 'lng': event['longitude'] }
    # print(str(event['venue_name']) + '_' + str(event['venue_address']) + '_' + str(event['title']) + '_\n' + str(event['description']) + '\n')
    yelpId = search._guessYelpId(event['venue_name'], location['lat'], location['lng'])
    if yelpId:
        eventObj = { 'yelp_id': yelpId,
                     'location': location,
                     'event_summary': event['title'],
                     'start_time': event['start_time'],
                     'url': event['url']
        }
        return eventObj

events = fetchEventsFromLocation(SF_LATLONG, NUM_RESULTS, 2)
for event in events:
    eventObj = getEventfulEventObj(event)
    if eventObj:
        pp(eventObj)
