"""Creates a grid of locations from a geo-bounded
box and caches the locations in Firebase.

To cache the results in the production database, see readme.

"""
from app.util import log
from math import sqrt

import app.geo as geo

# --- START MODIFIABLE PARAMETERS --- #

# The parameters in this file default to the Big Island of Hawaii.
# For an example of changes you may want to make, see this commit from the
# crawl-nashville branch:
# https://github.com/mozilla-mobile/prox-server/commit/127fb28724f002d23266215c5eef1bd2d7ee5878

# If this is False, then we actually perform the crawl.
dryRun = True

# The bounding box.
north_lat, west_lng = 20.260499, -156.030462
south_lat, east_lng = 18.978270, -154.812693

# START: only ONE of the following values should be `not None`.
# The interval between searches, in meters.
grid_size_m = None

# The radius of the geo-circle used for each search on Yelp, in meters.
# There is a hard maximum of venues returned per search, so the smaller the
# radius, the more venues can be crawled.
search_radius = 20000
# END: only ONE of the following values should be `not None`.

# The location you want t the most places from. An extra search will be added
# at this location and all searches closest to focus will be completed first
# so if we hit our API limits, the places closest to focus will be found.
focus = (19.915403, -155.8961577)

# (mcomella) I'm not sure what changing this would do.
geo_fudge = 1.0

# (mcomella) For logging *only*: used to calculate the maximum number of places
# we can get with this search. In Yelp v2, the value used to be 40 (which is
# what we used for Hawaii but jhugman thinks the value is 1000 now).
maxVenuesPerSearch = 1000

# --- END MODIFIABLE PARAMETERS --- #


# Calculate search radius or grid size if not specified.
if search_radius is None and grid_size_m is not None:
    search_radius = geo_fudge * sqrt(2) / 2 * grid_size_m

if grid_size_m is None and search_radius is not None:
    grid_size_m = 2 * search_radius / geo_fudge / sqrt(2)

if grid_size_m is None and search_radius is None:
    raise Exception("Need to set one of grid_size_m or search_radius")

# Calculate the grid.
# Note for smaller grid square sizes, there may be more squares nearer the equator 
# than away from it.
# Also: this does not attempt to wrap around, or top out at the top or bottom of the globe.
# i.e. this does not generalize to any bounded box on the planet.
def grid_points(north_lat, west_lng, south_lat, east_lng, grid_size_m = 100.0):
  lat, lng = (south_lat, west_lng)
  while lat < north_lat:
      lng = west_lng
      while lng < east_lng:
          yield (lat, lng)
          lng += geo.metersToLongitudeDegrees(grid_size_m, lat)

      lat_delta = grid_size_m / geo.g_METERS_PER_DEGREE_LATITUDE
      lat += lat_delta

grid = grid_points(north_lat, west_lng, south_lat, east_lng, grid_size_m)
grid = [focus] + sorted(grid, key=lambda pt: geo.distance(pt, focus))

office_locations = [
  (50.815078, -0.137089), # brighton
  (51.385114, -0.008778), # croydon
  # (-15.5095764,167.1841149), # vanuatu, lol not really.
  (43.6472912, -79.3966112), # toronto
  (37.7895639, -122.3911524), # san francisco
  (49.2824693,-123.1113848), # vancouver
  (52.5417121,13.3869854), # berlin
  (48.8721423,2.3389602), # paris
  (51.5045923,-0.0992805), # london
  (45.5234539,-122.6848713), # portland
  (37.387319,-122.0622035), # mountain view
  (35.6652311,139.725706), # tokyo
]

# Now do the crawl with the grid.
def crawlPoints(grid, search_radius, max_venue_per_search):
    for center in grid:
        lat, lng = center
        # Now actually do the search.
        if not dryRun:
            #from app.queue.enqueue import searchLocation
            from app.request_handler import searchLocationWithErrorRecovery as searchLocation
            log.info("starting: %.8f, %.8f -------------------" % center)
            searchLocation(lat, lng, search_radius, max_venue_per_search)
        else:
            print("%.8f, %.8f" % center)
    count = len(grid)
    log.info("Number of points: %d" % (count))
    log.info("Number of Yelp searches: %d" % (count * maxVenuesPerSearch / 20)) 
    log.info("Distance between points is %.2f km" % (grid_size_m / 1000))
    log.info("Search radius is %.2f km" % (search_radius / 1000))
    log.info("Maximum number of venues: %d" % (count * maxVenuesPerSearch))

crawlPoints(grid, search_radius, maxVenuesPerSearch)
crawlPoints(office_locations, 20000, 800)

