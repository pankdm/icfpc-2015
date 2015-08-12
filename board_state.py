
from enum import Enum
from copy import deepcopy
from config import Config
from moves import *

import copy
import numpy
import numpy as np

# base formula to convert from ugly coordinats
# to good ones
def convert_to_good_x(y, x):
    return x + (y + 1) / 2

def left_border(y):
    return convert_to_good_x(y, 0)

def right_border(y, width):
    return width + (y + 1) / 2
    # return convert_to_good_x(y, 0) + width



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



class BoardState:
    def __init__(self, board, score_count, width):
        self.b = board
        self.used_magic = set()
        self.score_count = score_count
        self.width = width
        self.min_y = len(self.b) + 1

        # self.init_np_helpers()

        for y in xrange(self.min_y - 1):
            for v in self.b[y]:
                if v == Cell.FULL:
                    self.min_y = y
                    return

        # checks before numpy
        # for y in xrange(len(self.b)):
        #     assert len(self.b[y]) == right_border(y, self.width)

    def init_np_helpers(self):
        np_board = self.b
        self.np_board = np_board
        grid = np.mgrid[:np_board.shape[0], :np_board.shape[1]].astype(np.int)
        ygrid = grid[0]
        xgrid = grid[1]
        self.is_ins = (xgrid >= (ygrid + 1) / 2) & \
            (xgrid < (ygrid + 1) / 2 + self.width)

        # self.is_empty = is_empty

    # const
    def is_np_valid(self, s, f):
        np_board = self.b
        np_rot = f.get_np_shape(s.angle)

        x = s.x + np_rot.dx
        y = s.y + np_rot.dy
        w = np_rot.shape.shape[1]
        h = np_rot.shape.shape[0]

        if x < 0 or y < 0 or x + w > np_board.shape[1] \
                or y + h > np_board.shape[0]:
            return False

        is_empty = self.is_ins & (self.np_board == 0)


        # print x,y, '-->', np_rot.shape
        # print 'is_empty: ', ~self.is_empty[y:(y+h), x:(x+w)]

        return not np.any( (np_rot.shape > 0) & ~is_empty[y:(y+h), x:(x+w)] )



    # const
    def is_valid(self, s, f):
        # f is FigureState
        coords = f.get_shape(s.angle)
        pivot_x = s.x
        pivot_y = s.y
        # print '@', pivot_y, pivot_x

        res = True
        for dy, dx in coords:
            # print 'dy, dx', dy, dx
            y = pivot_y + dy
            x = pivot_x + dx
            if not self.is_in_bounds(y, x):
                res = False
                break
            # print y, x, self.b.shape
            if self.b[y][x] == Cell.FULL:
                res = False
                break
        
        if Config.VERIFY_NP_VALID:
            another_res = self.is_np_valid(s, f)
            if res != another_res:
                print 'res = ', res, ' vs ', another_res
                print coords
                print self.b
            assert res == another_res
        
        return res

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
        for symbol in self.b[y][x_start : right_border(y, self.width)]:
            if symbol != Cell.FULL:
                return False
        return True
