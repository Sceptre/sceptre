---
layout: docs
title: Resolvers
---

# Overview

The purpose of this resolver is to retrieve values from the AWS SSM. 

## Available Resolvers

### ssm

Fetches the value stored in AWS SSM Parameter Store.

Syntax:

```yaml
parameter|sceptre_user_data:
    <name>: !ssm /prefix/param
```

Example:

Add encrypted data to the parameter store:
```
aws ssm put-parameter --name <parameter prefix>/<parameter name> \
--value <parameter value> --key-id <kms key id> --type "SecureString"
```

Use sceptre to retrieve and decrypt the value from SSM:
```
parameters:
    database_password: !ssm /dev/DbPassword
```
