
import sys
import json


def parse_file(file_name):
    s = open(file_name, 'r')
    return json.loads(s.read())

# {u'sourceSeeds': [0], u'sourceLength': 100, u'height': 15, u'width': 15, 
# u'units': [{u'pivot': {u'y': 0, u'x': 0}, u'members': [{u'y': 0, u'x': 0}]}], 
# u'id': 1, u'filled': [{u'y': 4, u'x': 2}, {u'y': 4, u'x': 3}, 

def print_board(b):
    i = 0
    for l in b:
        shift = ''
        if i % 2 == 1: shift = ' '
        print shift + ' '.join(l)
        i += 1


def show_state(js):
    xmax = js['width']
    ymax = js['height']
    b = [['_' for i in xrange(xmax)] for j in xrange(ymax)]
    has_something = False
    for cell in js['filled']:
        y = cell['y']
        x = cell['x']
        b[y][x] = '#'
        has_something = True
    if has_something:
        print_board(b)


js = parse_file(sys.argv[1])
show_state(js)

