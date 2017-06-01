# 04 Stacks as first-class citizens

Its difficult to instantiate Stack objects directly. In the Sceptre code base, we instantiate Stacks by instantiating their surrounding Environments, which create the stacks for us. Moving to a first-class citizen stack model, where we can interact with stacks directly would

## Implementation

Instantiating a Stack requires passing it environment config and a connection manager. These objects would have to be instantiated within the Stack.

## Pros
- Improves Sceptre's Python API
- Each stack instantiating its own connection manager may make multithreading easier

## Cons
- If each stack in an environment instantiates its own connection manager, we may have to enter an MFA code for each stack, rather than a single one for the environment
- Inefficient if each stack in an environment reads in environment config
- The above two points may be mitigated if Stack optionally accepts environment config and a connection manager, and instantiates them itself if they aren't passed through.
