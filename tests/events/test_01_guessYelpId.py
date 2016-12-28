from app.events import guessBizByName
from app.clients import yelpClient

TEST_LOCATIONS = [
        ("tate modern", 51.507769, -0.099346),
        ("tower of london", 51.508503, -0.075874),
        ("borough market", 51.505565, -0.090327),
        ("new london theatre", 51.515219, -0.122756),
        ("vaudeville theatre", 51.510279, -0.122412),
        ("AT&T park", 37.778816, -122.389270),
        ("ghirardelli square", 37.806082, -122.422801),
        ("dna lounge", 37.771050, -122.412408),
        ("domo", 37.775840, -122.426330),
        ("blue water cafe", 49.276355, -123.121031)
        ]

def matchLocationsInYelp():
    for location in TEST_LOCATIONS:
        placeName = location[0]
        print("Test: " + placeName)
        opts = {
          'term': placeName, # Yelp does a bad job with term searching
          'radius_filter': 1000,
          'sort': 1,
        }


        r = yelpClient.search_by_coordinates(location[1], location[2], **opts)
        bestGuess = guessBizByName(location[0], r.businesses)
        print(bestGuess.name if bestGuess else "No match found")

matchLocationsInYelp()
