# CHANGELOG

Categories: Added, Removed, Changed, Fixed, Nonfunctional, Deprecated

## Unreleased

## 2.1.3 (2019.05.14)

### Fixed

- Fix `stack_name` for s3 upload in Windows environment.

## 2.1.2 (2019.05.09)

### Fixed

- Fix `stack_output` resolver recursion error.

## 2.1.1 (2019.05.01)

### Fixed

- Fix CLI list output export issue.

- Fix path separators between operating systems.

- Fix S3 uploads to support China regions.

### Nonfunctional

- Upgrade to PyYaml 5.1.

- Update custom hook docs.

- Improve documentation site.

## 2.1.0 (2019.03.01)

### Added

- Support for SAM templates.

- Improve handling of missing config attributes.

### Nonfunctional

- Update colorama dependency version.

- Fix circleci build

## 2.0.3 (2019.02.15)

### Fixed

- Fix ConfigReader to follow symbolic links.

- Fix output of `--output yaml` with Python objects.

- Fix CLI `update change-set` command.

### Nonfunctional

- Improve Documentation.

- Fix Migration Guide documentation on `tags` vs `stack_tags`.

- Improve formatting of CLI `--help` command.

- Update `six` dependency version.

## 2.0.2 (2019.01.10)

### Fixed

- Fix `write` method in `sceptre.cli.helpers` to better handle `yaml` and `json`
  output format.

- Fix `sceptre generate` in CLI so that it respects `--output` flag.

- Update `PyYaml` dependency version to fix `CVE-2017-18342`.

- Fix `--export` option for `sceptre list outputs` for setting environment
  variables.

### Nonfunctional

- Improve `sceptre.stack.Stack.__repr__()` so that objects and lists are not
  contained in strings.

- Remove duplicate timestamp from logging in `plan.actions`.

- Fix minor documentation typo in `stack_group_config.md` stack example.

- Remove redundant `status` self-assignment in `sceptre.plan.actions.launch()`

## 2.0.1 (2018.12.17)

### Fixed

- Fix `list` and `describe` cli output

- Fix circleci and Makefile config

- Fix accessing `command_path` as list in templates

- Fix adding implicit dependencies for `stack_output` resolver

### Nonfunctional

- Improve delete stack confirmation message

- Improve delete change set message

- Add newline in `cli.md` docs to format code block correctly

- Update docs for Custom Resolver `setup.py`

- Update Custom Resolver docs

- Clarify docs on stack_output resolver

## 2.0.0 (2018.11.30)

### Added

- Support for `stack_group_config` via the `Stack()` API.

- Support for accessing `stack_group_config` in Templates

- `--ignore-dependencies` flag to CLI and API.

### Removed

- `write()` from `sceptre.config.graph.StackGraph`

### Fixed

- Describe commands output formatting

- Website Page titles

### Nonfunctional

- Updated Project docs

- Updated Website Documentation

- Removed unnecessary string from CLI output

## 2.0.0rc1-2 (2018.11.22)

### Fixed

- Added missing `stack_group_config` attributes to Stack.

## 2.0rc1 (2018.11.21)

### Added

- StackGraph (5171ae0)

- SceptreContext (c17cfc5)

- SceptrePlan (ab38157)

- SceptrePlanExecutor (ab38157)

- Support for cross-StackGroup dependencies (0b104db)

- StackActions (e8e34e8)

### Removed

- Environments. Stacks & their relationships are now held in StackGraph
  (0b104db)

### Changed

- Config.yaml `template_path` attribute. By default Sceptre uses "templates" as
  the root directory for `template_path` so the user should not specify
  `templates/` as part of the `template_path` attribute (0b104db)

- Update docstrings (0b104db)

- Stack class. The functions available to Stacks are stored in StackActions
  (0b104db)

### Nonfunctional

- Updated project documentation such as README (0b104db)
- Changed project cocs to use Markdown format (README, CHANGELOG, CONTRIBUTING)
  (0b104db)

## 1.4.2 (2018.09.11)

- Fix Config dict merge strategy returning None

## 1.4.1 (2018.08.22)

- Fix KeyError when merging configs

## 1.4.0 (2018.08.02)

- Update Click and PyYaml dependency versions
- Improve delete-change-set output message
- Add stack configuration merging strategies
- Add AMI Resolver to contrib/
- Fix launch environment dependency path
- Add error message for non-leaf environments
- Add KMS resolver to contrib
- SSM resolver to contrib
- Improve error handling in CLI and StackOutput
- Amend linting for integration tests and docs
- Decrease the number of circleci parallel runs
- Update Jinja dependency version to `<=2.8`
- Add ".template" as allowed file extensions for templates
- Add bash-completion script to contrib
- Add a contrib directory for non-core community contributions
- Update docs Makefile
- Add HTML title header and icon to docs

## 1.3.4 (2018-02-19)

- Fixed CircleCi PyPi Deployment
- Update Boto3 requirements

##1.3.3 (2018-02-19)

- Released in Error. Contained breaking changes from v2. Fixed in 1.3.4.

## 1.3.2 (2017.11.28)

- Improving stack dependency resolution.
- Improving CLI output for validate template command.
- Consolidating pip requirements files.
- Fixing Python 3 support.
- Fixing documentation typos.

## 1.3.1 (2017.10.23)

- Removing sceptre diff command.
- Adding support for the stack notifications attribute in stack config.
- Fixing bug which caused session re-creation on every boto call.

## 1.3.0 (2017.10.16)

- Re-adding the ability to specify credential profile in the environment config.
- Adding init project command to help initialize a new Sceptre project.
- Adding init env command to help initialize a new Environment config.
- Adding diff command to display differences between the local and deployed
  stack template.
- Fixed error message displayed for empty environments.
- Adding `environment_config` to config template rendering.
- Adding `on_failure` parameter to stack config.
- Adding automatic renewal of expired credentials when assuming IAM Roles.
- Deprecating use of `bash` hook in favour of `cmd` hook.
- Deprecating use of `asg_scheduled_actions` hook in favour of
  `asg_scaling_processes` hook.
- Adding status colouring for output of describe-env command.
- Fix spelling mistakes in documentation.

## 1.2.1 (2017.7.21)

- Changing Jinja rendering for templates only with '.j2' extension.
- Fixing broken links in documentation website.
- Updating references to Python templates instead of Troposphere templates.

## 1.2.0 (2017.7.14)

- Increasing maximum number of boto call retires from 5 to 30.
- Adding support Jinja rendering for stack templates.
- Adding stricter requirements for existing stack state when launch
  environments.
- Adding `cmd` hook for better cross platform support.
- Adding documentation around architecture of Sceptre projects.
- Adding versioned documentation.
- Improving documentation formatting.
- Fixing path error bug when using environment level commands on Windows.
- Fixing bug to correctly throw an AtrributeError in a Python stack template.

## 1.1.2 (2017.5.26)

- Fixing bug for `protect` in stack config.

## 1.1.1 (2017.2.29)

- Respect --dir when loading custom resolvers and hooks.

## 1.1.0 (2017.3.3)

- Include Scope in `update-stack-cs` output.
- Updates to documentation.

## 1.0.0 (2017.1.31)

- Removing deprecation notices.
- Updating documentation.

## 0.50.0 (2017.1.24)

- Changing syntax used for resolvers and hooks in config files.
- Deprecating use of `sceptre_get_template` function in Troposphere templates.
- Deprecating the accessing of Troposphere templates returned from
  `sceptre_get_template`.
- Deprecating the accessing of Troposphere templates from the global variable
  `t`.
- Deprecating the global variable `SCEPTRE_USER_DATA`.
- Adding support for `sceptre_handler` function in Troposphere templates.
- Adding support for pure CloudFormation JSON strings returned by
  `sceptre_handler`.
- Adding support for `sceptre_user_data` passed to `sceptre_handler`.
- Fixing bug in update-stack-cs.
- Adding project-variables resolver.

## 0.49.1 (2017.1.6)

- Adding documentation for CloudFormation Service Role.

## 0.49.0 (2017.1.6)

- Updating documentation on hooks.
- Adding support for CloudFormation Service Role.
- Adding support for custom stack names.
- Removing (before|after)\_launch hook.
- Changing documentation styling.
- Adding Python 3 support.
- Adding --verbose argument to describe-change-set.
- Adding support for launching stacks without uploading the template to S3.
- Adding a FAQ section on `parameters` vs `sceptre_user_data`.
- Adding support for CloudFormation template written in YAML.
- Bumping boto3 requirement.
- Adding more intuitive delete stack message.
- Removing profile.
- Fixing a multithreading bug.
- Improve CLI UX by printing only an exception's message, not the whole stack
  trace.
- Adding environment path check.
- Refactoring out code that fetches stack status.

## 0.48.0 (2016.12.5)

- Fixing StackStatusColourer: UPDATE_FAILED wan't coloured.
- Fixing bug from uploading templates to S3 from Windows.
- Improving exception thrown when a user tries to use the stack output resolve
  on a stack with no outputs.

## 0.47.0 (2016.12.1)

- Launch now deletes stacks in the CREATE_FAILED or ROLLBACK_COMPLETE states
  before re-creating them.
- Adding support for Troposphere<1.10.0.

## 0.46.0 (2016.11.11)

- Adding support for multiple environments.
- Speeding up integration tests.
- Switching to CircleCI for continuous integration and deployment of
  documentation.
- Changing template S3 key to use a UTC timestamp rather than seconds since
  epoch.
- Changing update-stack-cs to delete the change set by default.
- Stopping appending region to template bucket name.
- Refactoring logger.
- Changing exception names from <Name>Exception to <Name>Error.
- Publishing development docs to http://sceptre-dev.ce-tools.cloudreach.com/.

## 0.45.0 (2016.08.25)

- Adding support for Troposphere 1.8.
- Adding stack protection support.
- Adding support for allowing Troposphere templates to import modules from
  parent directories.
- Adding documentation section for IAM role setup.
- Fixing bug in update-wth-cs command.

## 0.44.0 (2016.08.5)

- Adding require_version.
- Renaming --machine-readable to --output.
- Refactoring hook.py.

## 0.43.4 (2016.08.2)

- Improving logging.

## 0.43.3 (2016.08.2)

- Updating CONTRIBUTING.rst.

## 0.43.2 (2016.08.1)

- Fixing multithreaded S3 bucket create bug.

## 0.43.1 (2016.08.1)

- Deprecating the CLI flags --iam-role, --profile, --region.

## 0.43.0 (2016.08.1)

- Adding machine readable output support.

## 0.42.0 (2016.08.1)

- Adding support for CAPABILITY_NAMED_IAM.

## 0.41.0 (2016.07.28)

- Adding Resolver support for sceptre_user_data.

## 0.40.0 (2016.07.28)

- Adding plugin support for Parameter Resolvers and Hooks.

## 0.39.2 (2016.07.21)

- Fixing exit status bug.

## 0.39.1 (2016.07.15)

- Updating requirements.

## 0.39.0 (2016.07.15)

- Add sceptre_hooks.
- Add builtin suspend and resume asg scaling actions.

## 0.38.4 (2016.07.14)

- Adding deprecation warning for --profile, --region, --iam_role.

## 0.38.3 (2016.07.14)

- Combining account_id and iam_role into a single parameter, iam_role, which is
  now the ARN of the IAM Role to assume.
- Fixing bug in integration tests.

## 0.38.2 (2016.07.14)

- Updating docs.

## 0.38.1 (2016.07.14)

- Updating docstrings.

## 0.38.0 (2016.07.14)

- Removing autocomplete as it broke integration tests.
- Fixing integration tests.

## 0.37.0 (2016.07.13)

- Adding the ability to tag stacks created by Sceptre.

## 0.36.0 (2016.07.12)

- Adding templating support to config files.

## 0.35.1 (2016.07.12)

- Fixing permissions on autocomplete files.

## 0.35.0 (2016.07.12)

- Sceptre now encrypts templates uploaded to S3 using AES256 by default.

## 0.34.0 (2016.07.12)

- Adding autocomplete support for bash and zsh.

## 0.33.0 (2016.07.11)

- Specify sceptre directory via --dir flag.

## 0.32.0 (2016.07.11)

- Refactoring how parameters are handled internally.
- Adding stack_output_external resolver.
- Adding the ability to explicitly specify dependencies.

## 0.31.0 (2016.07.11)

- Adding sceptre-update-cs.

## 0.30.0 (2016.07.08)

- Tail stack events for sceptre execute-change-set.
- Added formatted output for sceptre describe-change-set.

## 0.29.1 (2016.07.08)

- Fixing CI bug in 0.29.0.

## 0.29.0 (2016.07.08)

- Adding automatic support for no-colour'ed output.

## 0.28.0 (2016.07.07)

- Adding --no-colour flag.

## 0.27.2 (2016.07.07)

- Updating docs to add get-stack-policy and set-stack-policy.

## 0.27.1 (2016.07.07)

- Patching unittests and lint from previous release.

## 0.27.0 (2016.07.07)

- Adding get-stack-policy and set-stack-policy.

## 0.26.1 (2016.07.06)

- Changing ConfigReader object to Config object.

## 0.26.0 (2016.07.06)

- Adding more integration tests.

## 0.25.1 (2016.07.05)

- Fixing UnrecognisedHookTaskTypeException import in hook.py.

## 0.25.0 (2016.07.05)

- Adding describe-env command.

## 0.24.1 (2016.07.05)

- Updating documentation.

## 0.24.0 (2016.07.04)

- Ability to specify the region via the cli.
- Ability to specify a profile via the cli or config.yml.
- Ability to specify a role via the cli.
- Skip role assume when no role is specified in config.yaml or via the cli.

## 0.23.1 (2016.06.30)

- Moving upload_template_to_s3 into the Template object.

## 0.23.0 (2016.06.30)

- Adding support for the cascading of <stack_name>.yaml files.
- Moved --debug flag to be after sceptre keyword (\$ sceptre --debug <command>).
- Refactor how config is handled internally.
- Lazy load stack config and templates.

## 0.22.1 (2016.06.28)

- Adding dependency resolving to create-change-set.

## 0.22.0 (2016.06.27)

- Adding hooks.

## 0.21.2 (2016.06.24)

- Refactoring connection_manager.

## 0.21.1 (2016.06.14)

- Fixing bug in template.py.

## 0.21.0 (2016.06.14)

- Adding sceptre describe-stack-outputs command.

## 0.20.0 (2016.06.14)

- Switching from TROPOSPHERE_DATA to SCEPTRE_USER_DATA.
- Switching from configure to PyYaml.
- Fixing a print stack events error.

## 0.19.0 (2016.06.8)

- Adding Boto3 call retries when request limits are hit.

## 0.18.2 (2016.06.2)

- Removing a potential race condition when storing templates in S3.

## 0.18.1 (2016.05.27)

- Tidying up method names in the Stack() object.

## 0.18.0 (2016.05.26)

- Moving to using threading to launch/delete environments.
- Create/update/launch/delete commands now return non-zero if the command fails.

## 0.17.0 (2016.05.10)

- Adding basic integration tests.

## 0.16.1 (2016.05.9)

- Bumping to Troposphere 1.6.0.

## 0.16.0 (2016.05.4)

- Switching from Docopt to Click, improving support for use as a Python module.

## 0.15.3 (2016.04.21)

- Bumping boto3 dependency version to 1.3.1.

## 0.15.2 (2016.04.21)

- Defend against troposphere_data being a string in yaml.

## 0.15.1 (2016.04.14)

- Moving exceptions into their own file, `exceptions.py`.

## 0.15.0 (2016.04.14)

- Support for automatic reading in of arbitrary files.

## 0.14.1 (2016.04.14)

- Refactor `workplan.py`.

## 0.14.0 (2016.04.11)

- Adding change set support.

## 0.13.3 (2016.04.11)

- Moving dependency resolver code from `workplan.py` to `stack.py`.

## 0.13.2 (2016.04.7)

- Refactoring `stack.py`.

## 0.13.1 (2016.04.7)

- Improving troposphere template not found exception.

## 0.13.0 (2016.04.6)

- Adding `$ sceptre --version`.

## 0.12.1 (2016.04.6)

- Hiding internal class names.

## 0.12.0 (2016.04.6)

- Adding support for reading in environment variables for use as CloudFormation
  parameters.

## 0.11.0 (2016.03.31)

- Adding `continue-update-rollback` command.

## 0.10.2 (2016.03.31)

- Refactoring ConfigReader.

## 0.10.1 (2016.03.31)

- Updating documentation.

## 0.10.0 (2016.03.31)

- Adding Troposphere data injection support.

## 0.9.1 (2016.03.21)

- Minor refactor.

## 0.9.0 (2016.03.21)

- Adding --debug option.

## 0.8.2 (2016.03.21)

- Adding date time to printed out stack events.

## 0.8.1 (2016.03.21)

- Fixing bug in generate-template.

## 0.8.0 (2016.03.21)

- Sceptre now prints out stack events as stacks are being launched or deleted.

## 0.7.1 (2016.03.18)

- Refactoring interactor commands.

## 0.7.0 (2016.03.17)

- Adding lock-stack and unlock-stack commands.

## 0.6.3 (2016.03.16)

- Adding improved error handling for when users enter incorrect stack names.

## 0.6.2 (2016.03.16)

- Adding improved error handling for when users enter incorrect environment
  paths.
- Refactoring config_reader

## 0.6.1 (2016.03.15)

- Updating documentation.

## 0.6.0 (2016.03.15)

- Adding support for user-defined config directory structure.

## 0.5.1 (2016.03.10)

- Sceptre waits after checking a stack's status. This update drops the wait time
  from 3s to 1s.

## 0.5.0 (2016.03.10)

- Adds sceptre validate-template <env> <stack_name> command.

## 0.4.0 (2016.03.10)

- Sceptre now creates, updates and launches stacks from a template it uploads to
  s3.

## 0.3.2 (2016.03.10)

- Fixing create_bucket for region us-east-1.

## 0.3.1 (2016.03.10)

- Sceptre removes trailing slash from template_bucket_name.

## 0.3.0 (2016.03.09)

- Sceptre now appends time since epoch to uploaded JSON template names.

## 0.2.0 (2016.03.09)

- Sceptre now appends region to supplied bucket name.

## 0.1.3 (2016.03.08)

- Adding support for subdirectories in the template_bucket_name param.

## 0.1.2 (2016.03.08)

- Updating Troposphere to version 1.5.0.

## 0.1.1 (2016.03.08)

- Updating tox to only support Python 2.6 versions > 2.6.9.

## 0.1.0 (2016-03-07)

- Changing how parameter chaining is stated in yaml files.

## 0.0.1 (2015-12-13)

- First release.
