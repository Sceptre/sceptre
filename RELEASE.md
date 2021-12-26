# Sceptre release process

1. Bump version in `./sceptre/__init__.py` & `./setup.cfg`
2. Update Changelog with details from
   `git log --no-merges --format='%<(20)%an' v1.0.0..HEAD | sort | uniq`
   where the version number is the git tag of the last release.
3. Create a PR for above changes
4. Once PR is merged, `git pull` the changes to sync the *master* branch
5. `git tag -as vX.Y.Z`
6. `git push origin vX.Y.Z` (CI/CD publishes to PyPi)
7. Announce release to the #sceptre channel on og-aws Slack with a link to
   the latest changelog
