# coding=utf-8

from app import util


def test_strip_url_params_with_params():
    input_to_expected = {
        'https://duckduckgo.com/?q=python+take+while': 'https://duckduckgo.com/',
        'https://www.google.com/search?q=search': 'https://www.google.com/search',
        'https://www.yelp.com/biz/oasis-grill-san-francisco?adjust_creative=4Eouq5qgGdZWxF_f4qUZdg&utm_campaign=yelp_api_v3&utm_medium=api_v3_business_lookup':
            'https://www.yelp.com/biz/oasis-grill-san-francisco',
    }
    for input, expected in input_to_expected.iteritems():
        assert util.strip_url_params(input) == expected


def test_strip_url_params_without_params():
    # In the current implementation, we'll remove everything after the first ?.
    # In a better implementation, we'd validate a url, then rm params.
    inputs = [
        '',
        'a string',
        'https://duckduckgo.com/',
    ]
    for input in inputs:
        assert util.strip_url_params(input) == input


def test_strip_accents():
    """Testing against a list of accents I found - it's not exhaustive.
    I found them by holding down letter keys on macOS, which exposes an accent menu.
    """
    expected_to_input = {
        'a': u'àáâäãåā',
        'e': u'èéêëēėę',
        'i': u'îïíīįì',
        'o': u'ôöòóōõ',
        'u': u'ûüùúū',
        'c': u'çćč',
        'n': u'ñń',
    }
    for expected, input in expected_to_input.iteritems():
        assert util.strip_accents(input) == expected * len(input)


def test_str_contains_accents_true():
    inputs = [
        u'à',
        u'get to da chōppa!'
    ]
    for input in inputs:
        assert util.str_contains_accents(input)


def test_str_contains_accents_false():
    inputs = [
        'aoeu',
        u'aoeu',
        u'!',
    ]
    for input in inputs:
        assert not util.str_contains_accents(input)
