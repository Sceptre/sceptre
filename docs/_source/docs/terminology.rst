Terminology
===========

The following terms will be used though the rest of the Sceptre documentation:

Sceptre Project:
----------------

The directory which stores the top level config directory.

-  **Command Path** The Stack or StackGroup that you want to execute a Sceptre
   command against. For example, if you want to launch ``vpc.yaml`` in the
   example below the command path would be ``dev/vpc.yaml``.

   .. code-block:: text

      .
      └── config
          └── dev
              ├── config.yaml
              └── vpc.yaml

   Where as if you wanted to ``delete`` ``account-1`` in the example below the
   command path would be ``account-1``.

   .. code-block:: text

        .
        └── config
            └── account-1
                └── dev
                    └── eu-west-1
                        ├── config.yaml
                        └── vpc.yaml

Sceptre Context
---------------

Unless you go looking in the code, or you use Sceptre as a python module, you
won’t need to worry about ``SceptreContext``.

``SceptreContext`` is a place where we hold information that is relevant to the
project, including references to the project paths such as the path to your
Sceptre project, templates path, config path, and the default names for your
configuration files.

If you are adding functionality to the CLI or you want to use Sceptre as a
module you will need to create a ``SceptreContext`` and pass it an absolute
path to your Sceptre project directory and the “command_path” - the path you
are going to execute commands on.

Sceptre Plan
------------

As with ``SceptreContext`` you shouldn’t need to interact with ``SceptrePlan``
most of the time.

A ``SceptrePlan`` takes a ``SceptreContext`` and constructs everything you will
need to execute a command against your project. After creating a
``SceptrePlan`` you will be able to call all available methods for your stacks
and access the results from each stack. For example,

.. code-block:: python

   plan = SceptrePlan(context)

   responses = plan.launch()

## SceptrePlanExecutor

You won’t be able to interact with the ``SceptrePlanExecutor`` directly but
this part of the code is responsible for taking a ``SceptrePlan`` and ensuring
all commands on every stack, are executed in the correct order, concurrently.
The executor algorithm focuses on correctness over maximal concurrency. It know
what to execute and when based on a ``StackGraph`` which is created when a
``SceptrePlan`` is created.

StackGraph
----------

A ``StackGraph`` is a Directed Acyclic Graph where the nodes hold ``Stack``
objects and the edges represent a “depends on” relationship. The graph is
created when a ``SceptrePlan`` is instantiated and is then used during the
execution phase to ensure that stack dependency relationships are complete and
correct. Previously, in ``v1`` stack dependencies were available between
``Environments`` and even within ``Environments`` they could be temperamental,
this concept resolves this issue.

StackActions
------------

The ``StackActions`` class takes a ``Stack`` object and uses the data held on
the ``Stack`` when calling AWS. StackActions is used by the
``SceptrePlanExecutor``. To add new functionality you can add a method to
``StackActions`` and it will become available to all ``Stacks`` in Sceptre.
