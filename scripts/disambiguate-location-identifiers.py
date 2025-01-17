# Encoding: UTF-8
"""Automatically disambiguate location identifiers

This is an unmaintained one-shot script, only included in the repo for reference.


Disambiguates identifiers that aren't unique, Routes and Sea Routes, and
generic names like 'villa' or 'game corner' that could appear in future
generations again.

Does this by prepending the region name, and if that isn't enough, appends
numbers.
"""
from natsort import natsorted
import sys
import re
from collections import defaultdict

from pokedex.db import connect, tables

ambiguous_re = re.compile(r'^(sea-)?route-\d+$')

ambiguous_set = set('foreign-building game-corner global-terminal lighthouse '
    'restaurant flower-shop cycle-shop cafe shopping-mall villa'.split())

def main(*argv):
    session = connect()

    location_dict = defaultdict(list)
    for location in session.query(tables.Location).order_by(tables.Location.id):
        location_dict[location.identifier].append(location)

    changes = False
    pointer = 0
    test = []
    list_locations = []

    for identifier, locations in natsorted(location_dict.items()):
        disambiguate = any((
                len(locations) > 1,
                ambiguous_re.match(identifier),
                identifier in ambiguous_set,
            ))
        location_split = identifier.split('-')
      #  first_word =
        #print(location_split,pointer)
        if disambiguate:
            changes = True
            #print u'→'.encode('utf-8'),
            by_region = defaultdict(list)
            for location in locations:
                if location.region:
                    by_region[location.region.identifier].append(location)
                else:
                    by_region[None].append(location)
            for region_identifier, region_locations in by_region.items():

                if region_identifier:
                    new_identifier = '%s-%s' % (region_identifier, identifier)
                else:

                    # No change
                    new_identifier = identifier
                    print(new_identifier)
                if len(region_locations) == 1:
                   location = region_locations[0]
                    # The region was enough
                  # print(location)
                   location.identifier = new_identifier
                else:
                    # Need to number the locations :(
                    for i, location in enumerate(region_locations, start=1):
                        numbered_identifier = '%s-%s' % (new_identifier, i)
                       # print(numbered_identifier)
                       # location.identifier = numbered_identifier
                        print(locations)
            #print(location)
        pointer += 1
        for place in location_split:
            if place ==  'route':
                test.append(place)
        list_locations.append(location_split)


    if changes:
        if argv and argv[0] == '--commit':
            session.commit()
            print('Committed')
        else:
            print('Run with --commit to commit changes')
    else:
        print('No changes needed')
    #print(test)
    #print(location_split, pointer)



if __name__ == '__main__':
    main(*sys.argv[1:])