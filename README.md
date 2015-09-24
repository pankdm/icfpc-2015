# Snakes vs Lambdas

![](snakes-vs-lambdas.png)

This year the problem was about writing an AI to play hexagonal tetris.

Here is brief explanation of our solution.

At high level, we use 2-step approach:
1. For current figure using BFS we find the best next position (we call it macro move) according to some heuristic function.
2. For that position we generate sequence of moves that maximizes power words score.

Now let's consider each step in more details

## Macro Moves

First we generated a set of all terminal states (macro moves) where the current figure would be locked.
This is done using BFS. Then each state is scored using weighted sum of the following features (see `deep_solver.py` for more details):
1. **Real score**. Score that is obtained for locking the figure according to game rules. (E.g. the more lines will be cleared by macro move the higher will be score)
2. **Gravity score**. Sum of `-exp(-y / 20.)` for each (x, y), where (x, y) is filled cell of the board. It encourages putting the figure on the lowest lines.
3. **Covered Holes score**. We have 3 features here: number of empty cells that have a filled cell as a top-right neighbor (c1) or top-left neighbor (c2) or both (c3).
4. **Unfinished score**. Sum of `-exp(-num_empty / 6.0)` for each row, where `num_empty` is number of empty cells in this row. It encourages try to fill lines with the least number of empty cells.
5. **Smoothness score**. Sum of `abs(is_empty(x, y) - is_empty(x + 1, y))` for each (x, y) -- basically the number of times filled cell is adjacent to empty within a row. It encourages to put figures more compactly (do not leave holes in a row).

To make computation of this scores more efficient they were represented as vector operations over numpy arrays. For example, gravity score could be computed using formula:

```python
grid = np.mgrid[:np_board.shape[0], :np_board.shape[1]].astype(np.int)
ygrid = grid[0]
gravity_score = -np.sum(np_board * np.exp(-ygrid * 0.05))
```

It's hard to find balance of this scores, so each map has its own hand-tuned set of coefficients:

```python
# Values for
#       Config.DEEPSOLVER_DEPTH, \
#       Config.DEEPSOLVER_COEF_GRAVITY, \
#       Config.DEEPSOLVER_COEF_HOLE1, \
#       Config.DEEPSOLVER_COEF_HOLE2, \
#       Config.DEEPSOLVER_COEF_HOLE3, \
#       Config.DEEPSOLVER_COEF_UNF_ROW, \
#       Config.DEEPSOLVER_COEF_SMOOTH
# respectively
param = {
  0: (1, 150, 1, 1, 10, 0.5, 20),
  1: (1, 50, 1, 1, 1, 0.5, 2),
  2: (1, 20, 4, 4, 1, 0, 2),
  3: (1, 20, 4, 4, 1, 0, 2),
  4: (1, 70, 1, 1, 3, 0, 2),
  5: (1, 70, 1, 1, 3, 0, 2),
  6: (1, 0, -0.1, +0.2, 10, -145, 2),
  7: (1, 70, 1, 1, 3, 0, 2),
  8: (2, 10, 1, -4, 50, 0, 8),
  9: (1, 0, -1, -1, 10, 0, 2),
  10: (1, 35, 3, -1, 50, -500, 0.4),
  11: (2, 50, 1, 1, 8, 0, 5),
  12: (1, 50, 1, 1, 8, 0, 5),
  13: (1, 50, 1, 1, 8, 0, 5),
  14: (1, 50, 1, 1, 8, 0, 5),
  15: (2, 50, 1, 1, 1, 0, 1),
  16: (1, 50, 1, 1, 1, 0, 1),
  17: (1, 10, 0, 0, 0, 0, 0),
  18: (1, 50, 1, 1, 1, 0, 1),
  19: (1, 50, 1, 1, 1, 0, 1),
  20: (1, 50, 0, 0, 1, -3, 1),
  21: (1, 50, 0, 0, 1, -3, 1),
  22: (1, 70, 1, -10, 10, -460, 4),
  23: (3, 15, 0, 0, 0.3, 2, 15),
  24: (1, 50, 0, 0, 2, 0, 10),
  -1: (1, 50, 1, 1, 1, -100.5, 2),
}
```

We also implemented a couple of heuristics to speed up BFS (this was especially useful on big maps):
 - If the figure is higher than highest filled cell of the map, then use move by formula `Move.SE if current_figure.y % 2 == 0 else Move.SW`
 - If length of BFS queue is more than 40, then don't consider rotations when choosing next move


## Power words

In previous paragraph we described algorithm to compute the macro move for given figure.
Now we will explain how to choose sequence that will put the figure into the position defined by this macro move.

We used BFS that was first considering `ComplexMove`-s (sequence of basic moves that form a power word) and then basic moves itself.
As a score function for BFS we were using number of points we get for this sequence.
Words that were not used before have a score `300 + 2 * length` so algorithm is encouraged to try them first.


## Implementation details

The coordinate system provided in specification was very inconvenient to use, so we converted everything to our own representation of hexagonal grid.

TODO: explanation picture

We extended the `y`-th row by `(y + 1) / 2` cells to the left, and by `width - (y + 1) / 2` cells to the right so that each row has exactly `2 * width` cells.

We represented each figure by coordinates of pivot + list of `(dx, dy) -- relative coordinates of points to pivot.
Our coordinate system is a linear one, so it's relatively easy to compute the rotation of any given point (x, y) around pivot:

```
// Rotation is a affine transformation, to following axioms hold:
R (A + B) = R(A) + R(B)
R (c * A) = c * R(A)
// Now apply it to formula
(y, x) = y * (1, 0) + x * (0, 1)
R( (y, x) ) = R( y * (1, 0) ) + R( x * (0, 1) )
R( (y, x) ) = y * R( (1, 0) ) + x * R( (0, 1) )
// From the system definitions it's clear that
R: (1, 0) -> (0, -1)
R: (0, 1) -> (1, 1)
// And finally
R( (y, x) ) = y * (0, -1) + x * (1, 1) = (x, x - y)
```

Thus we get the following forumla:
```python
new_y = x
new_x = x - y
```

## Infrastructure

We implemented a bunch of scripts that were useful during contest.

**`interactive_tetris.py`** - script to play any map using keyboard. Was useful in debugging various corner cases of game rules implementation

**`tester_one.py`** - script that was solving given problem and sending the result if it's better than latest one. It was very useful to submit solutions with confidence that we will not overwrite the better one.

**`board_stats.py`** - very simple script to output basic statistics about all problems. Was useful in quick understanding complexity of maps. Example output:
```
0 || seeds = 1 || figures = 100 || w = 10, h = 10, total = 100
1 || seeds = 1 || figures = 100 || w = 15, h = 15, total = 225
2 || seeds = 10 || figures = 100 || w = 15, h = 30, total = 450
3 || seeds = 5 || figures = 100 || w = 30, h = 20, total = 600
4 || seeds = 50 || figures = 200 || w = 10, h = 15, total = 150
5 || seeds = 10 || figures = 100 || w = 30, h = 20, total = 600
6 || seeds = 50 || figures = 150 || w = 10, h = 10, total = 100
7 || seeds = 5 || figures = 100 || w = 40, h = 20, total = 800
8 || seeds = 10 || figures = 400 || w = 10, h = 8, total = 80
9 || seeds = 5 || figures = 400 || w = 10, h = 8, total = 80
10 || seeds = 1 || figures = 100 || w = 10, h = 7, total = 70
11 || seeds = 5 || figures = 50 || w = 10, h = 10, total = 100
12 || seeds = 10 || figures = 100 || w = 15, h = 20, total = 300
13 || seeds = 1 || figures = 100 || w = 15, h = 20, total = 300
14 || seeds = 1 || figures = 500 || w = 50, h = 50, total = 2500
15 || seeds = 1 || figures = 100 || w = 15, h = 20, total = 300
16 || seeds = 1 || figures = 100 || w = 15, h = 20, total = 300
17 || seeds = 1 || figures = 100 || w = 15, h = 15, total = 225
18 || seeds = 1 || figures = 1000 || w = 30, h = 30, total = 900
19 || seeds = 1 || figures = 100 || w = 15, h = 15, total = 225
20 || seeds = 1 || figures = 100 || w = 15, h = 15, total = 225
21 || seeds = 1 || figures = 20 || w = 10, h = 8, total = 80
22 || seeds = 1 || figures = 100 || w = 10, h = 8, total = 80
23 || seeds = 1 || figures = 100 || w = 10, h = 9, total = 90
24 || seeds = 1 || figures = 1620 || w = 100, h = 40, total = 4000
```

**``leader_board.py``** -- script to get a current state of leader board. It was useful to periodically obtain and monitor the following information:
 - Rank and score we currently have
 - How much more score we need to have in order to advance
 - Tag of our latest submission

Example output:
```
Ranks files wasn't specified using latest:  rankings/0092-o6ql.js
--------------------------------------------------------------------------------
0 || rank=68, score=4999 (next = 12 more) (need n/a) || power = 4 || tag = v3 /0262-ma6b score 4999 5
1 || rank=70, score=2778 (next = 6 more) (need n/a) || power = 2 || tag = v3 /0263-dwc5 score 2778 5
2 || rank=47, score=7176 (next = 40 more) (need n/a) || power = 5 || tag = v3 /0264-8ojg score 7176 5
3 || rank=65, score=3505 (next = 148 more) (need n/a) || power = 5 || tag = v3 /0265-cwy8 score 3505 5
4 || rank=49, score=4996 (next = 71 more) (need n/a) || power = 5 || tag = v3 /0270-6i0g score 4996 5
5 || rank=58, score=2945 (next = 32 more) (need n/a) || power = 4 || tag = v3 /0273-t67x score 3272 5
6 || rank=54, score=7891 (next = 145 more) (need n/a) || power = 5 || tag = v3 /0276-gq1n score 7891 5
7 || rank=65, score=2107 (next = 398 more) (need n/a) || power = 3 || tag = v3 /0274-rafx score 2107 5
8 || rank=81, score=7784 (next = 180 more) (need 12103 more) || power = 2 || tag = v3 /0245-732g score 7784 5
9 || rank=36, score=3751 (next = 59 more) (need n/a) || power = 0 || tag = /0036-4iu7 deep solver score 3751
10 || rank=71, score=2906 (next = 12 more) (need n/a) || power = 1 || tag = v3 /0255-8tay score 2906 5
11 || rank=83, score=1486 (next = 3 more) (need 4519 more) || power = 2 || tag = v3 /0257-u9kl score 1486 5
12 || rank=107, score=1276 (next = 26 more) (need 7699 more) || power = 0 || tag = v3 /0275-9cug score 1276 5
13 || rank=48, score=1795 (next = 2 more) (need n/a) || power = 5 || tag = v2 /0189-qbyf score 1795 5
14 || rank=70, score=9350 (next = 1302 more) (need n/a) || power = 4 || tag = v3 /0277-tgsy score 9350 5
15 || rank=50, score=3562 (next = 0 more) (need n/a) || power = 5 || tag = v3 /0282-zd6y score 3562 5
16 || rank=59, score=6434 (next = 42 more) (need n/a) || power = 5 || tag = v3 /0285-gl91 score 6434 5
17 || rank=37, score=5472 (next = 44 more) (need n/a) || power = 2 || tag = v3 /0286-a018 score 5472 5
18 || rank=92, score=1625 (next = 40 more) (need 13764 more) || power = 1 || tag = v3 /0284-lijc score 1625 5
19 || rank=40, score=5296 (next = 6 more) (need n/a) || power = 2 || tag = v3 /0283-cx2u score 5296 5
20 || rank=95, score=1944 (next = 6 more) (need 5570 more) || power = 0 || tag = v3 /0278-2d0h score 1944 5
21 || rank=39, score=1386 (next = 2 more) (need n/a) || power = 2 || tag = v3 /0279-ta96 score 1386 5
22 || rank=68, score=4394 (next = 126 more) (need n/a) || power = 2 || tag = v3 /0280-el3f score 4394 5
23 || rank=37, score=1338 (next = 3 more) (need n/a) || power = 1 || tag = v3 /0281-axv5 score 1338 5
24 || rank=72, score=5850 (next = 2324 more) (need n/a) || power = 2 || tag = v2 /0214-46fd score 5850 5
--------------------------------------------------------------------------------
Total rank
rank=59, score=1561 || 1481
In 1 ranks score = 1481, delta = 80
```
