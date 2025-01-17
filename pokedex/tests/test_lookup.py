# Encoding: UTF-8
import os

import pytest

parametrize = pytest.mark.parametrize


@parametrize(
    ('input', 'table', 'id'),
    [
        # Simple lookups
        (u'Eevee', 'pokemon_species', 133),
        (u'Scratch', 'moves', 10),
        (u'Master Ball', 'items', 1),
        (u'normal', 'types', 1),
        (u'Run Away', 'abilities', 50),

        # Funny characters
        (u'Mr. Mime', 'pokemon_species', 122),
        (u"Farfetch’d", 'pokemon_species', 83),
        (u'Poké Ball', 'items', 4),

        # Forms
        (u'Rotom', 'pokemon_species', 479),
        (u'Wash Rotom', 'pokemon_forms', 10059),
        (u'East Shellos', 'pokemon_forms', 10039),

        # Other languages
        (u'イーブイ', 'pokemon_species', 133),
        (u'Iibui', 'pokemon_species', 133),
        (u'Eievui', 'pokemon_species', 133),
        (u'이브이', 'pokemon_species', 133),
        (u'伊布', 'pokemon_species', 133),
        (u'Evoli', 'pokemon_species', 133),
    ]
)
def test_exact_lookup(lookup, input, table, id):
    results = lookup.lookup(input)
    assert len(results) == 1
    assert results[0].exact == True

    row = results[0].object
    assert row.__tablename__ == table
    assert row.id == id


def test_id_lookup(lookup):
    results = lookup.lookup(u'1')
    assert len(results) >= 5
    assert all(result.object.id == 1 for result in results)


def test_multi_lookup(lookup):
    results = lookup.lookup(u'Metronome')
    assert len(results) == 2
    assert results[0].exact


def test_type_lookup(lookup):
    results = lookup.lookup(u'pokemon:1')
    assert results[0].object.__tablename__ == 'pokemon_species'
    assert len(results) == 1
    assert results[0].object.name == u'Bulbasaur'

    results = lookup.lookup(u'1', valid_types=['pokemon_species'])
    assert results[0].object.name == u'Bulbasaur'


def test_language_lookup(lookup):
    # There are two objects named "charge": the move Charge, and the move
    # Tackle, which is called "Charge" in French.
    results = lookup.lookup(u'charge')
    assert len(results) > 1

    results = lookup.lookup(u'@fr:charge')
    assert results[0].iso639 == u'fr'
    assert len(results) == 1
    assert results[0].object.name == u'Tackle'

    results = lookup.lookup(u'charge', valid_types=['@fr'])
    assert results[0].object.name == u'Tackle'

    results = lookup.lookup(u'@fr,move:charge')
    assert results[0].object.name == u'Tackle'

    results = lookup.lookup(u'@fr:charge', valid_types=['move'])
    assert results[0].object.name, u'Tackle'


@parametrize(
    ('misspelling', 'name'),
    [
        # Regular English names
        (u'chamander', u'Charmander'),
        (u'pokeball', u'Poké Ball'),

        # Names with squiggles in them
        (u'farfetchd', u"Farfetch’d"),
        (u'porygonz', u'Porygon-Z'),

        # Sufficiently long foreign names
        (u'カクレオ', u'Kecleon'),
        (u'Yamikrasu', u'Murkrow'),
    ]
)
def test_fuzzy_lookup(lookup, misspelling, name):
    results = lookup.lookup(misspelling)
    first_result = results[0]
    assert first_result.object.name == name


def test_nidoran(lookup):
    results = lookup.lookup(u'Nidoran')
    top_names = [result.object.name for result in results[0:2]]
    assert u'Nidoran♂' in top_names
    assert u'Nidoran♀' in top_names


@parametrize(
    ('wildcard', 'name'),
    [
        (u'pokemon:*meleon', u'Charmeleon'),
        (u'item:master*', u'Master Ball'),
        (u'ee?ee', u'Eevee'),
    ]
)
def test_wildcard_lookup(lookup, wildcard, name):
    results = lookup.lookup(wildcard)
    first_result = results[0]
    assert first_result.object.name == name


def test_bare_random(lookup):
    for i in range(5):
        results = lookup.lookup(u'random')
        assert len(results) == 1


@parametrize(
    'table_name',
    [
        u'pokemon_species',
        u'moves',
        u'items',
        u'abilities',
        u'types'
    ]
)
def test_qualified_random(lookup, table_name):
    results = lookup.lookup(u'random', valid_types=[table_name])
    assert len(results) == 1
    assert results[0].object.__tablename__ == table_name


def test_moves_lookup(lookup):
    results = lookup.lookup(u'wrap')
    assert len(results) == 1

    results = lookup.lookup(u'megakick')
    assert len(results) == 1


def test_types_lookup(lookup):
    results = lookup.lookup(u'fire')
    assert len(results) == 2

    results = lookup.lookup(u'water')
    assert len(results) == 1

    results = lookup.lookup(u'ghost')
    assert len(results) == 2

    results = lookup.lookup(u'ice')
    assert len(results) == 1

    results = lookup.lookup(u'poison')
    assert len(results) == 1


def test_crash_empty_prefix(lookup):
    """Searching for ':foo' used to crash, augh!"""
    results = lookup.lookup(u':Eevee')
    assert results[0].object.name == u'Eevee'


def test_lookup_index(lookup):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index = os.path.abspath('%s/data/whoosh-index' % root)
    if os.path.exists(index):
        # Index exists
        results = lookup.lookup(u':Eevee')
        assert results[0].object.name == u'Eevee'
    else:
        # Index does not exist
        with pytest.raises(SystemExit):
            results = lookup.lookup(u':Eevee')


def test_prefix_lookup(lookup):
    prefix = 'char'
    results = lookup.prefix_lookup(prefix=prefix)
    object_name = results[0].object.name
    assert prefix in str(object_name).lower()

    prefix = 'smart'
    results = lookup.prefix_lookup(prefix=prefix)
    object_name = results[0].object.name
    assert prefix in str(object_name).lower()


def test_bad_prefix_lookup(lookup):
    prefix = 'yyy'
    results = lookup.prefix_lookup(prefix=prefix)
    with pytest.raises(IndexError):
        object_name = results[0].object.name

def test_symbol_name_lookup(lookup):
    results = lookup.lookup(u'???')
    assert results[0].object.name == u'???'

def test_pikachu_lookup(lookup):
    results = lookup.lookup(u'Pikachu')
    assert results[0].object.name == u'Pikachu'

def test_funny_characters(lookup):
    results = lookup.lookup(u'Poké Ball')
    assert len(results) == 1

    results = lookup.lookup(u'Mt. Moon')
    assert len(results) == 1


def test_other_language(lookup):
    results = lookup.lookup(u'フシギダネ')
    assert results[0].object.name == u'Bulbasaur'

    results = lookup.lookup(u'수댕이')
    assert results[0].object.name == u'Oshawott'

    results = lookup.lookup(u'噴嚏熊')
    assert results[0].object.name == u'Cubchoo'

    results = lookup.lookup(u'Dodoala')
    assert results[0].object.name == u'Komala'
