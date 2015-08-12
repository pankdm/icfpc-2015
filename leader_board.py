#!/usr/bin/env python


import urllib2
import json
import os
import argparse

from all_includes import *

# URL = "https://davar.icfpcontest.org/rankings.js"
URL = "http://icfpcontest.org/rankings.js"


TEAM_ID = 143
def get_current_best_score(problem_id):
    js = read_ranks()
    for t in js['data']['settings'][problem_id]['rankings']:
        if t['teamId'] == TEAM_ID:
            assert 'score' in t
            print 'Found: ', t
            return t['score']


def get_latest():
    files = os.listdir('rankings/')
    files.sort(reverse=True)
    if files:
        res = files[0]
    else:
        res = '0001-zzzz.js'
    return res

def download_ranks(file_name=None):
    if file_name == None:
        last = get_latest()
        print "Ranks files wasn't specified using next after: ", last
        now, other = last.split("-", 1)
        next = int(now) + 1
        file_name = "{:04d}-{}.js".format(next, get_random_string(4))

    response = urllib2.urlopen(URL)
    html = response.read()
    index = html.find('{')

    f = open('rankings/' + file_name, 'wt')
    f.write(html[index:])
    f.close()
    return json.loads(html[index:])

def read_ranks(file_name=None):
    if file_name == None:
        file_name = 'rankings/' + get_latest()
        print "Ranks files wasn't specified using latest: ", file_name
    f = open(file_name, 'rt')
    return json.loads(f.read())

def find_team(teams, substring):
    for index, team in enumerate(teams):
        if substring in team['team']:
            return index, team


def main():
    # js = download_ranks("rankings/0001-zzzz.js")
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=None)
    parser.add_argument("--download", action='store_true', default=False)
    parser.add_argument("--s", default="Snakes")
    parser.add_argument("--add_rank", default="10")


    args = parser.parse_args()
    add_rank = int(args.add_rank)

    if args.download:
        download_ranks(args.file)

    js = read_ranks(args.file)

    total_teams = js['data']['rankings']
    index, total_score = find_team(total_teams, args.s)
    total_next_score = total_teams[index - add_rank]['score']
    delta_score = total_score['score'] - total_next_score


    print '--' * 40
    for problem_id, p in enumerate(js['data']['settings']):
        index, team = find_team(p['rankings'], args.s)
        next_score = p['rankings'][index - delta_score]['score']
        power_score = team['power_score']
        our_score = team['score']
        if team['tags']:
            tag = team['tags'][0]
            i = tag.find('new_')
            tag = tag[:i] + tag[tag.find('/'):]
            # tag = tag[tag.find('/') + 1 : ].replace('_', ' ')
            tag = tag.replace('_', ' ')
        else:
            tag = 'EMPTY'
        prev = p['rankings'][index - 1]['score']
        print "{} || rank={}, score={} (next = {} more) (need {}) || power = {} || tag = {}".format(
            problem_id,
            team['rank'],
            our_score,
            prev - our_score,
            str(next_score - our_score) + ' more' if next_score else "n/a",
            power_score,
            tag)

    print '--' * 40
    print 'Total rank'
    print "rank={}, score={} || {}".format(
        total_score['rank'],
        total_score['score'],
        total_next_score,
        total_score['team'])
    print "In {} ranks score = {}, delta = {}".format(add_rank, total_next_score, delta_score)
if __name__ == "__main__":
    main()
