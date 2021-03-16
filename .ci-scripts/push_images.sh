#!/bin/sh

IMAGES=$(grep image local.yml | cut -f 2- -d: | grep -v :)

for IMAGE in $IMAGES; do
    docker image tag ${IMAGE}:latest ${CI_REGISTRY_IMAGE}/${IMAGE}:latest
    docker push ${CI_REGISTRY_IMAGE}/${IMAGE}:latest
done

echo "Images pushed to GitLab registry"
