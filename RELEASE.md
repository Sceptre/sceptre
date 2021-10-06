# How to release

This documents how to release the Fox fork of Sceptre.

## Bump version

Raise a PR against develop that bumps the version. For example, see [this](https://github.com/fsa-streamotion/sceptre/pull/24) PR.

Note that this step can be automated using the `bumpversion` tool, which will be already installed in the virtualenv. For example:

```text
▶ bumpversion --new-version 2.11.0 minor
```

This will update the version strings in the source code and commit.

## make dist

Run `make dist`. A `whl` file and a `.tar.gz` file is created inside `./dist`.

## Create GitHub release

- Go to https://github.com/fsa-streamotion/sceptre

- On the right-hand side, click [Releases](https://github.com/fsa-streamotion/sceptre/releases).

- Click *Draft a new release*

    * In *Choose a tag* write a new tag like `v2.10.0`.
    * In *Release title* also write the tag like `v2.10.0`.
    * Drag and drop the `whl` and `.tar.gz` to the screen where indicated.
    * Click *Publish release*.

That's it. The new release should now be available to install.

## See also

The upstream release workflow is documented in the the `Release Workflow` section [here](https://github.com/fsa-streamotion/sceptre/blob/02f6021589cd486868cf52bf9818e3afbd265fe6/.circleci/README.md#release-workflow).
