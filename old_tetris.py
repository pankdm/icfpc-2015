from enum import Enum


class Move(Enum):
    E = 1
    W = 2
    SE = 3
    SW = 4
    CLOCK = 5
    COUNTER_CLOCK = 6
    IGNORE = 7


class Cell:
    EMPTY = '_'
    FULL = '#'

command_mappings = [
    ("p'!.03", Move.W),
    ("bcefy2", Move.E),
    ("aghij4", Move.SW),
    ("lmno 5", Move.SE),
    ("dqevz1", Move.CLOCK),
    ("kstuwx", Move.COUNTER_CLOCK),
    ("\t\r\n", Move.IGNORE),
]

def get_base_figure(pivot_y, pivot_x, coords):
    deltas = []
    for y, x in coords:
        deltas.append( (y - pivot_y, x - pivot_x) )
    return deltas

# rotates figureon 60 degrees 
def rotate(deltas):
    res = []

# the order of coords is always y,x
class FigureState:
    def __init__(self, js):
        # coordinates of pivot
        self.y = js['pivot']['y']
        self.x = js['pivot']['x']
        # rotation clock wise
        self.angle = 0
        # array coordinates of all possible rotations
        # coordinates are relative to pivot
        self.rotations = None
        # max angle that you can rotate before getting the same figure
        self.max_angle = None

    def clone(self):
        res = FigureState()
        res.y = self.y
        res.x = self.x
        res.angle = self.angle
        res.rotations = self.rotations
        res.max_angle = self.max_angle
        return res


    def get_figure(self):
        return self.rotations[self.angle]

    def make_move(self, move):
        if move == Move.E:
            self.x += 1
        elif move == Move.W:
            self.x -= 1
        elif move == Move.SE:
            if self.y % 2 == 1:
                self.x += 1
            self.y += 1
        elif move == Move.SW:
            if self.y % 2 == 0:
                self.x -= 1
            self.y += 1
        elif move == Move.CLOCK:
            self.angle += 1
            if self.angle >= self.max_angle:
                self.angle -= self.max_angle
        elif move == Move.COUNTER_CLOCK:
            self.angle -= 1
            if self.angle < 0:
                self.angle += self.max_angle

class BoardState:
    def __init__(self, board):
        self.b = board

    def is_valid(self, f):
        # f is FigureState
        coords = f.get_figure()
        pivot_x = f.x
        pivot_y = f.y

        for dy, dx in coords:
            y = pivot_y + dy
            x = pivot_x + dx
            if not self.is_in_bounds(y, x):
                return False
            if self.b[y][x] == Cell.FULL:
                return False
        return True

    def is_in_bounds(self, y, x):
        if y < 0 or y >= len(self.b):
            return False
        if x < 0 or x >= len(self.b[y]):
            return False

    def lock_figure(self, f):
        coords = f.get_figure()
        pivot_x = f.x
        pivot_y = f.y

        for dy, dx in coords:
            y = pivot_y + dy
            x = pivot_x + dx
            self.b[y][x] = Cell.FULL


class Error(Exception):
    pass

class GameState:
    def __init__(self, js, seed):
        self.init_board_state(js)
        self.figure_generator = FigureGenerator(js, seed)

    def init_board_state(self, js):
        xmax = js['width']
        ymax = js['height']
        b = [[Cell.EMPTY for i in xrange(xmax)] for j in xrange(ymax)]
        for cell in js['filled']:
            y = cell['y']
            x = cell['x']
            b[y][x] = Cell.FULL
        self.b = b


    def make_move(self, move):
        next_figure = self.current_figure.clone()
        if self.board_state.is_valid(next_figure):
            self.current_figure = next_figure
        else:
            print "Unit was locked"
            self.board_state.lock_figure(self.current_figure)



class FigureGenerator:
    def __init__(self, js, seed):
        self.seed = seed
        self.figures = []
        for f in js['units']






