import io
import json
import pprint

from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator

from app.clients import yelpClient


def getLocality(lat, lon, **kwargs):
    return yelpClient.search_by_coordinates(lat, lon, **kwargs)

locality = getLocality(19.915403, -155.887403, term='beach')

businesses = locality.businesses
yelpIDs = [b.id for b in businesses]
print(yelpIDs)

