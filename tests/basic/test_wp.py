# coding=utf-8


from app.providers import wp, yelp
import atexit
import wikipedia
from functools import reduce


def test_match_place_name_to_wiki_page():
    """Test the place->wiki page matching algorithm underlying wp.geosearch returns only correct wiki pages for places.

    This test uses real data: Yelp places, the wiki pages returned by searching from Yelp place coordinates, and
    a mapping from Yelp places to their wikipedia pages.

    At the time of writing, this test is harder than in practice: the algorithm will compare the place against the
    ~10 closest Wikipedia pages whereas the test compares the place against *all* results (~50) within a region.
    If we were to make this test more lenient, we could match more places in practice but are more likely to get
    incorrect matches. Since we only compare against the 10 closest geotagged wiki pages, we may not get mismatches
    in practice.

    To add data to this test:
    1) Retrieve a list of place IDs - perhaps search within a radius in the Firebase.
    1.5) Make sure the list isn't too big (max at maybe 50?).
    2) Get their Yelp place names.
    3) Use `yelp_ids_to_wiki_pages` to get the wiki pages that would result from searching for these places.
    4) Find the places in Yelp that match wiki pages.
    5) (recommended to use pprint and copy-pasta) store the place names (2) in a set, the wiki pages (3) in a set,
       and the mapping between them in a dictionary (4). See _NASHVILLE_*.
    6) Add this mapping to _PLACE_NAMES_AND_WIKI_PAGES.

    TODO:
    - It might be cleaner to load the input data from a file.
    - Make it easier to get test data (e.g. place names)
    - Test can be faster: we iterate n places over n+ wiki pages = n^2. In practice, it's 10n, n pages over 10 wiki pages.
    - Add deliberate unicode tests!
    """
    for (place_names, wiki_pages, place_name_to_wiki_page) in _PLACE_NAMES_AND_WIKI_PAGES:
        _verify_match_place_input(place_names, wiki_pages, place_name_to_wiki_page)

        for place_name in place_names:
            actual = wp._match_place_name_to_wiki_page(place_name, wiki_pages)
            expected = place_name_to_wiki_page.get(place_name, None)
            assert actual == expected, "Expected wiki page %s but got %s from place %s" % (expected, actual, place_name)


def _verify_match_place_input(place_names, wiki_pages, place_name_to_wiki_page):
    """Verify the inputs follow the required convention. See dataset documentation below for more."""
    for place_name in place_name_to_wiki_page.keys():
        if place_name not in place_names:
            raise ValueError("Place name %s not in place name iterable." % place_name)

    for wiki_page in place_name_to_wiki_page.values():
        if wiki_page not in wiki_pages:
            raise ValueError("Wiki page %s not in wiki page iterable." % wiki_page)


def test_match_place_name_to_wiki_page_challenges():
    """There are some place -> wiki we can't match. Here we check these challenges for a match and
    alert the dev if there's a match.

    Use case: we're modifying the algorithm and we want to know if we improve the algorithm such that one of these
    challenges starts to work.

    If one of these is successful, consider adding them to the permanent assertions in
    `test_match_place_name_to_wiki_page`.
    """
    def alert(place_name, wiki_page):
        print('COMPLETED CHALLENGE place -> wiki: %s -> %s. Consider adding to permanent assertions.' % (place_name, wiki_page))
    for (place_name, wiki_page) in _CHALLENGE_PLACE_NAME_TO_WIKI.items():
        output = wp._match_place_name_to_wiki_page(place_name, [wiki_page])
        if output:
            # pytest eats our logs so we have to run after it's done. via: http://stackoverflow.com/a/38806934/2219998
            atexit.register(alert, place_name, wiki_page)


# I've found the best way to find more non-matching examples is to use get geotagged Wikipedia pages (either
# through Android app "Nearby" or API geosearch) and search for pages that you'd expect to be on Yelp.
_CHALLENGE_PLACE_NAME_TO_WIKI = {
    # San Francisco places.
    'Ferry Building Marketplace': 'San Francisco Ferry Building',
    'InterContinental Mark Hopkins': 'Mark Hopkins Hotel',
    'Tonga Room & Hurricane Bar': 'Tonga Room',
    'The Scarlet Huntington': 'Huntington Hotel (San Francisco)',
    'bound together anarchist collective bookstore': 'Bound Together Bookstore Collective',
    'Alamo Square': 'Alamo Square, San Francisco',
    'Lower Haight': 'Lower Haight, San Francisco',
    'USF - Fromm Institute': 'Fromm Institute for Lifelong Learning',
}


# See `test_match_place_name_to_wiki_page` for details.
# Entries in Yelp -> Wiki that are particularly challenging may be commented.
_NASHVILLE_PLACE_NAMES = {
    'Wildhorse Saloon',
    'Crazy Town Nashville',
    'Laovin It',
    'The Standard At The Smith House',
    'Cafe Le Crumbs',
    'The Melting Pot',
    "Rae's Gourmet Catering & Sandwich Shoppe",
    'Rodizio Grill The Brazilian Steakhouse',
    "Buffalo's Nashville",
    "BB King's Blues Club",
    'The Valentine',
    'A&M Events',
    'Honky Tonk Central',
    'Tin Roof Broadway',
    'Hee Hawlin',
    "Puckett's Grocery & Restaurant",
    'Pita Pit',
    'Really Entertaining Tours',
    'iRide Nashville',
    'Ichiban',
    'Sun Diner',
    'Frothy Monkey',
    'Merchants Restaurant',
    'Bongo Java Cafe',
    "Robert's Western World",
    'Riverfront Tavern',
    'The Stillery',
    'Bourbon Street Blues & Boogie Bar',
    "Ty's Soups and Sandwiches",
    'Benchmark Bar & Grill',
    'Experience Nashville Tours',
    'Rob Lindsay Pictures',
    "Skull's Rainbow Room",
    'Nashville Running Tours',
    "Daddy's Dogs - Downtown",
    'Bao Down',
    "Swingin' Doors Saloon",
    'Another Broken Egg Cafe',
    'DogVacay.com - Dog Boarding Community',
    'Back Alley Diner',
    "Manny's House of Pizza",
}
_NASHVILLE_WIKI_PAGES = {
    'Noel Hotel',
    'Nashville Arcade',
    'Timeline of Nashville, Tennessee',
    'Federal Office Building (701 Broadway, Nashville, Tennessee)',
    'Acme Farm Supply Building',
    'Barbershop Harmony Society',
    "St. Mary's Catholic Church (Nashville, Tennessee)",
    'Renaissance Nashville Hotel',
    "Doctor's Building (Nashville, Tennessee)",
    'Tennessee State Capitol',
    'Nashville Municipal Auditorium',
    'Battle of Brentwood',
    'Sheraton Nashville Downtown',
    'One Nashville Place',
    'Nashville, Tennessee',
    'Cheatham Building',
    'Life & Casualty Tower',
    'Bank of America Plaza (Nashville)',
    'Berger Building',
    'Tennessee Theatre (Nashville)',
    'Ryman Auditorium',
    'Viridian Tower',
    '505 (Nashville)',
    'Nashville Riverfront station',
    'Bridgestone Arena',
    'Nashville City Center',
    'Downtown Presbyterian Church (Nashville)',
    'Country Music Hall of Fame and Museum',
    'Frist Center for the Visual Arts',
    'Bennie-Dillon Building',
    'Savage House (Nashville, Tennessee)',
    'Fort Nashborough',
    "Robert's Western World",
    'James Robertson Hotel',
    'Mooreland (Brentwood, Tennessee)',
    'Beacon Center of Tennessee',
    'Southern Methodist Publishing House',
    "Rock 'n' Roll Nashville Marathon",
    'Frost Building (Nashville, Tennessee)',
    'SunTrust Plaza (Nashville)',
    'First American Cave',
    'Fifth Third Center (Nashville)',
    'Rich-Schwartz Building',
    'Signature Tower',
    'AT&T Building (Nashville)',
    'Tennessee State Library and Archives',
    'Utopia Hotel',
    'Hume-Fogg High School',
    'SunTrust Building (Nashville)',
    'Schermerhorn Symphony Center',
    'James K. Polk State Office Building',
    'The Pinnacle at Symphony Place',
    'The Stahlman',
    "Tootsie's Orchid Lounge",
    'War Memorial Auditorium',
    'Davidson County Courthouse (Nashville, Tennessee)',
    'John Seigenthaler Pedestrian Bridge',
    'Wildhorse Saloon',
    'Tennessee Performing Arts Center',
    'Christ Church Cathedral (Nashville, Tennessee)',
    'Estes Kefauver Federal Building and United States Courthouse',
    'UBS Tower (Nashville)',
}
_NASHVILLE_PLACE_NAME_TO_WIKI_PAGE = {
    'Wildhorse Saloon': 'Wildhorse Saloon',
    "Robert's Western World": 'Robert\'s Western World',
}

_SF_PLACE_NAMES = {
    'KUSAKABE',
    'Kokkari Estiatorio',
    'Cafe Me',
    'Hog Island Oyster Co',
    'Roli Roti Gourmet Rotisserie',
    'Primavera',
    'Il Canto Cafe',
    'Elixiria',
    'Frog Hollow Farm Market & Cafe',
    'Cafe Algiers',
    'Jackson Place Cafe',
    'eatsa',
    'Blue Bottle Coffee Stand',
    'Oasis Grill',
    'Mariposa Baking',
    '4505 Meats',
    'Se\xf1or Sisig',
    'Boccalone',
    'Prather Ranch Meat Company',
    'Boulevard',
    "Yo Yo's",
    "Lou's Cafe",
    'Paramo Coffee Company',
    'Barbarossa Lounge',
    'Chez Fayala',
    'BIX',
    'Takoba',
    'Fayala',
    'Golden Gate Meat Company',
    'Mourad Restaurant',
    'North India Restaurant',
    'Perbacco',
    'Coqueta',
    'The Sentinel',
    "Amawele's South African Kitchen",
    'Pabu',
    'Barbacco',
    'Chapter 2 Coffee',
    'Miss Tomato Sandwich Shop',
    'Tadich Grill',
    'Front Door Cafe',
    'Michael Mina',
    'La Mar Cebicher\xeda Peruana',
    'Wayfare Tavern',
    'The Dosa Brothers',
    "Cap'n Mike's Holy Smoke",
    '5A5 Steak Lounge',
    'DragonEats',
    "Leo's Oyster Bar",
    'Chaya Brasserie',
    'San Francisco Railway Museum and Gift Shop',
    'Hawk Hill',
}
_SF_WIKI_PAGES = {
    'Port of San Francisco',
    'San Francisco Railway Museum',
    '100 Pine Center',
    'Columbia Savings Bank Building',
    'Columbus Tower (San Francisco)',
    'Bank of California Building (San Francisco)',
    'Foundry Square',
    '345 California Center',
    'Four Embarcadero Center',
    'Matson Building',
    'Pacific Gas and Electric Company General Office Building and Annex',
    'Yerba Buena Cove',
    'Broadway and The Embarcadero Station',
    'KPMG Building',
    'Mission Street',
    'One Maritime Plaza',
    'Yerba Buena, California',
    'United States Customhouse (San Francisco)',
    '150 California Street',
    'Academy of Art University',
    '222 Second Street',
    'Millennium Tower (San Francisco)',
    '101 California Street',
    'San Francisco Transbay Terminal',
    'Ferryboat Santa Rosa',
    'Sue Bierman Park',
    'Saybrook University',
    'W San Francisco',
    'Tadich Grill',
    'Post Montgomery Center',
    'Old Federal Reserve Bank Building (San Francisco)',
    '456 Montgomery Plaza',
    'Transbay Transit Center',
    'Black Cat Bar',
    'One Front Street',
    '140 New Montgomery',
    'San Francisco Bay Area Planning and Urban Research Association',
    'Palace Hotel, San Francisco',
    'Niantic (whaling vessel)',
    'WonderCon',
    'Vaillancourt Fountain',
    'The Purple Onion',
    'Shell Building (San Francisco)',
    'Boulevard (restaurant)',
    '555 Mission Street',
    'Cartoon Art Museum',
    '45 Fremont Street',
    "Jack's Restaurant",
    'Hobart Building',
    'ThinkEquity',
    'Hubba Hideout',
    'Exploratorium',
    'Montgomery Block',
    'Transamerica Pyramid',
    'Merchants Exchange Building (San Francisco)',
    'One Embarcadero Center',
    'JPMorgan Chase Building (San Francisco)',
    'Punch Line San Francisco',
    'International Hotel (San Francisco)',
    'Salesforce Tower',
    'Aurora (Asawa)',
    'Palace Hotel Residential Tower',
    '33 Tehama Street',
    '388 Market Street',
    '44 Montgomery',
    'Hunter-Dulin Building',
    '535 Mission Street',
    'Blue Shield of California Building',
    'Jasper (San Francisco)',
    'Southern Pacific Building',
    'McKesson Plaza',
    'Mills Building and Tower',
    '595 Market Street',
    'Embarcadero West',
    '350 Mission Street',
    'Maritime Hall',
    'App Academy',
    'Embarcadero station',
    'Washington and The Embarcadero Station',
    'Montgomery Street station',
    'Clarks Point (San Francisco)',
    'Hyatt Regency San Francisco',
    '199 Fremont Street',
    'International Settlement (San Francisco)',
    'Embarcadero Center',
    'Three Embarcadero Center',
    'One Bush Plaza',
    'Providian Financial Building',
    'Financial District, San Francisco',
    '101 Second Street',
    'Youth Chance High School',
    'Consulate General of Mexico, San Francisco',
    'San Francisco Transbay development',
    'Admission Day Monument',
    'Stevenson Place',
    'Park Tower at Transbay',
    '425 California Street',
    'WildAid',
    '340 Fremont Street',
    'The Montgomery (San Francisco)',
    'Two Embarcadero Center',
    'One Rincon Hill',
    'Consulate General of Israel to the Pacific Northwest Region',
    'San Francisco Ferry Building',
    'Pacific Gas & Electric Building',
    '505 Montgomery Street',
    'Preparedness Day Bombing',
    'Market and The Embarcadero Station',
    'Central Plaza (San Francisco)',
    '50 California Street',
    '50 Fremont Center',
    "San Francisco Mechanics' Institute",
    'One California',
    'Royal Insurance Building, San Francisco',
    'Apollo (storeship)',
    'Montgomery Street',
    'Hotaling Building',
    'Hilton San Francisco Financial District',
    '333 Market Street',
    'Room 641A',
    'Folger Coffee Company Building',
    'New Montgomery Street',
    'California Historical Society',
    'Rincon Center',
    'Don Chee Way and Steuart Station',
    'Linden Lab',
    'Museum of the African Diaspora',
    'Loews Regency San Francisco',
    '123 Mission Street',
    'Bank of Italy Building (San Francisco)',
    'BlueStar PR',
    'St. Regis Museum Tower',
    'Le M\xe9ridien San Francisco',
    '399 Fremont Street',
    '425 Market Street',
    '181 Fremont',
    'Pacific Research Institute',
    'Pacific Exchange',
    'Central Embarcadero Piers Historic District',
    'One Market Plaza',
    'San Francisco Railway Museum',
    'Hawk Hill (California)',
}
_SF_PLACE_NAME_TO_WIKI_PAGE = {
    'Tadich Grill': 'Tadich Grill',

    # Wikipedia disambiguation markup, e.g. "(restaurant)".
    'Boulevard': 'Boulevard (restaurant)',
    'Hawk Hill': 'Hawk Hill (California)',

    # Place is superset.
    'San Francisco Railway Museum and Gift Shop': 'San Francisco Railway Museum',
}

_PLACE_NAMES_AND_WIKI_PAGES = [
    (_NASHVILLE_PLACE_NAMES, _NASHVILLE_WIKI_PAGES, _NASHVILLE_PLACE_NAME_TO_WIKI_PAGE),
    (_SF_PLACE_NAMES, _SF_WIKI_PAGES, _SF_PLACE_NAME_TO_WIKI_PAGE),
]


# --- TEST DATA COLLECTION FUNCTIONS --- #
def yelp_ids_to_wiki_pages(yelp_ids):
    """:return: The unioned set of wiki pages that come from searching for the yelp places with the wikipedia API."""
    return reduce(lambda wiki_pages, yelp_id: wiki_pages.union(_yelp_id_to_wiki_pages(yelp_id)),
                  yelp_ids,
                  set())


def _yelp_id_to_wiki_pages(yelp_id):
    yplace = yelp.resolve_with_key(yelp_id)
    coord = (yplace['coordinates']['latitude'], yplace['coordinates']['longitude'])
    return set(wikipedia.geosearch(*coord))
