
#!/bin/bash
# This builds docs from current sceptre version and pushes it to the website with lies in separate repository
set -ex
# show where we are on the machine
echo "we are in:" $(pwd)
ls -laF
# check env vars
declare -a vars=(DOCS_DIR WEBSITE_REPO GITHUB_EMAIL GITHUB_TOKEN CIRCLE_USERNAME)
for var_name in "${vars[@]}"
do
    [[ -z "$(eval "echo \$${var_name}")" ]] && { echo "Variable ${var_name} is not set or empty"; exit 1; }
done
CODE_DIR=$(pwd)
GITHUB_NAME=${CIRCLE_USERNAME}

mkdir -p ${DOCS_DIR}

#### go to docs dir, setup git and upload the results ####
cd ${DOCS_DIR}

# strip directory from repo path
WEBSITE_DIR=$(basename ${WEBSITE_REPO%.*})

# clone web site
git clone ${WEBSITE_REPO}

# ensure sceptre-docs exist in website
BUILD_DIR=${DOCS_DIR}/${WEBSITE_DIR}/docs

mkdir -p ${BUILD_DIR}

VERSION="dev"
 # deploy tagged version and strip 'v' from version
if [[ -n "${CIRCLE_TAG}" ]]; then
    VERSION=${CIRCLE_TAG#*v}
    LATEST_REDIRECT='<meta http-equiv="refresh" content="0; url='${VERSION}'" />'
    echo ${LATEST_REDIRECT} > ${BUILD_DIR}/index.html
fi

VERSION_BUILD_DIR=${BUILD_DIR}/${VERSION}

echo "Building docs in" ${VERSION_BUILD_DIR}

# remove version directory if exists
rm -rf ${VERSION_BUILD_DIR}

# build docs in correct dir
sphinx-build ${CODE_DIR}/docs/_source ${VERSION_BUILD_DIR} -q -d /tmp -b html -A GHPAGES=True -A version=${VERSION}

# remove old versions
OLD_VERSIONS=$(python3 old_versions.py "${BUILD_DIR}")

OIFS=${IFS}
IFS=","
rm -rf ${OLD_VERSIONS}
IFS=${OIFS}

# go to site/docs
cd ${WEBSITE_DIR}

# setup git user
git config --global user.email "${GITHUB_EMAIL}" > /dev/null 2>&1
git config --global user.name "${GITHUB_NAME}" > /dev/null 2>&1

git add -A

COMMIT_MESSAGE="Update docs version ${VERSION}" # commit sha: ${}

GH_PAGES_URL="https://${GITHUB_NAME}:${GITHUB_TOKEN}@${WEBSITE_REPO#*"https://"}"
git remote add website ${GH_PAGES_URL}

git commit -am "${COMMIT_MESSAGE}"
git push -f website master

echo "Finished Deployment!"
