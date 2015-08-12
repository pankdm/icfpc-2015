

from utils import *
from tetris import *
from magic_words import *
from all_includes import *
import sys

def apply_sequence(game, seq, trace=False):
    moves = string_to_moves(seq)
    # if trace:
    #     for move in moves:
    #         print move
    more_steps = 0
    for move, s in zip(moves, seq):
        if more_steps <= 0 and trace:
            print "====================="
            game.print_board()
            print s, ord(s), move
            # char = getch.getch()
            n = raw_input().strip('\n')
            if n == '': more_steps = 1
            else:
                print 'steps = ', n, more_steps
                more_steps = int(n)
        game.make_move(move)
        more_steps -= 1

    game.print_board()

def check_sequence_score(js, seed, seq, trace=False):
    assert seed in js['sourceSeeds']
    game = Tetris(js, seed)
    moves = string_to_moves(seq)

    used_magic = set()
    word = ""

    magic_score = 0
    num_moves = 0
    for move, s in zip(moves, seq):
        word += s
        for magic in MAGIC_WORDS:
            if not word.endswith(magic):
                continue
            if not magic in used_magic:
                magic_score += 300
                used_magic.add(magic)
            magic_score += 2 * len(magic)
        if trace:
            os.system('clear')
            game.print_board()
            print move, s
        try:
            num_moves += 1
            game.make_move(move)
        except GameEnds as e:
            print e

    print 'total moves = ', num_moves, 'out of ', len(moves)
    score = game.get_score() + magic_score
    print 'Canonical score = ', score
    return score


if __name__ == '__main__':
    js = parse_file(sys.argv[1])
    cmd = sys.argv[2]
    # cmd = "r'lyeh"
    game = Tetris(js, js['sourceSeeds'][0])
    apply_sequence(game, seq, true=True)

