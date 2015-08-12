#!/usr/bin/env python

from __future__ import print_function

from all_includes import *
from os import listdir

import argparse
import importlib
import json
import random
import re
import string

def run(module, solver_class, tests_dir, tests, tag, test_re):
    solver_module = importlib.import_module(module)
    solver_module.Config.PRINT_SOLVER_INFO = False
    solver_module.Config.PRINT_DEEP_SOLVER_INFO = False
    solver_module.Config.PRINT_TETRIS_INFO = False
    solver_module.Config.PRINT_BOARD = False

    result = {}
    scores = {}
    for test in listdir(tests_dir):
        if not re.search(test_re, test):
            continue
        tests = tests - 1
        if tests < 0:
            break

        problem = int(re.findall("\d+", test)[0])
        print("Solving problem " + str(problem))

        solver = getattr(solver_module, solver_class)()
        answers = solver.solve(parse_file(os.path.join(tests_dir, test)))
        score = 0
        solutions = []
        for _, answer in answers.items():
            score += answer[0]
        for seed, answer in answers.items():
            solution = {}
            solution["problemId"] = problem
            solution["seed"] = seed
            solution["solution"] = answer[1]
            solution["tag"] = tag + "_score_" + str(score / len(answers))
            solutions.append(solution)
        
        path = os.path.join(random_dir, "solution" + str(problem) + ".json")
        f = open(path, "w")
        json.dump(solutions, f, indent=2)
        print("Wrote to file: ", path)
        f.close()
        print()
        scores[problem] = score

    for score in scores.items():
        print("Test #" + str(score[0]) + ":", score[1])
    print("Total score:", sum(scores.values()))
    return solutions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("module")
    parser.add_argument("--tests_dir", default="problems")
    parser.add_argument("--max_tests", type=int, default=3)
    parser.add_argument("--re", default="\d+")
    parser.add_argument("--solver_class", default="SimpleSolver")
    parser.add_argument("--solutions_dir", default="solutions")
    parser.add_argument("--submit", action='store_true', default=False)
    args = parser.parse_args()

    random_dir = "solutions/" + ''.join([random.choice(string.lowercase) for i in xrange(16)])
    tag = random_dir + "_" + args.module + "_" + args.solver_class

    os.mkdir(random_dir)
    solution = run(args.module, args.solver_class, args.tests_dir, args.max_tests, tag, args.re)
    if args.submit:
        # os.mkdir(random_dir)
        f = open(os.path.join(random_dir, "solution.json"), "w")
        json.dump(solution, f, indent=2)
        print("Wrote to file: ", os.path.join(random_dir, "solution.json"))
        f.close()
