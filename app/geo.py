
import math

# The meridional circumference of the earth in meters
g_EARTH_MERI_CIRCUMFERENCE = 40007860.0

# Length of a degree latitude at the equator
g_METERS_PER_DEGREE_LATITUDE = 110574.0

# Number of bits per geohash character
g_BITS_PER_CHAR = 5

# Maximum length of a geohash in bits
g_MAXIMUM_BITS_PRECISION = 22*g_BITS_PER_CHAR

# Equatorial radius of the earth in meters
g_EARTH_EQ_RADIUS = 6378137.0

# The following value assumes a polar radius of
# var g_EARTH_POL_RADIUS = 6356752.3;
# The formulate to calculate g_E2 is
# g_E2 == (g_EARTH_EQ_RADIUS^2-g_EARTH_POL_RADIUS^2)/(g_EARTH_EQ_RADIUS^2)
# The exact value is used here to avoid rounding errors
g_E2 = 0.00669447819799

# Cutoff for rounding errors on double calculations
g_EPSILON = 1e-12

# Default geohash length
g_GEOHASH_PRECISION = 10

# Characters used in location geohashes
g_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

def encodeGeohash(location, precision=g_GEOHASH_PRECISION):
    import pygeohash as pgh
    lat, lon = location
    return pgh.encode(lat, lon, precision=precision)

def degreesToRadians(degrees):
    return degrees * math.pi / 180

def _log2(x):
    return math.log(x) / math.log(2)

# Calculates the number of degrees a given distance is at a given latitude.
#  @param {number} distance The distance to convert.
#  @param {number} latitude The latitude at which to calculate.
#  @return {number} The number of degrees the distance corresponds to.
def metersToLongitudeDegrees(distance, latitude):
    radians = degreesToRadians(latitude)
    num = math.cos(radians) * g_EARTH_EQ_RADIUS * math.pi/180
    sinRadians = math.sin(radians)
    denom = math.sqrt(1 - g_E2 * sinRadians * sinRadians)
    deltaDeg = num / denom
    if deltaDeg < g_EPSILON:
        if distance > 0:
            return 360
        else:
            return 0
    else:
        return min(360, distance/deltaDeg)

# Calculates the maximum number of bits of a geohash to get a bounding box that is larger than a
# given size at the given coordinate.
#
#  @param {Array.<number>} coordinate The coordinate as a [latitude, longitude] pair.
#  @param {number} size The size of the bounding box.
#  @return {number} The number of bits necessary for the geohash. 
def _boundingBoxBits(coordinate, size):
    latDeltaDegrees = size/g_METERS_PER_DEGREE_LATITUDE
    latitudeNorth = min(90, coordinate[0] + latDeltaDegrees)
    latitudeSouth = max(-90, coordinate[0] - latDeltaDegrees)
    bitsLat = math.floor(latitudeBitsForResolution(size))*2
    bitsLongNorth = math.floor(longitudeBitsForResolution(size, latitudeNorth))*2-1
    bitsLongSouth = math.floor(longitudeBitsForResolution(size, latitudeSouth))*2-1
    return min(bitsLat, bitsLongNorth, bitsLongSouth, g_MAXIMUM_BITS_PRECISION)


 # Wraps the longitude to [-180,180].
 #
 #  @param {number} longitude The longitude to wrap.
 #  @return {number} longitude The resulting longitude.
 
def _wrapLongitude(longitude):
  if longitude <= 180 and longitude >= -180:
      return longitude
  adjusted = longitude + 180
  if adjusted > 0:
      return (adjusted % 360) - 180
  else:
      return 180 - (-adjusted % 360)

# Calculates eight points on the bounding box and the center of a given circle. At least one
# geohash of these nine coordinates, truncated to a precision of at most radius, are guaranteed
# to be prefixes of any geohash that lies within the circle.
#
#  @param {Array.<number>} center The center given as [latitude, longitude].
#  @param {number} radius The radius of the circle.
#  @return {Array.<Array.<number>>} The eight bounding box points.
def boundingBoxCoordinates(center, radius):
    latDegrees = radius/g_METERS_PER_DEGREE_LATITUDE;
    latitudeNorth = min(90, center[0] + latDegrees);
    latitudeSouth = max(-90, center[0] - latDegrees);
    longDegsNorth = metersToLongitudeDegrees(radius, latitudeNorth);
    longDegsSouth = metersToLongitudeDegrees(radius, latitudeSouth);
    longDegs = max(longDegsNorth, longDegsSouth);
    return [
        (center[0], center[1]),
        (center[0], _wrapLongitude(center[1] - longDegs)),
        (center[0], _wrapLongitude(center[1] + longDegs)),
        (latitudeNorth, center[1]),
        (latitudeNorth, _wrapLongitude(center[1] - longDegs)),
        (latitudeNorth, _wrapLongitude(center[1] + longDegs)),
        (latitudeSouth, center[1]),
        (latitudeSouth, _wrapLongitude(center[1] - longDegs)),
        (latitudeSouth, _wrapLongitude(center[1] + longDegs)),
    ]

# Calculates a set of queries to fully contain a given circle. A query is a [start, end] pair
# where any geohash is guaranteed to be lexiographically larger then start and smaller than end.
#
#  @param {Array.<number>} center The center given as [latitude, longitude] pair.
#  @param {number} radius The radius of the circle.
#  @return {Array.<Array.<string>>} An array of geohashes containing a [start, end] pair.
def geohashQueries(center, radius):
    queryBits = max(1, _boundingBoxBits(center, radius))
    geohashPrecision = int(math.ceil(queryBits/g_BITS_PER_CHAR))
    coordinates = boundingBoxCoordinates(center, radius)
    queries = [
        _geohashQuery(encodeGeohash(coordinate, geohashPrecision), queryBits)
        for coordinate in coordinates
    ]

    # remove duplicates
    # preserve order of insertion, for the sake of ease of comparison
    keys = set()
    values = []
    from string import join
    for query in queries:
        key = join(query, ":")
        if key not in keys:
            keys.add(key)
            values.append(query)
    queries = values
    return queries


# Calculates the bits necessary to reach a given resolution, in meters, for the longitude at a
# given latitude.
# 
#  @param {number} resolution The desired resolution.
#  @param {number} latitude The latitude used in the conversion.
#  @return {number} The bits necessary to reach a given resolution, in meters.
def longitudeBitsForResolution(resolution, latitude):
  degs = metersToLongitudeDegrees(resolution, latitude)
  if abs(degs) > 0.000001: 
      return max(1, _log2(360/degs))
  else:
      return 1

# Calculates the bits necessary to reach a given resolution, in meters, for the latitude.
# 
# @param {number} resolution The bits necessary to reach a given resolution, in meters.
def latitudeBitsForResolution(resolution):
    return min(_log2(g_EARTH_MERI_CIRCUMFERENCE/2/resolution), g_MAXIMUM_BITS_PRECISION)


# var geohashQuery = function(geohash, bits) {
#   validateGeohash(geohash);
#   var precision = Math.ceil(bits/g_BITS_PER_CHAR);
#   if (geohash.length < precision) {
#     return [geohash, geohash+"~"];
#   }
#   geohash = geohash.substring(0, precision);
#   var base = geohash.substring(0, geohash.length - 1);
#   var lastValue = g_BASE32.indexOf(geohash.charAt(geohash.length - 1));
#   var significantBits = bits - (base.length*g_BITS_PER_CHAR);
#   var unusedBits = (g_BITS_PER_CHAR - significantBits);
#   /*jshint bitwise: false*/
#   // delete unused bits
#   var startValue = (lastValue >> unusedBits) << unusedBits;
#   var endValue = startValue + (1 << unusedBits);
#   /*jshint bitwise: true*/
#   if (endValue > 31) {
#     return [base+g_BASE32[startValue], base+"~"];
#   }
#   else {
#     return [base+g_BASE32[startValue], base+g_BASE32[endValue]];
#   }
# };


# Calculates the bounding box query for a geohash with x bits precision.
#
#  @param {string} geohash The geohash whose bounding box query to generate.
#  @param {number} bits The number of bits of precision.
#  @return {Array.<string>} A [start, end] pair of geohashes.
def _geohashQuery(geohash, bits):
  precision = int(math.ceil(bits/g_BITS_PER_CHAR))
  if (len(geohash) < precision):
      return (geohash, geohash+"~")

  geohash = geohash[0:precision]
  base = geohash[0:-1]
  lastValue = g_BASE32.index(geohash[-1])
  significantBits = bits - (len(base)*g_BITS_PER_CHAR)
  unusedBits = int(g_BITS_PER_CHAR - significantBits)
  
  # delete unused bits
  startValue = (lastValue >> unusedBits) << unusedBits;
  endValue = startValue + (1 << unusedBits);
  
  if (endValue > 31):
      return (base+g_BASE32[startValue], base+"~")
  else:
      return (base+g_BASE32[startValue], base+g_BASE32[endValue])