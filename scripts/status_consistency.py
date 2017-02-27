from app import geo
from app.firebase import db

from app.constants import locationsTable, venuesTable, GPS_LOCATIONS

# The casing of tripadvisor is not consistent across our Firebase scripts
TA_PROVIDER = "tripadvisor"
TA_DETAILS = "tripAdvisor"

dryRun = True

"""
Script to fix error states in the status table (e.g., places that have details
but are not not after adding new sources, due to accidental 
"""
def fixStatus(center, radius_km, provider, detailsProvider, version):
    location_table = db().child(locationsTable).get().val()
    placeIDs = geo.get_place_ids_in_radius(center, radius_km, location_table)
    print("number found {}".format(len(placeIDs)))

    statusTable = db().child(venuesTable, "status").get().val()
    placeDetails = db().child(venuesTable, "details").get().val()

    count = 0
    placeList = []
    for placeID in placeIDs:
        providers = placeDetails[placeID]["providers"]
        if detailsProvider in providers and statusTable[placeID][provider] == -1:
            st = db().child(venuesTable, "status", placeID)
            if not dryRun:
                st.update({provider: version})

            count += 1
            placeList.append(placeID)

    placeList.sort()
    print("Places updated: {}".format(placeList))
    print("total {} places with details: {}".format(detailsProvider, count))

if __name__ == '__main__':
    fixStatus(GPS_LOCATIONS["CHICAGO_CENTER"], 30, TA_PROVIDER, TA_DETAILS, 3)
