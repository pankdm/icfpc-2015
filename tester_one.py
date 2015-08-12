#!/usr/bin/env python

# from __future__ import print_function

from all_includes import *
from os import listdir

import argparse
import importlib
import json
import random
import re
import string

from config import Config
import solver
import deep_solver
# import solver_numpy

from check_seq import *
from leader_board import *
from magic_words import *

SOLVERS = {
    'simple_solver': solver.SimpleSolver,
    'deep_solver': deep_solver.DeepSolver,
    # 'numpy_solver': solver_numpy.SimpleSolver
}

VERSION = "v3"

def get_solver_class(solver_name):
    solver = SOLVERS.get(solver_name, None)
    assert solver != None, "unknown solver " + solver
    return solver

class Tester:
    def __init__(self, args):
        self.check_score = args.check_score
        self.send = args.send
        self.write_on_disk = args.write_on_disk
        self.check_solution = args.check_solution

    # will append solutions to solution
    def solve_one_file(self, file_name, solver_name, max_seeds, solutions):
        js = parse_file(file_name)
        problem_id = js['id']

        print '=' * 50
        print "Solving problem " + str(problem_id)
        score = 0
        num_seeds = 0
        answers = {}
        for seed in js['sourceSeeds']:
            if num_seeds >= max_seeds:
                print 'Solved max seeds: ', max_seeds, 'exiting'
                break
            else:
                solver_class = get_solver_class(solver_name)
                solver = solver_class()
                print 'Solving seed {} ({}/{})'.format(
                    seed, num_seeds, len(js['sourceSeeds']))
                old_score, seq = solver.solve_seed(js, seed)
                canonical_score = check_sequence_score(js, seed, seq)
                print 'score: {}, canonical_score: {}'.format(old_score, canonical_score)
                answers[seed] = (canonical_score, seq)
                num_seeds += 1

        print 'Dumping solutions'
        for _, answer in answers.items():
            score += answer[0]

        avg_seed_score = score / len(js['sourceSeeds'])
        for seed, answer in answers.items():
            solution = {}
            solution["problemId"] = problem_id
            solution["seed"] = seed
            solution["solution"] = answer[1]
            tag = VERSION + "_" + random_dir + "_score_" + str(score / len(answers))
            tag = tag + "_" + str(len(MAGIC_WORDS))
            solution["tag"] = tag
            solutions.append(solution)

        if self.write_on_disk:
            path = os.path.join(random_dir, "solution_" + str(problem_id) + ".json")
            f = open(path, "w")
            json.dump(solutions, f, indent=2)
            print "Wrote to file: ", path
            f.close()

        # canonical_score = check_sequence_score(js, seed, seq)
        # print 'Verifying solutions'
        # for seed in answers:
        #     score, seq = answers[seed]
        #     # if score > canonical_score:

        good_to_send = True
        if self.check_score:
            best_score = get_current_best_score(problem_id)
            print 'New score: {}, current: {}'.format(avg_seed_score, best_score)
            if avg_seed_score >= best_score:
                good_to_send = True
            else:
                good_to_send = False


        if self.send:
            if good_to_send:
                print
                print 'Sending by curl'
                os.system("./submit_file.sh " + path)
            else:
                print 'Refusing to send'

        # print()
        return problem_id, score

    def run(self, problem, solver_name, max_seeds, random_dir):
        Config.PRINT_SOLVER_INFO = False
        Config.PRINT_DEEP_SOLVER_INFO = False
        Config.PRINT_TETRIS_INFO = False
        Config.PRINT_BOARD = False

        result = {}
        scores = {}

        solutions = []
        print 'Will write to dir:', random_dir
        if problem != None:
            problem_id, score = self.solve_one_file(problem, solver_name, max_seeds, solutions)
            scores[problem_id] = score

        for score in scores.items():
            print "Test #" + str(score[0]) + ":", score[1]
        print "Total score:", sum(scores.values())
        return solutions


def get_next_random_dir(prefix):
    files = os.listdir('new_solutions/')
    files.sort(reverse=True)
    if files:
        last = files[0]
        now, other = last.split("-", 1)
        next = int(now) + 1
        res = "{:04d}-{}".format(next, get_random_string(4))
    else:
        res = '0001-zzzz'
    return prefix + res

# example usage:
# ./tester_one.py --solver=deep_solver --send --test=p/3.json 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default=None)
    parser.add_argument("--solver", default="simple_solver")
    parser.add_argument("--max_seeds", default=1000)
    parser.add_argument("--solutions_dir", default="new_solutions")
    parser.add_argument("--problems_dir", default="problems")
    parser.add_argument("--re", default="\d+")
    parser.add_argument("--write_on_disk", action='store_true', default=True)
    parser.add_argument("--check_score", action='store_true', default=True)
    parser.add_argument("--check_solution", action='store_true', default=True)
    parser.add_argument("--send", action='store_true', default=False)
    args = parser.parse_args()

    if args.solver == "deep_solver":
        args.send = True

    random_dir = get_next_random_dir('new_solutions/')
    tag = random_dir + "_" + args.solver
    
    # send assumes writing on disk
    if args.send:
        args.write_on_disk = True

    if args.write_on_disk:
        os.mkdir(random_dir)

    tester = Tester(args)
    solution = tester.run(
        args.test,
        args.solver,
        int(args.max_seeds),
        random_dir,
    )
    if args.write_on_disk:
        # os.mkdir(random_dir)
        f = open(os.path.join(random_dir, "all.json"), "w")
        json.dump(solution, f, indent=2)
        print "Wrote to file: ", os.path.join(random_dir, "solution.json")
        f.close()
