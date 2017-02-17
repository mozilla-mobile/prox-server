from __future__ import print_function

import sys

from fuzzywuzzy import fuzz, process
from app.fuzzywuzzy_processors import wiki_disambiguation_processor
import wikipedia

from app.util import slug

def resolve(url):
    pageID = slug(url)
    page = wikipedia.page(pageID, preload=True)
    return {
      "url": page.url,
      "summary": page.summary,
      "images": page.images,
    }

# --- SEARCH PARAMETERS --- #
# Run `pytest` when changing these parameters to ensure they still work.

_THRESHOLD = 80  # Set through trial and error.

# Selected by process of elimination:
# - partial_ratio: it scores 100 for 'Burger' to both 'Super Duper Burgers' and 'Bob's Burgers'
# - token_*: requires exact tokens so plurals are broken: 'Burger' & 'Super Duper Burgers' scores 48
#                                                         'Burgers' & 'Super Duper Burgers' scores 100.
_SCORER = fuzz.ratio

_PLACE_NAME_TO_WIKI_PAGE_PROCESSORS = [
    process.utils.full_process,
    wiki_disambiguation_processor,
]
# --- END SEARCH PARAMETERS --- #


def search(coord, place_name):
    """Finds the Wikipedia page corresponding to the given place.

    The current implementation requires Wikipedia geotags, meaning it'll miss:
    - Chains (Starbucks)
    - Corporate pages (Lagunitas, as opposed to the brewery site)
    - Area-based things (49-mile drive in SF)

    :param coord: is (latitude, longitude)
    :return: A wikipedia page title.
    """
    # We don't use the title arg of `wikipedia.geosearch`. It will return exact title matches, even if the geo location
    # does not match, so "Boulevard" will return a street rather than the restaurant (which is "Boulevard (restaurant)").
    wiki_page_titles = wikipedia.geosearch(*coord)
    return _match_place_name_to_wiki_page(place_name, wiki_page_titles)

def _match_place_name_to_wiki_page(place_name, wiki_page_titles):
    """Work horse of `geosearch`: separated for easier testing & debugging.

    For example places we can't yet match, see `test_wp._CHALLENGE_PLACE_NAME_TO_WIKI`.

    Potential improvements:
    - Change existing dials (for each pass?): local vars (e.g. _THRESHOLD), radius/limit kwarg to Wikipedia API
    - Changes scorers on different passes, e.g. partial_ratio is more lenient than ratio.
    - Modify full_process processor: it removes non-letter-number characters so wiki disambiguation markup can cause
      undesired matching. For example, "Boulevard (restaurant)" becomes "boulevard  restaurant", which matches
      "mourad restaurant" at 79.
    - Add additional processors:
      - Modify plurals, articles, accents (full_process will just remove accented characters :( ).
      - Remove city/state name occurences in wiki pages, e.g. "San Francisco Ferry Building" -> "Ferry Building"
        could better match the Yelp "Ferry Building Marketplace" (disclaimer: US-centric)
    - Modify place_name query string. These may be better than their "remove" counterparts because adding more
      characters gives more information to try to match against and may produce more accurate results than removing characters.
      - (reverse ^) add city/state to place names: "Ferry Building Marketplace" -> "San Francisco Ferry Building Marketplace"
      - Reverse wiki_disambiguation_processor: add common wikipedia endings: (restaurant), (California), etc.
    - Consider running most lenient processors first, moving towards more strict, like a filter. Right now we run the
      strictest first.
    """
    # We run multiple processor passes: if there is no match, the next processor may be more lenient.
    for processor in _PLACE_NAME_TO_WIKI_PAGE_PROCESSORS:
        matches = process.extractBests(place_name, wiki_page_titles, scorer=_SCORER, processor=processor,
                                       score_cutoff=_THRESHOLD)
        if len(matches) >= 1:
            if len(matches) > 1:
                print('More than one match above threshold', matches, file=sys.stderr)
            return matches[0][0]
    return None
