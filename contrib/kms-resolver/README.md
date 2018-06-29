---
layout: docs
title: Resolvers
---

# Overview

The purpose of this resolver is to retrieve values from the AWS KMS. 

## Available Resolvers

### kms

Fetches the value stored in AWS KMS.

Syntax:

```yaml
parameter|sceptre_user_data:
    <name>: !kms CIPHERTEXT
```

Example:

Encrypt data with KMS to get a Ciphertext:
```
aws kms --key-id <KMS Key Id> --plaintext <data> --output text --query CiphertextBlob

AQICAHhZyEsV0yflwE0mpKvPz7/O/zc1epgIurV43wXF/qF6MwFQYwZq7TrvtQ2....
```

Use sceptre to retrieve and decrypt the value from KMS:
```
parameters:
    database_password: !kms AQICAHhZyEsV0yflwE0mpKvPz7/O/zc1epgIurV43wXF/qF6MwFQYwZq7TrvtQ2...
```
