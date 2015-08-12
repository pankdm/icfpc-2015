#!/usr/bin/env python

from magic_words import *
import json

test_words = ["conway.",  "cocke.", "john", "backus", "bigboote"]
test_json = []
idx = 0
for word in test_words:
    solution = {}
    solution["problemId"] = idx
    solution["seed"] = 0
    solution["solution"] = word
    solution["tag"] = "tag"
    test_json.append(solution)
    idx += 1

f = open("word_test.json", "w")
json.dump(test_json, f, indent=2)
f.close()

