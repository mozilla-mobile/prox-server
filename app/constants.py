
# Change these names to change what the tables in firebase are called.
def _findTablePrefix():
    import os, getpass
    os_name, hostname = os.uname()[0:2]
    username = getpass.getuser()
    if os_name == "Linux":
        if hostname == "prox-dev.moo.mx":
            # staging
            return ""
        if hostname.startswith("ip-") and username == "prox":
            # production
            return "production/" 
    # development
    return username + "/"

_tablePrefix = _findTablePrefix()
_venues = "venues"
_events = "events"
_searches = "searches"
_locations = "locations"
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
locationsTable = _tablePrefix + _venues + '/' + _locations
cacheTable = _tablePrefix + _venues + '/' + _cache
proxwalkTable = venuesTable + "/" + _proxwalk

statusTable = "api_availability"

# Events
konaLatLng = { "lat": 19.622345, "lng": -155.665041 }

calendarInfo = {
    "googleCalendarUrl": "https://www.googleapis.com/calendar/v3/calendars/{}/events?key={}",
    "calendarIds": [ "mozilla.com_avh8q3pubnr4uj419aaubpat2g@group.calendar.google.com" ],
    "eventfulUrl": "https://api.eventful.com/json/events/search"
}
