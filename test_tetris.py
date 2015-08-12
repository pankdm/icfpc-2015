

import unittest
from tetris import *
from check_seq import *
from config import Config

class TestEverything(unittest.TestCase):
    def test_rng(self):
        rng = RNG(17)
        expected = [0,24107,16552,12125,9427,13152,21440,3383,6873,16117]
        for x in expected:
            self.assertEqual(x, rng.next_number())

    def test_figure_state(self):
        js = {
            'pivot': {
                'y': 0,
                'x': 0,
            },
            'members' : [
                {
                    'y': 0,
                    'x': 0
                }
            ]
        }
        figure = FigureState(js)
        self.assertEqual(figure.max_angle, 1)

    def test_rotate(self):
        a = [(1, 0)]
        expected = [
            [(1, 0)],
            [(0, -1)],
            [(-1, -1)],
            [(-1, 0)],
            [(0, 1)],
            [(1, 1)]
        ]
        for i in xrange(6):
            self.assertEqual(a, expected[i])
            a = rotate(a)
        
    def test_map6(self):
        seq = """
iiiiiiimimiiiiiimmimiiiimimimmimimimimmeemmimimiimmmmimmimiimimimmimmimeee
mmmimimmimeeemiimiimimimiiiipimiimimmmmeemimeemimimimmmmemimmimmmiiimmmiii
piimiiippiimmmeemimiipimmimmipppimmimeemeemimiieemimmmm 
"""
        # assert ' ' not in seq
        
        js = parse_file('p/6.json')
        tetris = Tetris(js, 0)

        # see screencast for exact
        try:
            apply_sequence(tetris, seq, trace=False)
        except GameEnds:
            pass
        self.assertEqual(tetris.num_moves, 203)
        self.assertEqual(tetris.get_score(), 61)

    def test_map6_big(self):
        # Config.PRINT_DEBUG_TETRIS_INFO = True
        seq = open('artifacts/problem6-seed0.txt', 'r').read()
        # assert ' ' not in seq
        
        js = parse_file('p/6.json')
        tetris = Tetris(js, 0)

        # see screencast for exact
        try:
            apply_sequence(tetris, seq, trace=False)
        except GameEnds as e:
            print e
            pass
        tetris.print_board()

        self.assertEqual(tetris.num_moves, 1180)
        self.assertEqual(tetris.get_score(), 3261)


    def test_figure_state(self):
        f1 = FigureState(1, 1, 1)
        f2 = FigureState(1, 1, 1)
        self.assertEqual(f1, f2)

        s = set()
        s.add(f1)
        s.add(f2)
        self.assertEqual(len(s), 1)

    def test_moves_to_string(self):
        moves = [
            Move.W,
            Move.E,
            Move.SW,
            Move.SE,
            Move.CLOCK,
            Move.COUNTER_CLOCK,
        ]
        s = moves_to_string(moves)
        self.assertEqual("pbaldk", s)


if __name__ == '__main__':
    unittest.main()
