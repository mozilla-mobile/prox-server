# This script creates a grid out of a geo bounded box
# that covers the Big Island of Hawaii.

# The grid size is in m, and is the interval between the searches
grid_size_m = None

# The search radius is in m and is the radius of the geo-circle used to 
# search yelp.
# There is a hard maximum of 40 venues per geo-circle (Yelp v2),
# so the smaller the radius, the more venues will be crawled.
search_radius = 28000

# Defined the bounded box of around the island.
north_lat, west_lng = 20.260499, -156.030462
south_lat, east_lng = 18.978270, -154.812693

# If this is False, then we actually perform the crawl.
dryRun = True

# Calculate search radius or grid size if not specified.
geo_fudge = 1.0
from math import sqrt
if search_radius is None and grid_size_m is not None:
    search_radius = geo_fudge * sqrt(2) / 2 * grid_size_m

if grid_size_m is None and search_radius is not None:
    grid_size_m = 2 * search_radius / geo_fudge / sqrt(2)

if grid_size_m is None and search_radius is None:
    raise Exception("Need to set one of grid_size_m or search_radius")

import app.geo as geo

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
          lng += geo.metersToLongitudeDegrees(grid_size_m, lat)
          yield (lat, lng)

      lat_delta = grid_size_m / geo.g_METERS_PER_DEGREE_LATITUDE
      lat += lat_delta

grid = grid_points(north_lat, west_lng, south_lat, east_lng, grid_size_m)

# Now do the crawl with the grid.
from collections import deque
history = deque()
count = 0

for center in grid:
    history.append(center)
    if len(history) == 3:
        history.popleft()
    count += 1
    lat, lng = center
    # Now actually do the search.
    if not dryRun:
        from app.queue.enqueue import searchLocation
        searchLocation(lat, lng, search_radius)

# Print some stats about the grid
prev_center, center = history

print("Number of points: %d" % (count))
print("Number of Yelp searches: %d" % (count * 2)) 
print("Distance between points is %.2f km" % geo.distance(center, prev_center))
print("Search radius is %.2f km" % (search_radius / 1000))
print("Maximum number of venues: %d" % (count * 40))