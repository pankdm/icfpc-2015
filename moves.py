from enum import Enum
from copy import deepcopy
from config import Config



class Move(Enum):
    E = 1
    W = 2
    SE = 3
    SW = 4
    CLOCK = 5
    COUNTER_CLOCK = 6
    IGNORE = 7


COMMAND_MAPPING = [
    ("p'!.03", Move.W),
    ("bcefy2", Move.E),
    ("aghij4", Move.SW),
    ("lmno 5", Move.SE),
    ("dqrvz1", Move.CLOCK),
    ("kstuwx", Move.COUNTER_CLOCK),
    ("\t\r\n", Move.IGNORE),
]


NON_ROTATING_MOVES = [
    Move.W,
    Move.E,
    Move.SW,
    Move.SE,
]

ALL_MOVES = [
    Move.W,
    Move.E,
    Move.SW,
    Move.SE,
    Move.CLOCK,
    Move.COUNTER_CLOCK,
]

CHAR_MAPPING = {}
for s, move in COMMAND_MAPPING:
    for char in s:
        assert char not in CHAR_MAPPING, char
        CHAR_MAPPING[char] = move


MOVE_TO_CHARS = {}
for s, move in COMMAND_MAPPING:
    MOVE_TO_CHARS[move] = s

def string_to_moves(s):
    res = []
    for char in s:
        move = CHAR_MAPPING.get(char, None)
        if move == None:
            raise Exception("{} is not a valid Move".format(char))
        res.append(move)
    return res

def moves_to_string(moves):
    res = []
    for move in moves:
        res.append(MOVE_TO_CHARS[move][0])
    return ''.join(res)


