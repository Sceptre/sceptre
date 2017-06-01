# 04 Remove cascading config for stack config files

Stack config files support [cascading config](http://sceptre.cloudreach.com/docs/environment_config.html#id1). This is mainly used for reducing repeated config when launching the same stack in multiple environments, such as launching a stack which enables CloudTrail in each region.

The following problems stem from cascading stack config:

1. It makes it impossible to launch stacks which are contained in an environment which also contains a sub environment.

  Given the following sceptre project:
  ```
  .
  └── config
      └── dev
          ├── ew1
          │   └── vpc.yaml
          └── vpc.yaml
  ```
  We have no way of knowing whether `dev/vpc.yaml` is a stack in its own right, or if it's an incomplete stack that `dev/ew1/vpc.yaml` completes. When we run `launch-env`, we have to exclude `dev/vpc.yaml`.
2. Using cascaded stack config can lead to complex environments with lots of empty files:

  ```
  .
  └── config
      └── dev
          ├── ew1
          │   └── cloud_trail.yaml  # empty file
          ├── ew2
          │   └── cloud_trail.yaml  # empty file
          ├── ...
          └── cloud_trail.yaml
  ```
  If there are lots of cascaded stack config files, it can be difficult to reason where config items are set.
3. Cascading config for stacks is poorly implemented, and a better implementation would introduce complexity.

  Stack config items, such as `sceptre_user_data` can be nested. Cascaded config currently replaces the whole item:
  ```
  # dev/cloud_trail.yaml
  ...
  sceptre_user_data:  # All of these items are overwritten, even though users may think that only repeated_param should be overwritten
    repeated_param: old_value
    unique_param: value

  ---

  # dev/ew1/cloud_trail.yaml
  ...
  sceptre_user_data:
    repeated_param: new_value

  ```

I think the benefits of cascaded stack config are outweighed by the negatives.

## Implementation

This is probably easiest implemented by creating a new stack config object as stack and environment config will be sufficiently different. The existing config object already has two initialisers..

## Pros
- Fixes problems listed above
- Reduces Sceptre complexity

## Cons
- Removes a feature
