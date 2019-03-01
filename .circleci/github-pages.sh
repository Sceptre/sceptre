#!/bin/bash
# This builds docs from current sceptre version and pushes it to the website with lies in separate repository
set -e
# show where we are on the machine
echo "we are in:" $(pwd)
ls -laF
# required env vars
declare -a vars=(
    CONTAINER_DEST_REPO_DIR # directory in container where dest repo is initialized within container
    DEST_REPO  # destination repository for rendered pages
    GITHUB_EMAIL
    GITHUB_TOKEN
    CIRCLE_USERNAME
  )
for var_name in "${vars[@]}"
do
    [[ -z "$(eval "echo \$${var_name}")" ]] && { echo "Variable ${var_name} is not set or empty"; exit 1; }
done

PROJECT_DIR=$(pwd)
GITHUB_NAME=${CIRCLE_USERNAME}

mkdir -p ${CONTAINER_DEST_REPO_DIR}

#### go to docs dir, setup git and upload the results #####
cd ${CONTAINER_DEST_REPO_DIR}

# strip directory from repo path
DEST_REPO_DIR_NAME=$(basename ${DEST_REPO%.*})

# clone web site
git clone ${DEST_REPO}

# ensure sceptre-docs exist in destination directory
BUILD_DIR=${CONTAINER_DEST_REPO_DIR}/${DEST_REPO_DIR_NAME}${RENDERED_DOCS_DIR:+"/${RENDERED_DOCS_DIR}"}

mkdir -p ${BUILD_DIR}

# name of the version in master branch
VERSION="dev"
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
OLD_VERSIONS=$(python3 "${PROJECT_DIR}/.circleci/old-versions.py" "${BUILD_DIR}")

OIFS=${IFS}
IFS=","
rm -rf ${OLD_VERSIONS}
IFS=${OIFS}

# go to site/docs
cd ${DEST_REPO_DIR_NAME}

# setup git user
git config --global user.email "${GITHUB_EMAIL}" > /dev/null 2>&1
git config --global user.name "${GITHUB_NAME}" > /dev/null 2>&1

git add -A

COMMIT_MESSAGE="Update docs version ${VERSION}" # commit sha: ${}

GH_PAGES_URL="https://${GITHUB_NAME}:${GITHUB_TOKEN}@${DEST_REPO#*"https://"}"
git remote add website ${GH_PAGES_URL}

git commit -am "${COMMIT_MESSAGE}"
git push -f website master

echo "Finished Deployment!"

