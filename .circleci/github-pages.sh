#!/bin/bash
# This builds docs from current sceptre version and pushes it to the website with lies in separate repository
set -e
# required env vars
declare -a vars=(
    REPOSITORY_PATH # directory in container where dest repo is initialized within container
    GITHUB_EMAIL  # email which is associated with commit message and github account
    CIRCLE_USERNAME  # built in variable in CIRCLE CI - should be same as user who pushes to repository
  )
for var_name in "${vars[@]}"
do
    [[ -z "$(eval "echo \$${var_name}")" ]] && { echo "Variable ${var_name} is not set or empty"; exit 1; }
done

PROJECT_DIR=$(pwd)
GITHUB_NAME=${CIRCLE_USERNAME}

mkdir -p ${REPOSITORY_PATH}

#### go to docs dir, setup git and upload the results #####
cd ${REPOSITORY_PATH}


if [[ -n "${DEPLOYMENT_GIT_HTTPS}" ]]; then
    CLONE_URL="https://${GITHUB_NAME}:${GITHUB_TOKEN}@${DEPLOYMENT_GIT_HTTPS#*"https://"}"
else
    CLONE_URL=${DEPLOYMENT_GIT_SSH}
fi

# strip directory from repo url
DEPLOY_DIR_NAME=$(basename ${CLONE_URL%.*})

# clone web site
git clone ${CLONE_URL}

# ensure sceptre-docs exist in destination directory
BUILD_DIR=${REPOSITORY_PATH}/${DEPLOY_DIR_NAME}${RENDERED_DOCS_DIR:+"/${RENDERED_DOCS_DIR}"}

mkdir -p ${BUILD_DIR}

# name of the docs version in master branch (assuming it's latest published version)
VERSION="${DOCS_DEV_VERSION:-"dev"}"
 # deploy tagged version and strip 'v' from version
if [[ -n "${CIRCLE_TAG}" ]]; then
    VERSION=${CIRCLE_TAG#*v}
    LATEST_REDIRECT='<meta http-equiv="refresh" content="0; url='${VERSION}'" />'
    # update stable link
    echo ${LATEST_REDIRECT} > ${BUILD_DIR}/index.html
    echo updating latest link
    cd ${BUILD_DIR}
    ln -fns ${VERSION} latest
    cd -
fi

VERSION_BUILD_DIR=${BUILD_DIR}/${VERSION}

echo "Building docs in" ${VERSION_BUILD_DIR}

# remove version directory if exists
rm -rf ${VERSION_BUILD_DIR}

# build docs in correct dir
sphinx-apidoc -fM -o "${PROJECT_DIR}/docs/_source/apidoc" ${PROJECT_DIR}/sceptre
sphinx-build ${PROJECT_DIR}/docs/_source ${VERSION_BUILD_DIR} -q -d /tmp -b html -A GHPAGES=True -A version=${VERSION}

# remove old versions
OLD_VERSIONS=$(python3 "${PROJECT_DIR}/.circleci/documentation-versions.py" "${BUILD_DIR}")

# backup standard IFS and use "," instead
OIFS=${IFS}
IFS=","
rm -rf ${OLD_VERSIONS}
# restore standard IFS
IFS=${OIFS}

# go to site/docs
cd ${DEPLOY_DIR_NAME}

# setup git user
git config --global user.email "${GITHUB_EMAIL}" > /dev/null 2>&1
git config --global user.name "${GITHUB_NAME}" > /dev/null 2>&1

git add -A

COMMIT_MESSAGE="Update docs version ${VERSION}" # commit sha: ${}


if [[ -n "${DEPLOYMENT_GIT_HTTPS}" ]]; then
    GH_PAGES_URL="https://${GITHUB_NAME}:${GITHUB_TOKEN}@${DEPLOYMENT_GIT_HTTPS#*"https://"}"
else
    GH_PAGES_URL=${DEPLOYMENT_GIT_SSH}
fi

git remote add website ${GH_PAGES_URL}

git commit -am "${COMMIT_MESSAGE}"
git push -f website master

echo "Finished Deployment!"
