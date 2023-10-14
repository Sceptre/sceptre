# Sceptre release process

Poetry is used to manage versions and deployments. Follow the below steps to release a version to pypi.

1. Bump the package version (i.e. `poetry version minor`)
2. Update Changelog with details from Github commit list since last release
3. Create a PR for above changes
4. Once PR is merged, `git pull` the changes to sync the *master* branch
5. `git tag -as vX.Y.Z`
6. `git push origin vX.Y.Z` (CI/CD publishes to PyPi)
7. Get list of contributors with
   `git log --no-merges --format='%<(20)%an' v1.0.0..HEAD | sort | uniq`, where
   the tag is the last deployed version.
8. Announce release to the #sceptre channel on og-aws Slack with a link to
   the latest changelog and list of contributors
