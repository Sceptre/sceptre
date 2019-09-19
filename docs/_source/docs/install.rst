Installation
============

Using pip
---------

This assumes that you have Python installed. A thorough guide on installing
Python can be found `here <python_install>`_. We highly recommend using Sceptre from within a
``virtualenv``. Notes on installing and setting up ``virtualenv`` can be found
`here <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`__.

Install Sceptre:

``pip install sceptre``

Validate installation by printing out Sceptre’s version number:

.. TODO resolve version in code

``sceptre --version``

.. TODO ask for fix from: https://github.com/sphinx-doc/sphinx/issues/3306

.. parsed-literal::

    Sceptre, version |version|

Update Sceptre:

``pip install sceptre -U``

.. _python_install: http://docs.python-guide.org/en/latest/starting/installation/

Using Docker image
------------------

To use our Docker image follow these instructions:

1. Pull the image ``docker pull cloudreach/sceptre:[SCEPTRE_VERSION_NUMBER]`` e.g.
   ``docker pull cloudreach/sceptre:2.1.3``. Leave out the version number if you
   wish to run `latest`.

2. Run the image. You will need to mount the working directory where your
   project resides to a directory called `project`. You will also need to mount
   a volume with your AWS config to your docker container. E.g.

``docker run -v $(pwd):/project -v /Users/me/.aws/:/root/.aws/:ro cloudreach/sceptre:latest --help``

If you want to use a custom ENTRYPOINT simply amend the Docker command:

``docker run -ti --entrypoint='' cloudreach:test sh``

The above command will enter you into the shell of the Docker container where
you can execute sceptre commands - useful for development.

If you have any other environment variables in your non-docker shell you will
need to pass these in on the Docker CLI using the ``-e`` flag. See Docker
documentation on how to achieve this.
