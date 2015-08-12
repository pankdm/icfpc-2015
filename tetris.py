from enum import Enum
from copy import deepcopy
from config import Config
from moves import *

import copy
import numpy

from board_state import *



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


class ComplexMove:
    def __init__(self, seq, points):
        self.seq = seq
        self.points = points
        self.min_x = 0
        self.max_x = 0
        self.max_y = 0
        self.max_angle = 100
        self.positions = [(0, 0, 0)]
        self.moves = []
        fake_state = FigureState(0, 0, 0)
        x = 0
        y = 0
        #print(seq)
        for l in seq:
            move = CHAR_MAPPING[l]
            self.moves.append(move)
            fake_state = fake_state.next_state(move, self)
            #print(fake_state, move)
            self.positions.append((fake_state.x, fake_state.y, fake_state.angle if fake_state.angle < 10 else fake_state.angle - 100))
            self.max_x = max(self.max_x, fake_state.x)
            self.min_x = max(self.min_x, fake_state.x)
            self.max_y = max(self.max_y, fake_state.y)
        #print(self.positions)

    def valid(self, figure_angle):
        was = set()
        for position in self.positions:
            pos = (position[0], position[1], position[2] % figure_angle)
            # print(position, pos, figure_angle)
            if pos in was:
                return False
            was.add(pos)
        return True


    def __eq__(self, other):
        return (self.seq == other.seq) and (self.y == other.y) and self.angle == other.angle

# rotation of figure defined by numpy array
class NPRotation:
    def __init__(self, deltas):

        min_y, min_x = deltas[0]
        max_y, max_x = deltas[0]

        for dy, dx in deltas:
            max_y = max(max_y, dy)
            min_y = min(min_y, dy)

            max_x = max(max_x, dx)
            min_x = min(min_x, dx)

        y_len = max_y - min_y + 1
        x_len = max_x - min_x + 1

        self.shape = numpy.zeros((y_len, x_len), dtype=int)
        self.shape.fill(Cell.EMPTY)
        
        for dy, dx in deltas:
            y = dy - min_y
            x = dx - min_x
            self.shape[y][x] = Cell.FULL

        self.dy = min_y
        self.dx = min_x



class ImmutableFigure:
    def __init__(self, state, js):

        # max angle that you can rotate before getting the same figure
        self.max_angle = None
        self.max_y = 0
        self.max_x = 0
        self.min_x = 0

        # array coordinates of all possible rotations
        # coordinates are relative to pivot
        self.rotations = []
        # numpy rotations
        self.np_rotations = []
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
            self.max_x = max(self.max_x, max(map(lambda pos: pos[1], current_figure)))
            self.min_x = min(self.min_x, min(map(lambda pos: pos[1], current_figure)))
            
            self.np_rotations.append(NPRotation(current_figure))

            current_figure = rotate(current_figure)
            if set(current_figure) == set(base_figure):
                self.max_angle = angle + 1
                break


    def get_shape(self, angle):
        return self.rotations[angle]

    def get_np_shape(self, angle):
        return self.np_rotations[angle]

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
        # print 'numpy, FTW!!'

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



