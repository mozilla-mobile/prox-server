from app.request_handler import _guessYelpId, searchLocation

LOCS = [
    (37.783875, -122.409405), # SF
    (38.903564, -77.036996), # D.C.
    (51.531724, -0.131832), # London
    (42.359984, -71.063343) # Boston
    ]

for location in LOCS:
    searchLocation(location[0], location[1], 30, 30)

