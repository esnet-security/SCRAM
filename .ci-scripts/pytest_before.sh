#!/bin/sh

set -e

env

if [ -z "${CI_REGISTRY}" ]; then
    # GitHub uses Ubuntu
    apk add make
    docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    export COMPOSE_PROJECT_NAME=$CI_PIPELINE_ID
else
    export COMPOSE_PROJECT_NAME=$GITHUB_REPOSITORY
fi

.ci-scripts/pull_images.sh
make build
.ci-scripts/push_images.sh
make migrate
make run
