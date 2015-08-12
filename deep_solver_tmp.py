#!/usr/bin/env python

from random import shuffle
from tetris import *
from all_includes import *
from check_seq import *
from collections import deque
import math
from copy import deepcopy
import profile
from magic_land_tmp import find_moves_with_magic

import config
import time
import cPickle as pk
import numpy as np
from datetime import datetime

class ISolver:
    def solve(js):
        # returns string representing the answer
        return ""



def gen_macro_moves_vlad(board_state, fig, fig_state):
    q = deque([fig_state])
    all_states = {fig_state: None}
    terminal_states = []
    
    while q:
        cur_fig_state = q.popleft()
        for move in ALL_MOVES:
            next_fig_state = cur_fig_state.next_state(move, fig)

            # skip visited states
            if next_fig_state in all_states:
                continue

            all_states[next_fig_state] = (move, cur_fig_state)

            if not board_state.is_valid(next_fig_state, fig):
                terminal_states.append((cur_fig_state, move))
                continue
            else:
                q.append(next_fig_state)

    return terminal_states, all_states

# some helper functions
bfs_time = 0.0
def gen_macro_moves(board_state, fig, fig_state):
    time_start = time.time()

    q = deque([fig_state])
    all_states = {fig_state: None}
    terminal_states = []
    
    while q:
        cur_fig_state = q.popleft()
        moves = ALL_MOVES
        #print(cur_fig_state.y, fig.max_y)
        if cur_fig_state.y + fig.max_y < board_state.min_y - 2:
            moves = [Move.SE if cur_fig_state.y % 2 == 0 else Move.SW]
        elif len(q) >= 40:
            moves = NON_ROTATING_MOVES
        for move in moves:
            next_fig_state = cur_fig_state.next_state(move, fig)

            # skip visited states
            if next_fig_state in all_states:
                continue

            all_states[next_fig_state] = (move, cur_fig_state)

            if not board_state.is_valid(next_fig_state, fig):
                terminal_states.append((cur_fig_state, move))
                continue
            else:
                q.append(next_fig_state)

    #time_end = time.time()
    #if Config.PRINT_DEEP_SOLVER_INFO:
        #print "Time:", time_end - time_start
    global bfs_time
    bfs_time += time.time() - time_start
    return terminal_states, all_states

def go_backwards(all_states, finish, start):
    result = []
    now = finish
    while not now == start:
        move, now = all_states[now]
        result.append(move)

    result.reverse()
    return result

def find_moves(macro_move, tetris):
    ntris = tetris.clone()
    board_state = ntris.board_state
    fig = ntris.current_figure
    fig_state = ntris.s
    
    _, all_states = gen_macro_moves(board_state, fig, fig_state)
    return go_backwards(all_states, macro_move, fig_state) 


total_stat_eval = 0.0
def static_eval_np(tetris, debug=False):
    time_a = time.time()

    board_state = tetris.board_state
    fig = tetris.current_figure
    fig_state = tetris.s

    np_board = board_state.b
    width = board_state.width

    grid = np.mgrid[:np_board.shape[0], :np_board.shape[1]].astype(np.int)
    ygrid = grid[0]
    xgrid = grid[1]

    gravity_score = -np.sum(np_board * np.exp(-ygrid * 0.05))

    is_ins = (xgrid >= (ygrid + 1) / 2) & \
            (xgrid < (ygrid + 1) / 2 + width)

    is_empty = is_ins & (np_board == 0)
    holes1 = is_empty[1:, :] & ~is_empty[:-1, :]
    holes2 = holes1.copy()
    holes2[:, 1:] = is_empty[1:, 1:] & ~is_empty[:-1, :-1]
    holes3 = holes1 & holes2
    
    is_border = (xgrid == (ygrid + 1)/2) | (xgrid == (ygrid + 1)/2 + width - 1)
    w_border = (1.0 - 0.9 * is_border[1:,:])
    
    covered_hole_score1 = -np.sum(holes1 * w_border)
    covered_hole_score2 = -np.sum(holes2 * w_border)
    covered_hole_score3 = -np.sum(holes3 * w_border)

    smoothness_score = -np.sum( np.abs(is_empty[:,1:] - is_empty[:,:-1]) )

    unfinished_score = -np.sum( np.exp( -np.sum(is_empty, axis=1) / 6.0 ))

    if debug: \
        print board_state.score_count.get_score(), \
            gravity_score, \
            covered_hole_score1, \
            covered_hole_score2, \
            covered_hole_score3, \
            unfinished_score, \
            smoothness_score

    global total_stat_eval
    total_stat_eval += time.time() - time_a

    return (
        1.0 * board_state.score_count.get_score() + 
        Config.DEEPSOLVER_COEF_GRAVITY * gravity_score +
        Config.DEEPSOLVER_COEF_HOLE1 * covered_hole_score1 +
        Config.DEEPSOLVER_COEF_HOLE2 * covered_hole_score2 + 
        Config.DEEPSOLVER_COEF_HOLE3 * covered_hole_score3 +
        Config.DEEPSOLVER_COEF_UNF_ROW * unfinished_score +
        Config.DEEPSOLVER_COEF_SMOOTH * smoothness_score
        )
    

def static_eval(tetris, debug=False):
    time_a = time.time()

    board_state = tetris.board_state
    fig = tetris.current_figure
    fig_state = tetris.s

    gravity_score = 0.0
    covered_hole_score1 = 0.0
    covered_hole_score2 = 0.0
    covered_hole_score3 = 0.0
    unfinished_score = 0.0
    smoothness_score = 0.0

    width = board_state.width

    for i, row in enumerate(board_state.b):
        num_empty = 1
        smooth_prev = 1
        for j, c in enumerate(row):
            if c == Cell.FULL:
                gravity_score -= math.exp(-i * 0.05)

            if c == Cell.EMPTY and i > 0 and j >= convert_to_good_x(i, 0) and j < right_border(i, width):
                num_empty += 1

                xmin = convert_to_good_x(i-1, 0)
                xmax = right_border(i-1, width) - 1

                ul = 0
                ii, jj = i - 1, j - 1
                if jj < xmin or jj > xmax or board_state.b[ii][jj] == Cell.FULL:
                    ul = 1

                ur = 0
                ii, jj = i - 1, j 
                if jj < xmin or jj > xmax or board_state.b[ii][jj] == Cell.FULL:
                    ur = 1

                s = 1.0# + i/10.0
                if j == convert_to_good_x(i, 0) or j == right_border(i, width) - 1:
                    s = 0.1

                covered_hole_score1 -= ul * s
                covered_hole_score2 -= ur * s
                covered_hole_score3 -= ul * ur * s

            # smoothness
            if j >= convert_to_good_x(i, 0) and j < right_border(i, width) - 0:
                smooth_cur = 1 if c == Cell.FULL else 0
                smoothness_score -= abs(smooth_cur - smooth_prev)
                smooth_prev = smooth_cur

        if smooth_prev == 0:
            smoothness_score -= 1

        unfinished_score -= math.exp(-num_empty / 6.0)

    if debug: \
        print board_state.score_count.get_score(), \
            gravity_score, \
            covered_hole_score1, \
            covered_hole_score2, \
            covered_hole_score3, \
            unfinished_score, \
            smoothness_score

    global total_stat_eval
    total_stat_eval += time.time() - time_a

    return (
        1.0 * board_state.score_count.get_score() + 
        Config.DEEPSOLVER_COEF_GRAVITY * gravity_score +
        Config.DEEPSOLVER_COEF_HOLE1 * covered_hole_score1 +
        Config.DEEPSOLVER_COEF_HOLE2 * covered_hole_score2 + 
        Config.DEEPSOLVER_COEF_HOLE3 * covered_hole_score3 +
        Config.DEEPSOLVER_COEF_UNF_ROW * unfinished_score +
        Config.DEEPSOLVER_COEF_SMOOTH * smoothness_score
        )



def search_eval(tetris, depth):
    if depth == 0:
        #return (None, static_eval(tetris))
        return (None, static_eval_np(tetris))

    board_state = tetris.board_state
    fig = tetris.current_figure
    fig_state = tetris.s
    
    terminal_states, _ = gen_macro_moves(board_state, fig, fig_state)
    #if Config.PRINT_DEEP_SOLVER_INFO:
        #print "Num term states", len(terminal_states)
    
    macro_move_scores = []

    time_tot = 0.0
    for term_fig_state, move in terminal_states:
        #time_a = time.time()
        #ntetris = deepcopy(tetris)
        ntetris = tetris.clone()
        #time_tot += time.time() - time_a
        ntetris.board_state.lock_figure(term_fig_state, fig)
        try:
            ntetris.spawn_next_figure()
            macro_move_scores.append((
                    term_fig_state,
                    move,
                    search_eval(ntetris, depth - 1)[1],
            ))
        except GameEnds as e:
            macro_move_scores.append((
                    term_fig_state,
                    move,
                    -1000000.0, #ntetris.board_state.score_count.get_score() + 0.0,
            ))
    #if Config.PRINT_DEEP_SOLVER_INFO:
       # print "debug time", time_tot

    return sorted(macro_move_scores, key=lambda x: -x[2])[0]


def search_eval2(tetris, depth):
    if depth == 0:
        #return (None, None, static_eval(tetris))
        return (None, None, static_eval_np(tetris))

    board_state = tetris.board_state
    fig = tetris.current_figure
    fig_state = tetris.s
    
    terminal_states, _ = gen_macro_moves(board_state, fig, fig_state)
    #if Config.PRINT_DEEP_SOLVER_INFO:
        #print "Num term states", len(terminal_states)
    
    #if len(terminal_states) > 400:
    #    shuffle(terminal_states)
    #    terminal_states = terminal_states[:400]

    #branch_limits = [20, 10, 5, 2, 2, 2, 2]
    branch_limits = [10, 4, 3, 2, 2, 2, 2]

    for int_depth in range(depth):
        macro_move_scores = []
        #print "== Num moves considered:", len(terminal_states)
        for term_fig_state, move in terminal_states:
            ntetris = tetris.clone()
            ntetris.board_state.lock_figure(term_fig_state, fig)
            try:
                ntetris.spawn_next_figure()
                macro_move_scores.append((
                        term_fig_state,
                        move,
                        search_eval2(ntetris, int_depth)[2]
                ))
            except GameEnds as e:
                macro_move_scores.append((
                        term_fig_state,
                        move,
                        -10000000.0 + tetris.board_state.score_count.get_score(),
                ))

        macro_move_scores = sorted(macro_move_scores, key=lambda x: -x[2])
        terminal_states = [(x[0], x[1]) for x in  macro_move_scores[:branch_limits[int_depth]]]

    return sorted(macro_move_scores, key=lambda x: -x[2])[0]


class DeepSolver(ISolver):
    def __init__(self):
        self.solution = []

    def tune_deepsovler_params(self, i):
        param = {
            0: (1, 150, 1, 1, 10, 0.5, 20),
            1: (1, 50, 1, 1, 1, 0.5, 2),
            2: (1, 20, 4, 4, 1, 0, 2),
            3: (1, 20, 4, 4, 1, 0, 2),
            4: (1, 70, 1, 1, 3, 0, 2),  # d2
            5: (1, 70, 1, 1, 3, 0, 2),
            6: (1, 0, -0.1, +0.2, 10, -145, 2), # d2, 5466

            7: (1, 70, 1, 1, 3, 0, 2),

            8: (2, 10, 1, -4, 50, 0, 8), # d2

            9: (1, 0, -1, -1, 10, 0, 2), # d2, 4780

            #10: (1, 55, 1, -1, 50, 0, 5),
            10: (1, 35, 3, -1, 50, -500, 0.4),

            11: (2, 50, 1, 1, 8, 0, 5),

            12: (1, 50, 1, 1, 8, 0, 5),
            13: (1, 50, 1, 1, 8, 0, 5),
            14: (1, 50, 1, 1, 8, 0, 5),

            15: (2, 50, 1, 1, 1, 0, 1),

            16: (1, 50, 1, 1, 1, 0, 1),

            -1: (1, 50, 1, 1, 1, 0.5, 2),
        }

        if i in param:
            Config.DEEPSOLVER_DEPTH, (Config.DEEPSOLVER_COEF_GRAVITY, \
            Config.DEEPSOLVER_COEF_HOLE1, Config.DEEPSOLVER_COEF_HOLE2, \
            Config.DEEPSOLVER_COEF_HOLE3, Config.DEEPSOLVER_COEF_UNF_ROW, \
            Config.DEEPSOLVER_COEF_SMOOTH) = \
                param[i][0], (float(x) for x in param[i][1:])
    
    def solve_seed(self, js, seed):
        self.tune_deepsovler_params(js['id'])

        tetris = Tetris(js, seed)
        solution = []
        try:
            if Config.PRINT_BOARD:
              tetris.print_board()
            
            global total_stat_eval
            total_stat_eval = 0.0

            game_bfs_time = 0.0
            total_figures = js['sourceLength']
            current_figure = 0
            while True:
                bfs_time_start = bfs_time 
                macro_move, final_move, score = search_eval2(tetris, Config.DEEPSOLVER_DEPTH)
                game_bfs_time += bfs_time - bfs_time_start

                if Config.PRINT_DEEP_SOLVER_INFO:
                    print "Total BFS time:", game_bfs_time
                    print "Best score:", score
                    print macro_move
                    print "static eval time", total_stat_eval
                #getch.getch()

                #for move in find_moves(macro_move, tetris):
                #    solution.append(move)
                #solution.append(final_move)
                moves, magic = find_moves_with_magic(macro_move, tetris, final_move)
                solution.append(moves)

                # apply move
                tetris.board_state.lock_figure(macro_move, tetris.current_figure)
                tetris.board_state.used_magic |= magic
                tetris.spawn_next_figure()
                if Config.PRINT_BOARD:
                    tetris.print_board() 
                    #static_eval(tetris, True)
                    static_eval_np(tetris, True)
                    #getch.getch()

                current_figure += 1
                if current_figure % (total_figures / 10 + 1) == 0:
                    print "{} Processed {} out of {}".format(
                        datetime.now(),                        
                        current_figure, total_figures)

            print "Total BFS time:", game_bfs_time

        except GameEnds as e:
            print e
            print tetris.get_score()
            ans = "".join(solution)
            print(ans)
            answer = (tetris.get_score(), ans)
            if Config.CHECK_SEQ_SCORE:
                check_sequence_score(js, seed, ans, False)
        return answer



    def solve(self, js):
        answers = {}
        for seed in js['sourceSeeds']:
            answers[seed] = self.solve_seed(js, seed)
            #break
        return answers


def main():
    js = parse_file(sys.argv[1])
    DeepSolver().solve(js)

if __name__ == '__main__':
    config.Config.PRINT_TETRIS_INFO = False
    #profile.run('main()')
    main()


