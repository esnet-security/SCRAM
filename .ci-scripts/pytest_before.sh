#!/bin/sh

set -e

if [ -z "${CI_REGISTRY}" ]; then
    # Running in GitHub
    export COMPOSE_PROJECT_NAME=$GITHUB_RUN_ID
    make build
else
    # Running in Gitlab
    apk add make
    docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    export COMPOSE_PROJECT_NAME=$CI_PIPELINE_ID
    .ci-scripts/pull_images.sh
    make build
    .ci-scripts/push_images.sh
fi

make migrate
make run
