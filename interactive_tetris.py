

from tetris import *
import sys
import getch
import os
import json

def parse_file(file_name):
    s = open(file_name, 'r')
    return json.loads(s.read())


key_mapping = {
    'a': Move.W,
    'd': Move.E,
    'z': Move.SW,
    'x': Move.SE,
    'e': Move.CLOCK,
    'q': Move.COUNTER_CLOCK
}


def play_tetris(tetris):
    try:
        while True:
            tetris.print_board()
            k = getch.getch()
            os.system('clear')  # on linux / os x
            print '=' * 50
            move = key_mapping.get(k, None)

            print 'you pressed', k
            if k == 'n':
                #spawn next figure
                tetris.spawn_next_figure()
                continue

            if move == None:
                continue
            tetris.make_move(move)
    except GameEnds as e:
        tetris.print_board()
        raise e

if __name__ == '__main__':
    js = parse_file(sys.argv[1])
    tetris = Tetris(js, js['sourceSeeds'][0])
    # os.system('clear')  # on linux / os x
    play_tetris(tetris)


