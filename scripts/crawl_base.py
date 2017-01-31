"""Crawls a location and radius, caching the places in Firebase.

This script only writes the foundation of places found in Yelp; subsequent
crawl scripts must be run after this to acquire richer data for each place
found.

To cache the results in the production database, see readme.

"""
from app.request_handler import searchLocationWithErrorRecovery as searchLocation
from app.util import log
from math import sqrt

import app.geofire as geo
import app.search as search

# --- START MODIFIABLE PARAMETERS --- #

# The parameters in this file default to the current sprint location.
# To change the search area, simply modify the search_center and search_radius.

# If this is False, then we store the results in Firebase.
dryRun = True

# The center of our grid.
# Using a center + radius lets us make a square grid, allowing us to recursively
# subdivide the area until we find a square small enough to be under the max Yelp results.
# The sum of all such squares will be the complete set of restaurants for the given location.
search_center = (41.8338725,-87.688585)  # Chicago.

# The radius of the geo-circle used for each search on Yelp, in meters.
search_radius = 29750

# --- END MODIFIABLE PARAMETERS --- #

# Currently unused, but kept here for reference.
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

def crawlPoints(search_center, search_radius):
    lat, lng = search_center

    if dryRun:
        log.info("Dry run - center: (%.8f, %.8f) radius: %d meters" % (lat, lng, search_radius))
        yelpVenues = search.getVenuesFromIndex(lat, lng, search_radius)
        for biz in yelpVenues:
            log.info(biz.id)
        log.info("%d unique results found." % len(yelpVenues))
        return

    log.info("starting: %.8f, %.8f -------------------" % search_center)
    searchLocation(lat, lng, search_radius)

crawlPoints(search_center, search_radius)
