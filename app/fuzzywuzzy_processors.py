"""A collection of processors for fuzzywuzzy.

TODO:
- This should really be in app/util/... but util.py makes that hard.

"""
from fuzzywuzzy import process
import re

_WIKI_DISAMBIGUATION_REGEX = re.compile('(.+)\s+\(.+\)')


def wiki_disambiguation_processor(s):
    """fuzzywuzzy processor: full process & removes Wiki disambiguation markup (e.g. '(restaurant)')."""
    disambiguated_s = _rm_wiki_disambiguation_markup(s)
    return process.utils.full_process(disambiguated_s)


def _rm_wiki_disambiguation_markup(s):
    """Removes Wiki disambiguation markup (e.g. '(restaurant)') from a string."""
    match = _WIKI_DISAMBIGUATION_REGEX.match(s)
    if match:
        return match.group(1)
    else:
        return s
