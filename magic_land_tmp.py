from magic_words import *
from collections import deque
from tetris import *

def go_backwards(all_states, finish, start):
    result = []
    complex_moves = set()
    now = finish
    while not now == start:
        _, move, now = all_states[now]
        #print(now, move)
        if not isinstance(move, ComplexMove):
            result.append(MOVE_TO_CHARS[move][0])
        else:
            result.append(move.seq)
            complex_moves.add(move.seq)
    result.reverse()
    return result, complex_moves

def find_solution(board_state, fig, fig_state, final_state):
    q = deque([fig_state])
    all_states = {fig_state: (0, None, None)}
    terminal_states = []

    not_magic = ["abhoth","ghizghuth"]

    MAGIC_MOVES = []
    for word in ["azores"]:#["nithon", , "magnum innominandum", "zstylzhemgni", , "ph'nglui mglw'nafh cthulhu r'lyeh wgah'nagl fhtagn"]:#"azathoth", "faugn", "dagon", "hastur", "nyarlathotep", "shoggoths", "ph'nglui", "mglw'nafh", "cthulhu", "wgah'nagl", "fhtagn"]:
        move = ComplexMove(word + 'a', 2 * len(word) +
            (300 if not word in board_state.used_magic else 0))
        if not move.valid(fig.max_angle):
            continue
        MAGIC_MOVES.append(move)
    #print(MAGIC_MOVES, fig.max_angle)
    while q:
        cur_fig_state = q.popleft()
        cur_points = all_states[cur_fig_state][0]
        moves = ALL_MOVES

        if cur_fig_state.y + fig.max_y < board_state.min_y - 2:
            moves = [Move.SE if cur_fig_state.y % 2 == 0 else Move.SW]
        elif len(q) >= 200:
            moves = NON_ROTATING_MOVES


        for complex_move in MAGIC_MOVES:
            if cur_fig_state.x + complex_move.min_x + fig.min_x >= 0 and\
                    cur_fig_state.x + complex_move.max_x + fig.max_x < board_state.width and\
                    cur_fig_state.y + complex_move.max_y + fig.max_y + 2 < board_state.min_y:
                next_state = cur_fig_state.clone()
                valid = True
                for move in complex_move.moves:
                    next_state = next_state.next_state(move, fig)
                    valid = valid and board_state.is_valid(next_state, fig)
                    if not valid:
                        break

                if not valid:
                    continue

                points = cur_points + complex_move.points
                if not next_state in all_states or all_states[next_state][0] < points:
                    all_states[next_state] = (points, complex_move, cur_fig_state)
                    q.append(next_state)
                    
        for move in moves:
            next_fig_state = cur_fig_state.next_state(move, fig)

            # skip visited states
            if next_fig_state in all_states:
                continue

            all_states[next_fig_state] = (cur_points, move, cur_fig_state)

            if board_state.is_valid(next_fig_state, fig):
                q.append(next_fig_state)

    solution = go_backwards(all_states, final_state, fig_state)
    return solution


def find_moves_with_magic(macro_move, tetris, final_move):
    ntris = tetris.clone()
    board_state = ntris.board_state
    fig = ntris.current_figure
    fig_state = ntris.s
    solution, used_magic = find_solution(board_state, fig, fig_state, macro_move)
    answer = "".join(solution) + MOVE_TO_CHARS[final_move][0]
    return answer, used_magic


