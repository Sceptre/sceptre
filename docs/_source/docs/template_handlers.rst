Template Handlers
=================

Template handlers can be used to resolve a ``template`` config block to a CloudFormation template. This can be used to
fetch templates from S3, for example. Users can create their own template handlers to easily add support for other
template loading mechanisms. See `Custom Template Handlers`_ for more information.

.. warning::

   The ``template_path`` key is deprecated in favor of the ``template`` key.

Available Template Handlers
---------------------------

file
~~~~~~~~~~~~~~~~~~~~

Loads a template from the local file system. This handler supports templates with .json, .yaml, .template, .j2
and .py extensions.  This is the default template handler type, specifying the ``file`` type is optional.

For backwards compatability, when a ``template_path`` key is specified in the Stack config, it is wired to
use the ``file`` template handler.

Syntax:

.. code-block:: yaml

   template:
     type: file
     path: <path>

Example:

.. code-block:: yaml

   template:
     path: storage/bucket.yaml

.. note::

   The ``path`` property can contain an absolute or relative path to the template file.
   This handler assumes a relative path to be from sceptre_project_dir/templates


s3
~~~~~~~~~~~~~

Downloads a template from an S3 bucket.  The bucket is accessed with the same credentials that is used to run sceptre.
This handler supports templates with .json, .yaml, .template, .j2 and .py extensions.

Syntax:

.. code-block:: yaml

   template:
     type: s3
     path: <bucket>/<key>

Example:

.. code-block:: yaml

   template:
     type: s3
     path: infra-templates/v1/storage/bucket.yaml

http
~~~~~~~~~~~~~

Downloads a template from a url on the web.  By default, this handler will attempt to download
templates with 5 retries and a download timeout of 5 seconds.  The default retry and timeout
options can be overridden by setting the `http_template_handler key`_ in the stack group config
file.

Syntax:

.. code-block:: yaml

   template:
     type: http
     url: <url>

Example:

.. code-block:: yaml

   template:
     type: http
     url: https://raw.githubusercontent.com/acme/infra-templates/v1/storage/bucket.yaml



Custom Template Handlers
------------------------

If you need to load templates from a different source, you can write your own template handler.

A template handler is a Python class which inherits from abstract base class ``TemplateHandler`` found in the
``sceptre.template_handlers`` module.

To have Sceptre validate that the ``template`` block specified in the Stack config is correct, template handlers
should provide a JSON schema with the required and optional properties. The ``schema()`` method should be
implemented and return a Python dictionary with the schema. For examples of JSON schemas in Python, please see
the documentation of the `jsonschema library`_.

Template handlers get access to the ``template`` block parameters, ``sceptre_user_data`` and ``connection_manager``.
These properties are available on ``self``. Using ``connection_manager``, template handlers can call AWS endpoints
to perform actions or fetch templates. These correspond to the AWS Python SDK (see Boto3_). For example:

.. code-block:: python

        self.connection_manager.call(
            service="s3",
            command="get_object",
            kwargs={
                "Bucket": bucket,
                "Key": key
            }
        )

Sceptre uses the ``sceptre.template_handlers`` entry point to load template handlers. They can be written anywhere and
are installed as Python packages.

Example
~~~~~~~

The following Python module template can be copied and used:

.. code-block:: text

   custom_template_handler
   ├── custom_template_handler.py
   └── setup.py

The following Python module template can be copied and used:

custom_template_handler.py
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

        from sceptre.template_handlers import TemplateHandler


        class CustomTemplateHandler(TemplateHandler):
            """
            The following instance attributes are inherited from the parent class TemplateHandler.

            Parameters
            ----------
            name: str
                The name of the template. Corresponds to the name of the Stack this template belongs to.
            handler_config: dict
                Configuration of the template handler. All properties except for `type` are available.
            sceptre_user_data: dict
                Sceptre user data defined in the Stack config
            connection_manager: sceptre.connection_manager.ConnectionManager
                Connection manager that can be used to call AWS APIs
            """

            def __init__(self, *args, **kwargs):
                super(CustomTemplateHandler, self).__init__(*args, **kwargs)

            def schema(self):
                """
                Return a JSON schema of the properties that this template handler requires.
                For help filling this, see https://github.com/Julian/jsonschema
                """
                return {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

            def handle(self):
                """
                `handle` should return a CloudFormation template string or bytes. If the return
                value is a byte array, UTF-8 encoding is assumed.

                To use instance attribute self.<attribute_name>. See the class-level docs for a
                list of attributes that are inherited.

                Returns
                -------
                str|bytes
                    CloudFormation template
                """
                return ""


setup.py
^^^^^^^^

.. code-block:: python

   from setuptools import setup

   setup(
       name='<custom_resolver_package_name>',
       py_modules=['<custom_resolver_module_name>'],
       entry_points={
           'sceptre.template_handlers': [
               '<custom_template_handler_type> = <custom_template_handler_module_name>:CustomTemplateHandler',
           ],
       }
   )

Then install using ``python setup.py install`` or ``pip install .`` commands.

This template handler can be used in a Stack config file with the following syntax. Any properties you put in the
``template`` block will be passed to the template handler in the ``self.handler_config`` dictionary.

.. code-block:: yaml

   template:
     type: <custom_template_handler_type>
     <property>: <value>

.. _jsonschema library: https://github.com/Julian/jsonschema
.. _Custom Template Handlers: #custom-template-handlers
.. _Boto3: https://aws.amazon.com/sdk-for-python/
.. _http_template_handler key: stack_group_config.html#http-template-handler

Calling AWS services in your custom template_handler
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For details on calling AWS services or invoking AWS-related third party tools in your
template handler, see :ref:`using_connection_manager`
