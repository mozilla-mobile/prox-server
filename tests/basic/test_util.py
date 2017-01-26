# coding=utf-8

from app import util


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
