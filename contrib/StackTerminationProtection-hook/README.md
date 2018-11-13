---
layout: docs
title: Hooks
---

# Overview

The purpose of this hook is to enable and disable the stack
termination protection. 

## Available Hooks

### StackTermination

Enables and disables stack termination.

Syntax:

```yaml
parameter|sceptre_user_data:
    <name>: !stack_termination_protection 'enabled'/'disabled'
```

Example:

Enable stack termination protection after creating stack
and disable stack termination protection before stack deletion:
```
hooks:
  after_create:
    - !stack_termination_protection 'enabled'
  before_delete:
    - !stack_termination_protection 'disabled'
```
