---
layout: docs
title: Resolvers
---

# Overview

The purpose of this resolver is to fetch Amazon Linux AMI IDs from AWS CLI. 

## Available Resolvers

### fetch_ami

Fetches the correct AMI ID based on the paramaters passed to it

Syntax:

```yaml
sceptre_user_data:
	InstanceProperties:
	    ImageId: !fetch_ami typeOfAMI
```

Example:

Use sceptre to fetch the correct AMI you need for your environment:
```yaml
sceptre_user_data:
	InstanceProperties:
	    ImageId: !fetch_ami HVM (SSD) EBS-Backed 64-bit
```

Types of AMIs allowed:

```
HVM (SSD) EBS-Backed 64-bit
HVM Instance Store 64-bit
PV EBS-Backed 64-bit
PV Instance Store 64-bit
HVM (NAT) EBS-Backed 64-bit
```
