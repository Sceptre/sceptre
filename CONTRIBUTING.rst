=======================
Contributing to Sceptre
=======================

- `Code of Conduct`_
- `How to Contribute`_

  - `Report Bugs`_
  - `Enhancement Proposal`_
  - `Contributing Code`_

- `Get Started`_
- `Credits`_


Code of Conduct
---------------

This project adheres to the Contributor Covenant `code of conduct <http://contributor-covenant.org/version/1/4/>`_. By participating, you are expected to uphold this code. Please report unacceptable behaviour to sceptre@cloudreach.com.


How to Contribute
-----------------

Report Bugs
***********

Before submitting a bug, please check our `issues page <https://github.com/cloudreach/sceptre/issues>`_ to see if it's already been reported.

When reporting a bug, fill out the required template, and please include as much detail as possible as it helps us resolve issues faster.


Enhancement Proposal
********************

Enhancement proposals should:

* Use a descriptive title.
* Provide a step-by-step description of the suggested enhancement.
* Provide specific examples to demonstrate the steps.
* Describe the current behaviour and explain which behaviour you expected to see instead.
* Keep the scope as narrow as possible, to make it easier to implement.

Remember that this is a volunteer-driven project, and that contributions are welcome.


Contributing Code
*****************

Contributions should be made in response to a particular GitHub Issue. We find it easier to review code if we've already discussed what it should do, and assessed if it fits with the wider codebase.

Beginner friendly issues are marked with the ``beginner friendly`` tag. We'll endeavour to write clear instructions on what we want to do, why we want to do it, and roughly how to do it. Feel free to ask us any questions that may arise.

A good pull request:

* Is clear.
* Works across all supported version of Python.
* Complies with the existing codebase style (`flake8 <http://flake8.pycqa.org/en/latest/>`_, `pylint <https://www.pylint.org/>`_).
* Includes `docstrings <https://www.python.org/dev/peps/pep-0257/>`_ and comments for unintuitive sections of code.
* Includes documentation for new features.
* Includes tests cases that demonstrates the previous flaw that now passes with the included patch, or demonstrates the newly added feature. Tests should have 100% code coverage.
* Is appropriately licensed (Apache 2.0).



Get Started
-----------

1. Fork the ``sceptre`` repository on GitHub.
2. Clone your fork locally::

    $ git clone git@github.org:your_name_here/sceptre.git

3. Install your local copy into a `virtual environment <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_. Assuming you have virtualenv installed, this is how you set up your fork for local development:

.. code-block:: shell

    $ cd sceptre/
    $ # Enable your virtual environment
    $ virtualenv env
    $ source env/bin/activate
    $ # Install Sceptre's development requirements
    $ pip install -r requirements_dev.txt
    $ # Install Sceptre's test requirements
    $ pip install -r requirements_tests.txt
    $ # Install sceptre locally, so you can test your changes
    $ pip install -e .

4. Create a branch for local development:

.. code-block:: shell

    $ git checkout -b <GitHub issue number>-<short description>

5. When you're done making changes, check that your changes pass flake8 and the tests, including testing other Python versions with tox:

.. code-block:: shell

    $ make lint
    $ make test-all
    $ make coverage  # coverage should be 100%

6. Make sure the changes comply with the pull request guidelines in the section on `Contributing Code`_.

7. Commit your changes:

.. code-block:: shell

    $ git add .
    $ git commit

Commit messages should follow `these guidelines <https://github.com/erlang/otp/wiki/Writing-good-commit-messages>`_.

Push your branch to GitHub::

    $ git push origin <description of pull request>

8. Submit a pull request through the GitHub website.


Credits
-------

This document took inspiration from the CONTRIBUTING files of the `Atom <https://github.com/atom/atom/blob/abccce6ee9079fdaefdecb018e72ea64000e52ef/CONTRIBUTING.md>`_ and `Boto3 <https://github.com/boto/boto3/blob/e85febf46a819d901956f349afef0b0eaa4d906d/CONTRIBUTING.rst>`_ projects.
