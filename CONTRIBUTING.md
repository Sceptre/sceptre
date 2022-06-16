# Contributing to Sceptre

Thanks for your interest in Sceptre! We greatly appreciate any contributions to
the project.

# Code of Conduct

This project adheres to the Contributor Covenant
[code of conduct](http://contributor-covenant.org/version/1/4/). By
participating, you are expected to uphold this code. Please report unacceptable
behaviour to the [Sceptre github discussion](https://github.com/Sceptre/sceptre/discussions).

# How to Contribute

## Report Bugs

Before submitting a bug, please check our
[issues page](https://github.com/Sceptre/sceptre/issues) and
[discussion board](https://github.com/Sceptre/sceptre/discussions) to see if it's
already been reported.

When reporting a bug, fill out the required template, and please include as much
detail as possible as it helps us resolve issues faster.

## Enhancement Proposal

Enhancement proposals should:

- Use a descriptive title.
- Provide a step-by-step description of the suggested enhancement.
- Provide specific examples to demonstrate the steps.
- Describe the current behaviour and explain which behaviour you expected to see
  instead.
- Keep the scope as narrow as possible, to make it easier to implement.

## Contributing Code

Contributions should be made in response to a particular GitHub Issue. We find
it easier to review code if we've already discussed what it should do, and
assessed if it fits with the wider codebase.

Beginner friendly issues are marked with the `beginner friendly` tag. We'll
endeavour to write clear instructions on what we want to do, why we want to do
it, and roughly how to do it. Feel free to ask us any questions that may arise.

A good pull request:

- Is clear.
- Works across all supported version of Python.
- Complies with the existing codebase style
  ([pre-commit](https://pre-commit.com/))
- Includes [docstrings](https://www.python.org/dev/peps/pep-0257/) and comments
  for unintuitive sections of code.
- Includes documentation for new features.
- Includes tests cases that demonstrates the previous flaw that now passes with
  the included patch, or demonstrates the newly added feature.
- New code should have 100% test coverage. The build will fail if overall
  code-coverage falls below 92%.
- Is appropriately licensed (Apache 2.0).

Please keep in mind:

- The benefit of contribution must be compared against the cost of maintaining
  the feature, as maintenance burden of new contributions are usually put on the
  maintainers of the project.

# Get Started

1. Fork the `sceptre` repository on GitHub.

2. Clone your fork locally

```bash
$ git clone git@github.org:<github_username>/sceptre.git
```

3. Install Sceptre for development (we recommend you use a
   [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/))

```bash
   $ cd sceptre/
   $ pip install -r requirements/prod.txt
   $ pip install -r requirements/dev.txt
   $ pip install -e .
```

4. Create a branch for local development:

```bash
$ git checkout -b <branch-name>
```

5. When you're done making changes, check that your changes pass
   [linting](#Linting), [unit tests](#Unit-Tests) and have
   sufficient coverage and [integration tests](#Integration-Tests)
   pass.

6. Make sure the changes comply with the pull request guidelines in the section
   on `Contributing Code`.

7. Commit and push your changes.

   Commit messages should follow
   [these guidelines](https://github.com/erlang/otp/wiki/Writing-good-commit-messages)

   Use the following commit message format
   `[Resolves #issue_number] Short description of change`.

   e.g. `[Resolves #123] Fix description of resolver syntax in documentation`

8. Submit a pull request through the GitHub website.

## Linting

As a pre-deployment step we syntatically validate files with
[pre-commit](https://pre-commit.com).

Please [install pre-commit](https://pre-commit.com/#install) then run
`pre-commit install` to setup the git hooks.  Once configured the pre-commit
linters will automatically run on every git commit.  Alternatively you
can manually execute the validations by running `pre-commit run --all-files`.

## Unit Tests

Run unit tests or coverage in your current environment - (handy for quickly
running unit tests):

```bash
$ make test
$ make coverage
```

Note: Sceptre aims to be compatible with Python 3, please run unit test
against all supported versions. You will need the corresponding versions
of Python installed on your system.

Run unit tests and coverage on all supported python versions:

```bash
$ make test-all
```

Tox is used to manage python vresions for running unit tests.  If you use pyenv
to manage Python versions, try `pip install tox-pyenv` to make tox and pyenv play
nicely.

## Integration Tests

If you haven't setup your local environment or personal CircleCI account to run
integration tests then follow these steps:

To run on CircleCi (please do this before submitting your PR so we can see that
your tests are passing):

- Login to CircleCi using your Github Account.
- Click `Add Projects`, you will be presented with a list of projects from your
  GitHub Account.
- On your sceptre fork press the `Set Up Project` button.
- You can ignore the setup steps, we already have a CircleCi config file in
  Sceptre. Click "Start Building".
- Modify the `Project Settings`, which can be found by navigating:
  `Builds -> Sceptre` and selecting the `Settings` icon, on the right hand side
  of the page.
- Once in the `Project Settings` section under `Permissions` select
  `AWS Permissions`.
- Add your `Access Key ID` and `Secret Access Key` that is associated with an
  IAM User from your AWS account. The IAM User will require "Full" permissions
  for `CloudFormation` and `S3` and Write permissions for `STS` (AssumeRole).
  For an example please take a look at the Sceptre
  [CI service user policy](https://github.com/Sceptre/sceptre-aws/blob/master/config/prod/sceptre-integration-test-service-access.yaml#L5-L35)

Once you have set up CircleCi any time you commit to a branch in your fork all
tests will be run, including integration tests.

You can also (optionally) run the integration tests locally, which is quicker
during development.

### To run integration tests locally

* `pip install awscli`
* Setup [AWS CLI Environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)
  to work with an AWS account that you have access to.  You can use the same user
  that you use for CircleCi.
* `pip install behave`

_Note_: All integration tests are setup to run in `eu-west-*` region.  If you prefer
to run in a different region you must update the region in each test before running it

### run all tests

```bash
$ behave integration-tests
```

### run a specific feature

```bash
$ behave integration-tests --include <feature-file>
```

### run a specific scenario

```bash
$ behave integration-tests -n "<scenario-name>"
```

# Sponsors

* [Sage Bionetworks](https://sagebionetworks.org/) donated the AWS account for running Sceptre integration
  tests.  Please contact it@sagebase.org for support.
* [GoDaddy](https://www.godaddy.com/) donated [the domain](https://docs.sceptre-project.org) for hosting
  the Sceptre project.  Please contact oss@godaddy.com for support.
* [Cloudreach](https://www.cloudreach.com/) started the Sceptre project and continuted to maintain it
  until the ver 2.4 release.  It has since been extricated from Cloudreach and has been maintained
  by members of the Sceptre open source community.

# Credits

This document took inspiration from the CONTRIBUTING files of the
[Atom](https://github.com/atom/atom/blob/abccce6ee9079fdaefdecb018e72ea64000e52ef/CONTRIBUTING.md)
and
[Boto3](https://github.com/boto/boto3/blob/e85febf46a819d901956f349afef0b0eaa4d906d/CONTRIBUTING.rst)
projects.
