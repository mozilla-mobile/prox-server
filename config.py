# Paths to key files
FIREBASE_KEY_PATH="firebase.local.json"

# Firebase config for prox-server
# These are public-facing and can be found in the console under Auth > Web Setup (in the top-right corner)
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyCksV_AC0oB9OnJmj0YgXNOrmnJawNbFeE",
    "authDomain": "prox-server-cf63e.firebaseapp.com",
    "databaseURL": "https://prox-server-cf63e.firebaseio.com",
    "storageBucket": "prox-server-cf63e.appspot.com",
    "messagingSenderId": "888537898788",
    "serviceAccount": FIREBASE_KEY_PATH
    # Using the service account will authenticate as admin by default
}

yelpSearchCategories = ["active",
                        "arts",
                        "food",
                        "hotelstravel",
                        "localflavor",
                        "nightlife",
                        "pets",
                        "restaurants",
                        "shopping"]
