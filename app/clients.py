import io
import json

from factual import Factual

from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator

with io.open('keys.local.json') as cred:
    creds = json.load(cred)
    yelpCreds = creds["yelp"]
    auth = Oauth1Authenticator(**yelpCreds)
    yelpClient = Client(auth)
    factualCreds = creds["factual"]
    factualClient = Factual(factualCreds["key"], factualCreds["secret"])

