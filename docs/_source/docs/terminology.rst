Terminology
===========

The following terms will be used though the rest of the Sceptre
documentation:

-  **Environment Path**: A slash ('/') separated list of directory names
   which details how to move from the top level config directory to an
   environment directory. For example, with the following directory
   structure, the environment path would simply be ``dev``:

   ::

       .
       └── config
           └── dev
               ├── config.yaml
               └── vpc.yaml

   In the following directory structure, the environment path would be
   ``account-1/dev/eu-west-1``:

   ::

        .
        └── config
            └── account-1
                └── dev
                    └── eu-west-1
                        ├── config.yaml
                        └── vpc.yaml

-  **Launch**: In the context of Sceptre commands, ``launch`` means to
   try to ``create`` a stack. If the stack has already been created,
   Sceptre tries to ``update`` the stack. If there are no updates to be
   performed, ``launch`` returns a zero exit code.
-  **Sceptre Directory**: The directory which stores the top level
   config directory.
