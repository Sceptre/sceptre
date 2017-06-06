---
layout: docs
---

# Advanced Patterns

This section details patterns and techniques that advanced users may want to use.

## Using an Environment's Connection Manager

When using Sceptre as a Python module, it is possible to make use of an environment's connection manager to make Boto3 calls to that environment's account and region, using the credentials set in environment config.

Once an environment is initialised, the connection manager can be accessed as follows:

```python
from sceptre.environment import Environment

env = Environment(
    sceptre_dir="string",
    environment_path="string",
    options={}
)

client = env.connection_manager._get_client("<service name>")
```

Where `<service name>` can be any of the services [supported by Boto3](http://boto3.readthedocs.io/en/latest/reference/services/index.html).

This client is a normal Boto3 client, and can be used as such.

