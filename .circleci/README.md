##### Required env variables

* `REPOSITORY_PATH` - directory in container where dest repo is initialized within container
* `DEPLOYMENT_GIT_SSH` or `DEPLOYMENT_GIT_HTTPS`' - destination repository for rendered pages
   * `DEPLOYMENT_GIT_SSH` - requires adding SSH key to the CircleCI + deploy key with push rights to the target repository 
   * `DEPLOYMENT_GIT_HTTPS` - requires setting up personal access token with push rights to the target repository
* `GITHUB_EMAIL` - email which is associated with commit message and github account
* `GITHUB_TOKEN` - access token with push rights to the target repository `/docs`
* `CIRCLE_USERNAME` - built in variable in CIRCLE CI - should be same as user who pushes to repository

##### Optional evn variables

* `RENDERED_DOCS_DIR` - directory where rendered pages are stored within `DEST_REPO` - default is repository root
* `DOCS_DEV_VERSION` - directory name where latest version of docs are published,
   default value is `dev` will result in path `../docs/dev`