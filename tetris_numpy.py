from enum import Enum
from copy import deepcopy
from config import Config
from moves import *

import copy
import numpy


class Cell:
    EMPTY = 0
    FULL = 1
    # for output
    UNIT = 2
    EMPTY_PIVOT = 3
    PIVOT = 4


CELLS_TO_STRING = {
    Cell.EMPTY: '_',
    Cell.FULL: '#',
    Cell.UNIT: 'x',
    Cell.EMPTY_PIVOT: '.',
    Cell.PIVOT: 'Z',
}

def show_cell(cell):
    return CELLS_TO_STRING[cell]


# class Cell:
#     EMPTY = 1
#     FULL = 2
#     # for output
#     UNIT = 3
#     EMPTY_PIVOT = 4
#     PIVOT = 5


# is used to indicate invalid state
class GameEnds(Exception):
    pass

# is used to indicate that the game was ended with 0 points
class WrongMove(Exception):
    pass

class Error(Exception):
    pass

# base formula to convert from ugly coordinats
# to good ones
def convert_to_good_x(y, x):
    return x + (y + 1) / 2

def left_border(y):
    return convert_to_good_x(y, 0)

def right_border(y, width):
    return width + (y + 1) / 2
    # return convert_to_good_x(y, 0) + width

def get_base_figure(pivot_y, pivot_x, coords):
    deltas = []
    for y, x in coords:
        deltas.append( (y - pivot_y, x - pivot_x) )
    return deltas

# rotates figure on 60 degrees 
# (1, 0) --> (0, -1)
# (0, 1) --> (1, 1)
# (y, x) = y * (1, 0) + x * (0, 1) -->
# y * (0, -1) + x * (1, 1) = (x, x - y)
def rotate(deltas):
    res = []
    for y, x in deltas:
        res.append( (x, x - y) )
    return res


def modify_board(b, y, x, data):
    if 0 <= y < len(b) and 0 <= x < len(b[y]):
        b[y][x] = data


class ImmutableFigure:
    def __init__(self, state, js):

        # max angle that you can rotate before getting the same figure
        self.max_angle = None
        self.max_y = 0

        # array coordinates of all possible rotations
        # coordinates are relative to pivot
        self.rotations = []
        self.init_rotations(state, js)

    # s is a state
    def init_rotations(self, state, js):
        coords = []
        for f in js['members']:
            y = f['y']
            x = convert_to_good_x(y, f['x'])
            coords.append( (y, x) )
        pv_y = state.y
        pv_x = state.x
        base_figure = get_base_figure(pv_y, pv_x, coords)
        current_figure = base_figure
        self.rotations = []
        
        for angle in xrange(6):
            self.rotations.append(current_figure)
            self.max_y = max(self.max_y, max(map(lambda pos: pos[0], current_figure)))
            current_figure = rotate(current_figure)
            if set(current_figure) == set(base_figure):
                self.max_angle = angle + 1
                break

    def get_shape(self, angle):
        return self.rotations[angle]

    # returns minimal value of y coordinate of figure
    def get_min_y(self, state):
        min_y = None
        for dy, dx in self.get_shape(state.angle):
            y = state.y + dy
            x = state.x + dx
            min_y = min_none(min_y, y)

        return min_y


# the order of coords is always y,x
class FigureState:
    def __init__(self, y, x, angle):
        self.y = y
        self.x = x
        self.angle = angle

    def __eq__(self, other):
        return (self.x == other.x) and (self.y == other.y) and self.angle == other.angle
        # return self.to_tuple() == other.to_tuple()

    def __hash__(self):
        return (self.y, self.x, self.angle).__hash__()

    def init_from_js(self, js):
        # coordinates of pivot
        self.y = js['pivot']['y']
        self.x = convert_to_good_x(self.y, js['pivot']['x'])
        # rotation clock wise
        self.angle = 0

    def to_tuple(self):
        return (self.y, self.x, self.angle)

    def __repr__(self):
        return repr(self.to_tuple())

    # const
    def next_state(self, move, f):
        x = self.x
        y = self.y
        angle = self.angle
        if move == Move.E:
            x += 1
        elif move == Move.W:
            x -= 1
        elif move == Move.SE:
            x += 1
            y += 1
        elif move == Move.SW:
            y += 1
        elif move == Move.CLOCK:
            angle += 1
            if angle >= f.max_angle:
                angle -= f.max_angle
        elif move == Move.COUNTER_CLOCK:
            angle -= 1
            if angle < 0:
                angle += f.max_angle

        return FigureState(y, x, angle)

    def make_move(self, move, f):
        self = self.next_state(move, f)

    def clone(self):
        return FigureState(self.y, self.x, self.angle)


class BoardState:
    def __init__(self, board, score_count, width):
        self.b = board
        self.score_count = score_count
        self.width = width
        self.min_y = len(self.b) + 1
        for y in xrange(self.min_y - 1):
            for v in self.b[y]:
                if v == Cell.FULL:
                    self.min_y = y
                    return

        # checks before numpy
        # for y in xrange(len(self.b)):
        #     assert len(self.b[y]) == right_border(y, self.width)

    # const
    def is_valid(self, s, f):
        # f is FigureState
        coords = f.get_shape(s.angle)
        pivot_x = s.x
        pivot_y = s.y
        # print '@', pivot_y, pivot_x

        for dy, dx in coords:
            # print 'dy, dx', dy, dx
            y = pivot_y + dy
            x = pivot_x + dx
            if not self.is_in_bounds(y, x):
                return False
            # print y, x, self.b.shape
            if self.b[y][x] == Cell.FULL:
                return False
        return True

    # const
    def is_in_bounds(self, y, x):
        if y < 0 or y >= len(self.b):
            return False
        xmin = convert_to_good_x(y, 0)
        if x < xmin or x >= right_border(y, self.width):
            return False
        return True

    def print_debug_info(self):
        print 'Score:', self.score_count.get_score()

    # which lines will be cleared if figure s would be locked
    def compute_lines_to_clear(self, s, f):
        coords = f.get_shape(s.angle)
        pivot_y = s.y
        lines_to_clear = set()
        for dy, dx in coords:
            y = pivot_y + dy
            if self.is_full_line(y):
                lines_to_clear.add(y)
        return lines_to_clear


    def lock_figure(self, s, f):
        coords = f.get_shape(s.angle)
        pivot_x = s.x
        pivot_y = s.y

        for dy, dx in coords:
            y = pivot_y + dy
            x = pivot_x + dx
            self.b[y][x] = Cell.FULL
            self.min_y = min(self.min_y, y)

        lines_to_clear = self.compute_lines_to_clear(s, f)
        # check and remove full cells
        # TODO: make faster

        if Config.PRINT_DEBUG_TETRIS_INFO:
            print 'Will clear', lines_to_clear
        total_deleted = 0
        if lines_to_clear:
            for y in reversed(xrange(len(self.b))):
                while y - total_deleted in lines_to_clear:
                    total_deleted += 1
                if total_deleted == 0:
                    continue
                y2 = y - total_deleted

                # len1 = len(self.b[y])
                # assert len1 == right_border(y, self.width)
                len1 = right_border(y, self.width)

                # copy last "width" symbols from top to bottom
                if y2 >= 0:
                    len2 = right_border(y2, self.width)
                    self.b[y][len1 - self.width : len1] = self.b[y2][len2 - self.width : len2]
                else:
                    # self.b[y][len1 - self.width : len1] = [Cell.EMPTY] * self.width
                    self.b[y].fill(Cell.EMPTY)

        self.min_y += total_deleted
        # update score
        line_score = len(lines_to_clear)
        self.score_count.lock_figure(len(coords), line_score)

    def is_full_line(self, y):
        x_start = convert_to_good_x(y, 0)
        for symbol in self.b[y][x_start:]:
            if symbol != Cell.FULL:
                return False
        return True

def min_none(a, b):
    if a == None: return b
    return min(a, b)

def max_none(a, b):
    if a == None: return b
    return max(a, b)


class Tetris:
    def __init__(self, js, seed):
        # fields (putting here for readiblity)
        # board with filled (or not) cells
        self.board_state = None
        # current state of figure
        self.s = None
        # base figure
        self.current_figure = None
        self.width = js['width']

        # real init
        self.score_count = ScoreCount()

        self.init_board_state(js)
        self.figure_generator = FigureGenerator(js, seed)
        self.spawn_next_figure()

        self.num_moves = 0

    def get_score(self):
        return self.score_count.get_score()

    def spawn_next_figure(self):
        # (s)tate and current immutable (f)igure
        s, f = self.figure_generator.get_next_figure()
        s = s.clone()

        shape = f.get_shape(s.angle)
        ymin = None
        for y, x in shape:
            ymin = min_none(ymin, y)

        if Config.PRINT_DEBUG_TETRIS_INFO:
            print shape
            print 'ymin = ', ymin
        s.y = -ymin

        min_r = None
        min_l = None
        for y, x in shape:
            ynow = s.y + y
            assert(ynow >= 0)
            # xmax = len(self.board_state.b[ynow])
            # assert xmax == right_border(ynow, self.width)
            xmax = right_border(ynow, self.width)

            dr = xmax - 1 - x
            min_r = min_none(min_r, dr)

            dl = x - convert_to_good_x(ynow, 0)
            min_l = min_none(min_l, dl)

        delta_x = (min_l + min_r) / 2
        if Config.PRINT_DEBUG_TETRIS_INFO:
            print 'min_l = ', min_l, 'min_r = ', min_r
            print 'delta_x = ', delta_x
        s.x = delta_x - min_l
        
        if not self.board_state.is_valid(s, f):
            raise GameEnds("Couldn't spawn new: the board is full!")

        self.current_figure = f
        self.s = s
        self.previous_states = { s }


    def init_board_state(self, js):
        xmax = js['width']
        ymax = js['height']

        real_xmax = right_border(ymax - 1, self.width)
        b = numpy.zeros((ymax, real_xmax), dtype=int)
        for y in xrange(ymax):
            for x in xrange(xmax):
                b[y][x] = Cell.EMPTY
        print 'numpy, FTW!!'

        for cell in js['filled']:
            y = cell['y']
            x = convert_to_good_x(y, cell['x'])
            b[y][x] = Cell.FULL
        self.board_state = BoardState(b, self.score_count, xmax)

    def make_move(self, move):
        # early skip
        if move == Move.IGNORE:
            return
        
        self.num_moves += 1
        next_s = self.s.next_state(move, self.current_figure)
        if next_s in self.previous_states:
            raise WrongMove("Already was in state {}".format(next_s))

        if self.board_state.is_valid(next_s, self.current_figure):
            self.s = next_s
            self.previous_states.add( self.s )
        else:
            if Config.PRINT_DEBUG_TETRIS_INFO:
                print 'locking figure, spawning new one'
            self.board_state.lock_figure(self.s, self.current_figure)
            self.spawn_next_figure()

    def print_board(self):
        b = deepcopy(self.board_state.b)

        f = self.current_figure
        state = self.s
        pv_y = state.y
        pv_x = state.x
        modify_board(b, pv_y, pv_x, Cell.EMPTY_PIVOT)

        for dy, dx in f.get_shape(state.angle):
            if b[pv_y + dy][pv_x + dx] == Cell.EMPTY_PIVOT:
                b[pv_y + dy][pv_x + dx] = Cell.PIVOT
            else:
                b[pv_y + dy][pv_x + dx] = Cell.UNIT 

        for y in xrange(len(b)):
            xmin = convert_to_good_x(y, 0)
            shift = ''
            if y % 2 == 1:
                shift = ' '
            line = ''
            # print 'iterating on x from ', left_border(y), right_border(y, self.width)
            for x in xrange(left_border(y), right_border(y, self.width)):
                line += show_cell(b[y][x]) + ' '
            print shift + line

        self.board_state.print_debug_info()
        print 'num moves:', self.num_moves
        self.figure_generator.print_debug_info()

        print 'current angle ', state.angle
        print 'max angle', f.max_angle

    def clone(self):
        result = copy.copy(self)
        result.board_state = deepcopy(self.board_state)
        result.s = deepcopy(self.s)
        result.score_count = deepcopy(self.score_count)
        result.figure_generator = self.figure_generator.clone()
        return result


class RNG:
    modulus = 2**32
    mult = 1103515245
    increment = 12345
    mask = 0x7fff
    def __init__(self, seed):
        self.x = seed

    def next_number(self):
        res = self.x
        self.x = (self.mult * self.x + self.increment) % self.modulus
        # taking bits 30..16 from result
        return (res >> 16) & self.mask

    def current_number(self):
        return self.x


class FigureGenerator:
    def __init__(self, js, seed):
        self.seed = seed
        self.length = js['sourceLength']
        self.rng = RNG(seed)
        self.cnt = 0
        self.index = None

        self.figures = []
        for js_unit in js['units']:
            state = FigureState(None, None, None)
            state.init_from_js(js_unit)
            f = ImmutableFigure(state, js_unit)
            
            self.figures.append( (state, f) )

    def print_debug_info(self):
        print 'figure count = ', self.cnt
        print 'figure index = ', self.index
        print 'total number = ', self.length
        print 'num figures = ', len(self.figures)

    def get_next_figure(self):
        self.cnt += 1
        if self.cnt > self.length:
            raise GameEnds("No more figures (processed: {})".format(self.length))

        index = self.rng.next_number() % len(self.figures)
        self.index = index

        return self.figures[index]

    def clone(self):
        result = copy.copy(self)
        result.rng = deepcopy(self.rng)
        return result

class ScoreCount:
    def __init__(self):
        self.score = 0
        self.ls_old = 0

    def get_score(self):
        return self.score

    @staticmethod
    def compute_line_bonus(line_score):
        return 100 * line_score * (line_score + 1) / 2

    def lock_figure(self, size, line_score):
        points = size + ScoreCount.compute_line_bonus(line_score)
        lines_bonus = 0
        if self.ls_old > 1:
            lines_bonus += (self.ls_old - 1) * points / 10

        self.ls_old = line_score
        self.score += points + lines_bonus



