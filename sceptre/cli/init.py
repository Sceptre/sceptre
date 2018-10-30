import os
import errno

import click
import yaml

from sceptre.context import SceptreContext
from sceptre.config.reader import STACK_GROUP_CONFIG_ATTRIBUTES
from sceptre.cli.helpers import catch_exceptions
from sceptre.exceptions import ProjectAlreadyExistsError


@click.group(name="init")
def init_group():
    """
    Commands for initialising Sceptre projects.

    """
    pass


@init_group.command("grp")
@click.argument('stack_group')
@catch_exceptions
@click.pass_context
def init_stack_group(ctx, stack_group):
    """
    Initialises a stack_group in a project.

    Creates STACK_GROUP folder in the project and a config.yaml with any
    required properties.
    """
    context = SceptreContext(project_path=ctx.obj["project_path"])

    for item in os.listdir(context.project_path):
        # If already a config folder create a sub stack_group
        if os.path.isdir(item) and item == context.config_path:
            _create_new_stack_group(context, stack_group)


@init_group.command("project")
@catch_exceptions
@click.argument('project_name')
@click.pass_context
def init_project(ctx, project_name):
    """
    Initialises a new project.

    Creates PROJECT_NAME project folder and a config.yaml with any
    required properties.
    """
    context = SceptreContext(project_path=ctx.obj["project_path"])
    sceptre_folders = {context.config_path, context.templates_path}
    project_folder = os.path.join(context.project_path, project_name)
    try:
        os.mkdir(project_folder)
    except OSError as e:
        # Check if stack_group folder already exists
        if e.errno == errno.EEXIST:
            raise ProjectAlreadyExistsError(
                'Folder \"{0}\" already exists.'.format(project_name)
            )
        else:
            raise

    for folder in sceptre_folders:
        folder_path = os.path.join(project_folder, folder)
        os.makedirs(folder_path)

    defaults = {
        "project_code": project_name,
        "region": os.environ.get("AWS_DEFAULT_REGION", "")
    }

    config_path = os.path.join(context.project_path, project_name,
                               context.config_path)
    _create_config_file(context, config_path, defaults)


def _create_new_stack_group(context, new_path):
    """
    Creates the subfolder for the stack_group specified by `path`
    starting from the `config_dir`. Even if folder path already exists,
    they want to initialise `config.yaml`.

    :param config_dir: The directory path to the top-level config folder.
    :type config_dir: str
    :param path: The directory path to the stack_group folder.
    :type path: str
    """
    # Create full path to stack_group
    full_config_path = os.path.join(context.project_path, context.config_path,
                                    new_path)
    init_config_msg = 'Do you want initialise {}'.format(context.config_file)

    # Make folders for the stack_group
    try:
        os.makedirs(full_config_path)
    except OSError as e:
        # Check if stack_group folder already exists
        if e.errno == errno.EEXIST:
            init_config_msg =\
              'StackGroup path exists. ' + init_config_msg
        else:
            raise

    if click.confirm(init_config_msg):
        _create_config_file(context, full_config_path)


def _get_nested_config(context, path):
    """
    Collects nested config from between `config_dir` and `path`. Config at
    lower level as greater precedence.

    :param config_dir: The directory path to the top-level config folder.
    :type config_dir: str
    :param path: The directory path to the stack_group folder.
    :type path: str
    :returns: The nested config.
    :rtype: dict
    """
    full_config_path = os.path.join(context.project_path, context.config_path)
    config = {}
    for root, _, files in os.walk(full_config_path):
        # Check that folder is within the final stack_group path
        if path.startswith(root) and context.config_file in files:
            config_path = os.path.join(root, context.config_file)
            with open(config_path) as config_file:
                config.update(yaml.safe_load(config_file))
    return config


def _create_config_file(context, path, defaults={}):
    """
    Creates a `config.yaml` file in the given path. The user is asked for
    values for requried properties. Defaults are suggested with values in
    `defaults` and then vaules found in parent `config.yaml` files. If
    properties and their values are the same as in parent `config.yaml`, then
    they are not included. No file is produced if require values are satisfied
    by parent `config.yaml` files.

    :param config_dir: The directory path to the top-level config folder.
    :type config_dir: str
    :param path: The directory path to the stack_group folder.
    :type path: str
    :param defaults: Defaults to present to the user for config.
    :type defaults: dict
    """
    config = dict.fromkeys(STACK_GROUP_CONFIG_ATTRIBUTES.required, "")
    parent_config = _get_nested_config(context, path)

    # Add standard defaults
    config.update(defaults)

    # Add parent config values as defaults
    config.update(parent_config)

    # Ask for new values
    for key, value in config.items():
        config[key] = click.prompt(
            'Please enter a {0}'.format(key), default=value
        )

    # Remove values if parent config are the same
    config = {k: v for k, v in config.items() if parent_config.get(k) != v}

    # Write config.yaml if config not empty
    filepath = os.path.join(path, context.config_file)
    if config:
        with open(filepath, 'w') as config_file:
            yaml.safe_dump(
                config, stream=config_file, default_flow_style=False
            )
    else:
        click.echo("No {} file needed - covered by parent config.".format(
            context.config_file))
