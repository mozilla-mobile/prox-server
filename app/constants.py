
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