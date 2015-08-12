#!/bin/bash -exv

API_TOKEN='I7ianfAOm8sPEABe+TWK5JJHN4YQcOIzmkI/1p6d4hg='
TEAM_ID="177"

echo $OUTPUT

curl --user :$API_TOKEN -X POST -H "Content-Type: application/json" \
        -d "$OUTPUT" \
        https://davar.icfpcontest.org/teams/$TEAM_ID/solutions
