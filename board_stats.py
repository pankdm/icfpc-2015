#!/usr/bin/env python

from all_includes import *
from utils import *


for i in xrange(0, 25):
    js = parse_file('p/{}.json'.format(i))
    w = js['width']
    h = js['height']
    seeds = len(js['sourceSeeds'])
    unique_seeds = len(set(js['sourceSeeds']))
    figures = js['sourceLength']

    print "{} || seeds = {} || figures = {} || w = {}, h = {}, total = {}".format(
        i, seeds, figures, w, h, w * h)
