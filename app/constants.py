
# Change these names to change what the tables in firebase are called.
# _tablePrefix = "user_name"
_tablePrefix = ""
_venues = "venues"
_events = "events"
_searches = "searches"

# number of seconds after a search in a given area that it should be cached.
searchCacheExpiry = 60 * 60 * 24 # s
searchCacheRadius = 1000 # m

# Don't edit these directly.
venuesTable = _tablePrefix + _venues
eventsTable = _tablePrefix + _events
searchesTable = _tablePrefix + _searches

# Events
konaLatLng = { "lat": 19.622345, "lng": -155.665041 }

calendarInfo = {
    "calRefreshSec": 3600,
    "googleCalendarUrl": "https://www.googleapis.com/calendar/v3/calendars/{}/events?key={}",
    "calendarIds": [ "hawaii247.com_dm8m04hk9ef3cc81eooerh3uos@group.calendar.google.com", "mozilla.com_avh8q3pubnr4uj419aaubpat2g@group.calendar.google.com" ],
    "eventfulUrl": "https://api.eventful.com/json/events/search"
}
