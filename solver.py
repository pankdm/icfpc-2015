#!/usr/bin/env python

# from tetris import *
from tetris import *

from all_includes import *
from collections import deque
import profile
from config import Config
from check_seq import *
    
class ISolver:
    def solve(js):
        # returns string representing the answer
        return ""

# some helper functions
def do_bfs(board_state, s, f):
    q = deque([s])
    all_states = {s: None}
    terminal_states = {}
    
    while q:
        now = q.popleft()
        for move in ALL_MOVES:
            next = now.next_state(move, f)
            # skip visited states
            if next in all_states:
                continue
            if not board_state.is_valid(next, f):
                terminal_states[now] = move
                continue
            q.append(next)
            all_states[next] = (move, now)
    return terminal_states, all_states

# returns "score": the more, the better
def score_position(board_state, s, f):
    ls = len(board_state.compute_lines_to_clear(s, f))

    # add position bonus
    score = ScoreCount.compute_line_bonus(ls)
    score += 0.01 * f.get_min_y(s)

    return score

def go_backwards(all_states, finish, start):
    result = []
    now = finish
    while now != start:
        move, now = all_states[now]
        result.append(move)

    result.reverse()
    return result

class SimpleSolver(ISolver):
    def __init__(self):
        pass

    def solve(self, js):
        answers = {}
        for seed in js['sourceSeeds']:
            answers[seed] = self.solve_seed(js, seed)
        return answers

    def solve_seed(self, js, seed):
        try:
            # print 'solving seed', seed
            tetris = Tetris(js, seed)
            solution = []
            self.solve_tetris(tetris, solution)
        except GameEnds as e:
            print e
            print tetris.get_score()
            ans = moves_to_string(solution)
            return (tetris.get_score(), ans)
            # print answers[seed]

    def solve_tetris(self, tetris, solution):
        if Config.PRINT_SOLVER_INFO:
            tetris.print_board()


        while True:
            f = tetris.current_figure
            s = tetris.s
            board_state = tetris.board_state

            terminal_states, all_states = do_bfs(board_state, s, f)
            if Config.PRINT_SOLVER_INFO:
                tetris.print_board()
                print 'can go to', len(all_states)

            best_state = None
            best_score = None
            for state in terminal_states:
                score = score_position(board_state, state, f)
                # print state, '-->', score
                if best_score == None or score > best_score:
                    best_state = state
                    best_score = score

            moves = go_backwards(all_states, best_state, s)
            if Config.PRINT_SOLVER_INFO:
                print 'will go to', best_state, 'score = ', score
                print 'found a path with ', len(moves)
            for move in moves:
                solution.append(move)
                tetris.make_move(move)

            last_move = terminal_states[best_state]
            solution.append(last_move)
            tetris.make_move(last_move)

            
            if Config.PRINT_SOLVER_INFO:
                getch.getch()
            

def check_one():
    Config.PRINT_SOLVER_INFO = False
    Config.VERIFY_NP_VALID = True

    js = parse_file(sys.argv[1])
    seed = js['sourceSeeds'][0]
    ans = SimpleSolver().solve_seed(js, seed)
    print 'score = ', ans
    print 'Now checking', seed
    score, seq = ans
    check_sequence_score(js, seed, seq, False)


def main():
    Config.PRINT_SOLVER_INFO = True
    js = parse_file(sys.argv[1])
    seed = js['sourceSeeds'][0]
    ans = SimpleSolver().solve_seed(js, seed)

    # for seed in ans:
    #     print 'Now checking', seed
    #     score, seq = ans[seed]
    #     check_sequence_score(js, seed, seq, False)




if __name__ == '__main__':
    # profile.run('main()')
    # main()
    check_one()


