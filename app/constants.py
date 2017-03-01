import getpass
from enum import Enum

# Change these names to change what the tables in firebase are called.
def _findTablePrefix():
    username = getpass.getuser()
    #os_name, hostname = os.uname()[0:2]
    #if os_name == "Linux":
    #    if hostname == "prox-dev.moo.mx":
    #        # staging
    #        return ""
    #    if hostname.startswith("ip-") and username == "prox":
    #        # production
    #        return "production/"
    return "users/" + username + "/"  # Development
    #return "branches/" + <key> + "/"  # Production

_tablePrefix = _findTablePrefix()
_venues = "venues"
_events = "events"
_searches = "searches"
_details = "details"
_locations = "locations"
_status = "status"
_proxwalk = "proxwalk"
_cache = "cache"

# number of seconds after a search in a given area that it should be cached.
searchCacheExpiry = 60 * 60 * 20 # s
searchCacheRadius = 1000 # m

# radius we ask yelp to query around.
venueSearchRadius = 40000 # m
# the max number of venues we'll ask for for a given geo circle.
venueSearchNumber = 200 

# Don't edit these directly.
venuesTable = _tablePrefix + _venues
eventsTable = _tablePrefix + _events
searchesTable = _tablePrefix + _searches
detailsTable = _tablePrefix + _venues + '/' + _details
locationsTable = _tablePrefix + _venues + '/' + _locations
statusTable = _tablePrefix + _venues + '/' + _status
cacheTable = _tablePrefix + _venues + '/' + _cache
proxwalkTable = venuesTable + "/" + _proxwalk

apiAvailabilityTable = "api_availability"

# Events
konaLatLng = { "lat": 19.622345, "lng": -155.665041 }

calendarInfo = {
    "googleCalendarUrl": "https://www.googleapis.com/calendar/v3/calendars/{}/events?key={}",
    "calendarIds": [ "mozilla.com_avh8q3pubnr4uj419aaubpat2g@group.calendar.google.com" ],
    "eventfulUrl": "https://api.eventful.com/json/events/search"
}

# Location lat/lngs
GPS_LOCATIONS = {
    "CHICAGO_CENTER" : (41.8338725, -87.688585),
    "GARFIELD_PARK" : (41.886724, -87.717264),
    "MUSEUM_SCIENCE_INDUSTRY" : (41.790805, -87.583130),
    "CULTURAL_CENTER" : (41.883754, -87.624941),
    "METROPOLIS_COFFEE" : (41.994339, -87.657278)
}

class Status(Enum):
    NOT_FOUND = 0
    FETCH_FAILED = -1
