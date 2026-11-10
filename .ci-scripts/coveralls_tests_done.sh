#!/bin/sh

# Exits 0 if every workflow that calls coveralls-finish.yml has finished all of its other jobs
# for the given commit, exits 1 otherwise.
# Usage: coveralls_tests_done.sh <commit sha> <event name>
# Requires GH_TOKEN and GH_REPO to be set for the gh CLI (this is the case when called via actions)

# Basically, each test workflow uploads its coverage and then calls coveralls-finish.yml, which runs this
# script. So this runs once per workflow, each time right after that workflow's tests finish.
# The workflows finish whenever they do, and whichever finishes last sees everything as done and
# closes the build. The jobs that finish before the last one see something still going and exit 1,
# leaving the build open for the later ones.

set -e

sha="$1"
event="$2"

for file in .github/workflows/*.yml; do
    # Only look at workflows that upload to Coveralls which are the ones that call coveralls-finish.yml
    grep -q 'uses: ./.github/workflows/coveralls-finish.yml' "$file" || continue
    wf=$(basename "$file")

    # Find this workflow's most recent run for the commit. If it's not found yet, we exit 1 (not done yet)
    run_id=$(gh run list --workflow "$wf" --commit "$sha" --event "$event" --limit 1 --json databaseId --jq '.[0].databaseId')

    # then we list the run's jobs that haven't finished yet (skipping the "Close Coveralls Build"), and exit 1
    pending=$(gh run view "$run_id" --json jobs \
        --jq '[.jobs[] | select(.status != "completed" and (.name | startswith("Close Coveralls Build") | not)) | .name] | join(", ")')
    if [ -n "$pending" ]; then
        echo "$wf: waiting on $pending"
        exit 1
    fi
    # finally, if we've got to this point, we know all the workflows are done, yay!
    echo "$wf: done"
done
