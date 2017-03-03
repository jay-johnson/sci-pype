#!/bin/bash

ENV_VERSION_TAG=""

if [[ -e ./src/common/common-bash.sh ]]; then
    source ./src/common/common-bash.sh .
fi

source ./properties.sh .

echo ""
amnt "--------------------------------------------------------"
amnt "Building new Docker image(${maintainer}/${imagename})"
docker build --rm -t $maintainer/$imagename .
last_status=$?
if [[ "${last_status}" == "0" ]]; then
    echo ""
    if [[ "${ENV_VERSION_TAG}" != "" ]]; then
        image_csum=$(docker images | grep "${maintainer}/${imagename} " | grep latest | awk '{print $3}')
        if [[ "${image_csum}" != "" ]]; then
            docker tag $image_csum $maintainer/$imagename:$ENV_VERSION_TAG
            last_status=$?
            if [[ "${last_status}" != "0" ]]; then
                err "Failed to tag image(${imagename}) with Tag(${ENV_VERSION_TAG})"
                lg ""
                exit 1
            else
                good "Build Successful Tagged Image(${imagename}) with Tag(${ENV_VERSION_TAG})"
            fi

            echo ""
            exit 0
        else
            lg ""
            err "Build failed to find latest image(${imagename}) with Tag(${ENV_VERSION_TAG})"
            echo ""
            exit 1
        fi
    else
        good "Build Successful"
        echo ""
        exit 0
    fi
    lg ""
else
    lg ""
    err "Build failed with exit code: ${last_status}"
    echo ""
    exit 1
fi

exit 0
