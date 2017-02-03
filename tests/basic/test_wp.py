# coding=utf-8

from __future__ import print_function
from app.providers import wp, yelp
import atexit
import wikipedia


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
    for (place_name, wiki_page) in _CHALLENGE_PLACE_NAME_TO_WIKI.iteritems():
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
    u'Wildhorse Saloon',
    u'Crazy Town Nashville',
    u'Laovin It',
    u'The Standard At The Smith House',
    u'Cafe Le Crumbs',
    u'The Melting Pot',
    u"Rae's Gourmet Catering & Sandwich Shoppe",
    u'Rodizio Grill The Brazilian Steakhouse',
    u"Buffalo's Nashville",
    u"BB King's Blues Club",
    u'The Valentine',
    u'A&M Events',
    u'Honky Tonk Central',
    u'Tin Roof Broadway',
    u'Hee Hawlin',
    u"Puckett's Grocery & Restaurant",
    u'Pita Pit',
    u'Really Entertaining Tours',
    u'iRide Nashville',
    u'Ichiban',
    u'Sun Diner',
    u'Frothy Monkey',
    u'Merchants Restaurant',
    u'Bongo Java Cafe',
    u"Robert's Western World",
    u'Riverfront Tavern',
    u'The Stillery',
    u'Bourbon Street Blues & Boogie Bar',
    u"Ty's Soups and Sandwiches",
    u'Benchmark Bar & Grill',
    u'Experience Nashville Tours',
    u'Rob Lindsay Pictures',
    u"Skull's Rainbow Room",
    u'Nashville Running Tours',
    u"Daddy's Dogs - Downtown",
    u'Bao Down',
    u"Swingin' Doors Saloon",
    u'Another Broken Egg Cafe',
    u'DogVacay.com - Dog Boarding Community',
    u'Back Alley Diner',
    u"Manny's House of Pizza",
}
_NASHVILLE_WIKI_PAGES = {
    u'Noel Hotel',
    u'Nashville Arcade',
    u'Timeline of Nashville, Tennessee',
    u'Federal Office Building (701 Broadway, Nashville, Tennessee)',
    u'Acme Farm Supply Building',
    u'Barbershop Harmony Society',
    u"St. Mary's Catholic Church (Nashville, Tennessee)",
    u'Renaissance Nashville Hotel',
    u"Doctor's Building (Nashville, Tennessee)",
    u'Tennessee State Capitol',
    u'Nashville Municipal Auditorium',
    u'Battle of Brentwood',
    u'Sheraton Nashville Downtown',
    u'One Nashville Place',
    u'Nashville, Tennessee',
    u'Cheatham Building',
    u'Life & Casualty Tower',
    u'Bank of America Plaza (Nashville)',
    u'Berger Building',
    u'Tennessee Theatre (Nashville)',
    u'Ryman Auditorium',
    u'Viridian Tower',
    u'505 (Nashville)',
    u'Nashville Riverfront station',
    u'Bridgestone Arena',
    u'Nashville City Center',
    u'Downtown Presbyterian Church (Nashville)',
    u'Country Music Hall of Fame and Museum',
    u'Frist Center for the Visual Arts',
    u'Bennie-Dillon Building',
    u'Savage House (Nashville, Tennessee)',
    u'Fort Nashborough',
    u"Robert's Western World",
    u'James Robertson Hotel',
    u'Mooreland (Brentwood, Tennessee)',
    u'Beacon Center of Tennessee',
    u'Southern Methodist Publishing House',
    u"Rock 'n' Roll Nashville Marathon",
    u'Frost Building (Nashville, Tennessee)',
    u'SunTrust Plaza (Nashville)',
    u'First American Cave',
    u'Fifth Third Center (Nashville)',
    u'Rich-Schwartz Building',
    u'Signature Tower',
    u'AT&T Building (Nashville)',
    u'Tennessee State Library and Archives',
    u'Utopia Hotel',
    u'Hume-Fogg High School',
    u'SunTrust Building (Nashville)',
    u'Schermerhorn Symphony Center',
    u'James K. Polk State Office Building',
    u'The Pinnacle at Symphony Place',
    u'The Stahlman',
    u"Tootsie's Orchid Lounge",
    u'War Memorial Auditorium',
    u'Davidson County Courthouse (Nashville, Tennessee)',
    u'John Seigenthaler Pedestrian Bridge',
    u'Wildhorse Saloon',
    u'Tennessee Performing Arts Center',
    u'Christ Church Cathedral (Nashville, Tennessee)',
    u'Estes Kefauver Federal Building and United States Courthouse',
    u'UBS Tower (Nashville)',
}
_NASHVILLE_PLACE_NAME_TO_WIKI_PAGE = {
    u'Wildhorse Saloon': 'Wildhorse Saloon',
    u"Robert's Western World": 'Robert\'s Western World',
}

_SF_PLACE_NAMES = {
    u'KUSAKABE',
    u'Kokkari Estiatorio',
    u'Cafe Me',
    u'Hog Island Oyster Co',
    u'Roli Roti Gourmet Rotisserie',
    u'Primavera',
    u'Il Canto Cafe',
    u'Elixiria',
    u'Frog Hollow Farm Market & Cafe',
    u'Cafe Algiers',
    u'Jackson Place Cafe',
    u'eatsa',
    u'Blue Bottle Coffee Stand',
    u'Oasis Grill',
    u'Mariposa Baking',
    u'4505 Meats',
    u'Se\xf1or Sisig',
    u'Boccalone',
    u'Prather Ranch Meat Company',
    u'Boulevard',
    u"Yo Yo's",
    u"Lou's Cafe",
    u'Paramo Coffee Company',
    u'Barbarossa Lounge',
    u'Chez Fayala',
    u'BIX',
    u'Takoba',
    u'Fayala',
    u'Golden Gate Meat Company',
    u'Mourad Restaurant',
    u'North India Restaurant',
    u'Perbacco',
    u'Coqueta',
    u'The Sentinel',
    u"Amawele's South African Kitchen",
    u'Pabu',
    u'Barbacco',
    u'Chapter 2 Coffee',
    u'Miss Tomato Sandwich Shop',
    u'Tadich Grill',
    u'Front Door Cafe',
    u'Michael Mina',
    u'La Mar Cebicher\xeda Peruana',
    u'Wayfare Tavern',
    u'The Dosa Brothers',
    u"Cap'n Mike's Holy Smoke",
    u'5A5 Steak Lounge',
    u'DragonEats',
    u"Leo's Oyster Bar",
    u'Chaya Brasserie',
    u'San Francisco Railway Museum and Gift Shop',
    u'Hawk Hill',
}
_SF_WIKI_PAGES = {
    u'Port of San Francisco',
    u'San Francisco Railway Museum',
    u'100 Pine Center',
    u'Columbia Savings Bank Building',
    u'Columbus Tower (San Francisco)',
    u'Bank of California Building (San Francisco)',
    u'Foundry Square',
    u'345 California Center',
    u'Four Embarcadero Center',
    u'Matson Building',
    u'Pacific Gas and Electric Company General Office Building and Annex',
    u'Yerba Buena Cove',
    u'Broadway and The Embarcadero Station',
    u'KPMG Building',
    u'Mission Street',
    u'One Maritime Plaza',
    u'Yerba Buena, California',
    u'United States Customhouse (San Francisco)',
    u'150 California Street',
    u'Academy of Art University',
    u'222 Second Street',
    u'Millennium Tower (San Francisco)',
    u'101 California Street',
    u'San Francisco Transbay Terminal',
    u'Ferryboat Santa Rosa',
    u'Sue Bierman Park',
    u'Saybrook University',
    u'W San Francisco',
    u'Tadich Grill',
    u'Post Montgomery Center',
    u'Old Federal Reserve Bank Building (San Francisco)',
    u'456 Montgomery Plaza',
    u'Transbay Transit Center',
    u'Black Cat Bar',
    u'One Front Street',
    u'140 New Montgomery',
    u'San Francisco Bay Area Planning and Urban Research Association',
    u'Palace Hotel, San Francisco',
    u'Niantic (whaling vessel)',
    u'WonderCon',
    u'Vaillancourt Fountain',
    u'The Purple Onion',
    u'Shell Building (San Francisco)',
    u'Boulevard (restaurant)',
    u'555 Mission Street',
    u'Cartoon Art Museum',
    u'45 Fremont Street',
    u"Jack's Restaurant",
    u'Hobart Building',
    u'ThinkEquity',
    u'Hubba Hideout',
    u'Exploratorium',
    u'Montgomery Block',
    u'Transamerica Pyramid',
    u'Merchants Exchange Building (San Francisco)',
    u'One Embarcadero Center',
    u'JPMorgan Chase Building (San Francisco)',
    u'Punch Line San Francisco',
    u'International Hotel (San Francisco)',
    u'Salesforce Tower',
    u'Aurora (Asawa)',
    u'Palace Hotel Residential Tower',
    u'33 Tehama Street',
    u'388 Market Street',
    u'44 Montgomery',
    u'Hunter-Dulin Building',
    u'535 Mission Street',
    u'Blue Shield of California Building',
    u'Jasper (San Francisco)',
    u'Southern Pacific Building',
    u'McKesson Plaza',
    u'Mills Building and Tower',
    u'595 Market Street',
    u'Embarcadero West',
    u'350 Mission Street',
    u'Maritime Hall',
    u'App Academy',
    u'Embarcadero station',
    u'Washington and The Embarcadero Station',
    u'Montgomery Street station',
    u'Clarks Point (San Francisco)',
    u'Hyatt Regency San Francisco',
    u'199 Fremont Street',
    u'International Settlement (San Francisco)',
    u'Embarcadero Center',
    u'Three Embarcadero Center',
    u'One Bush Plaza',
    u'Providian Financial Building',
    u'Financial District, San Francisco',
    u'101 Second Street',
    u'Youth Chance High School',
    u'Consulate General of Mexico, San Francisco',
    u'San Francisco Transbay development',
    u'Admission Day Monument',
    u'Stevenson Place',
    u'Park Tower at Transbay',
    u'425 California Street',
    u'WildAid',
    u'340 Fremont Street',
    u'The Montgomery (San Francisco)',
    u'Two Embarcadero Center',
    u'One Rincon Hill',
    u'Consulate General of Israel to the Pacific Northwest Region',
    u'San Francisco Ferry Building',
    u'Pacific Gas & Electric Building',
    u'505 Montgomery Street',
    u'Preparedness Day Bombing',
    u'Market and The Embarcadero Station',
    u'Central Plaza (San Francisco)',
    u'50 California Street',
    u'50 Fremont Center',
    u"San Francisco Mechanics' Institute",
    u'One California',
    u'Royal Insurance Building, San Francisco',
    u'Apollo (storeship)',
    u'Montgomery Street',
    u'Hotaling Building',
    u'Hilton San Francisco Financial District',
    u'333 Market Street',
    u'Room 641A',
    u'Folger Coffee Company Building',
    u'New Montgomery Street',
    u'California Historical Society',
    u'Rincon Center',
    u'Don Chee Way and Steuart Station',
    u'Linden Lab',
    u'Museum of the African Diaspora',
    u'Loews Regency San Francisco',
    u'123 Mission Street',
    u'Bank of Italy Building (San Francisco)',
    u'BlueStar PR',
    u'St. Regis Museum Tower',
    u'Le M\xe9ridien San Francisco',
    u'399 Fremont Street',
    u'425 Market Street',
    u'181 Fremont',
    u'Pacific Research Institute',
    u'Pacific Exchange',
    u'Central Embarcadero Piers Historic District',
    u'One Market Plaza',
    u'San Francisco Railway Museum',
    u'Hawk Hill (California)',
}
_SF_PLACE_NAME_TO_WIKI_PAGE = {
    u'Tadich Grill': 'Tadich Grill',

    # Wikipedia disambiguation markup, e.g. "(restaurant)".
    u'Boulevard': 'Boulevard (restaurant)',
    u'Hawk Hill': 'Hawk Hill (California)',

    # Place is superset.
    u'San Francisco Railway Museum and Gift Shop': 'San Francisco Railway Museum',
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
