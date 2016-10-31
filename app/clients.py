import io
import json

from factual import Factual
from foursquare import Foursquare

from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator

from app.yelp3 import Yelp3Client

with io.open('keys.local.json') as cred:
    creds = json.load(cred)
    _yelpCreds = creds["yelp"]
    _auth = Oauth1Authenticator(**_yelpCreds)
    yelpClient = Client(_auth)

    _factualCreds = creds["factual"]
    factualClient = Factual(_factualCreds["key"], _factualCreds["secret"])

    _foursquareCreds = creds["foursquare"]
    foursquareClient = Foursquare(_foursquareCreds["client_id"], _foursquareCreds["client_secret"])

    googleapikey = creds["googleapikey"]
    eventfulkey = creds["eventfulkey"]
    tripadvisorkey = creds["tripadvisorkey"]

    _yelp3Creds = creds["yelp3"]
    yelp3Client = Yelp3Client(_yelp3Creds["app_id"], _yelp3Creds["app_secret"])
    yelp3Client.refreshAccessToken()
