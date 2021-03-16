#!/bin/sh

IMAGES=$(grep image local.yml | cut -f 2- -d: | grep -v :)

for IMAGE in $IMAGES; do
    docker pull ${CI_REGISTRY_IMAGE}/${IMAGE}:latest
    docker image tag ${CI_REGISTRY_IMAGE}/${IMAGE}:latest ${IMAGE}:latest
done

echo "Images pulled if available"
