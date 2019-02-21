import os
import errno

import click
import yaml

from sceptre.config.reader import STACK_GROUP_CONFIG_ATTRIBUTES
from sceptre.cli.helpers import catch_exceptions
from sceptre.exceptions import ProjectAlreadyExistsError


@click.group(name="new")
def new_group():
    """
    Commands for initialising Sceptre projects.

    """
    pass


@new_group.command("group", short_help="Creates a new Stack Group directory in a project.")
@click.argument('stack_group')
@catch_exceptions
@click.pass_context
def new_stack_group(ctx, stack_group):
    """
    Creates StackGroup folder in the project and a config.yaml with any
    required properties.
    \f

    :param stack_group: Name of the StackGroup directory to create.
    :type stack_group: str
    """
    cwd = ctx.obj.get("project_path")
    for item in os.listdir(cwd):
        # If already a config folder create a sub stack_group
        if os.path.isdir(item) and item == "config":
            config_dir = os.path.join(os.getcwd(), "config")
            _create_new_stack_group(config_dir, stack_group)


@new_group.command("project", short_help="Creates a new project.")
@catch_exceptions
@click.argument('project_name')
@click.pass_context
def new_project(ctx, project_name):
    """
    Creates PROJECT_NAME project folder and a config.yaml with any
    required properties.
    \f

    :param project_name: The name of the Sceptre Project to create.
    :type project_name: str
    """
    cwd = os.getcwd()
    sceptre_folders = {"config", "templates"}
    project_folder = os.path.join(cwd, project_name)
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

    config_path = os.path.join(cwd, project_name, "config")
    _create_config_file(config_path, config_path, defaults)


def _create_new_stack_group(config_dir, new_path):
    """
    Creates the subfolder for the stack_group specified by `new_path`
    starting from the `config_dir`. Even if folder path already exists,
    they want to initialise `config.yaml`.

    :param config_dir: The directory path to the top-level config folder.
    :type config_dir: str
    :param new_path: The directory path to the stack_group folder.
    :type new_path: str
    """
    # Create full path to stack_group
    folder_path = os.path.join(config_dir, new_path)
    new_config_msg = 'Do you want initialise config.yaml?'

    # Make folders for the stack_group
    try:
        os.makedirs(folder_path)
    except OSError as e:
        # Check if stack_group folder already exists
        if e.errno == errno.EEXIST:
            new_config_msg =\
                'StackGroup path exists. ' + new_config_msg
        else:
            raise

    if click.confirm(new_config_msg):
        _create_config_file(config_dir, folder_path)


def _get_nested_config(config_dir, path):
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
    config = {}
    for root, _, files in os.walk(config_dir, followlinks=True):
        # Check that folder is within the final stack_group path
        if path.startswith(root) and "config.yaml" in files:
            config_path = os.path.join(root, "config.yaml")
            with open(config_path) as config_file:
                config.update(yaml.safe_load(config_file))
    return config


def _create_config_file(config_dir, path, defaults={}):
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
    parent_config = _get_nested_config(config_dir, path)

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
    filepath = os.path.join(path, "config.yaml")
    if config:
        with open(filepath, 'w') as config_file:
            yaml.safe_dump(
                config, stream=config_file, default_flow_style=False
            )
    else:
        click.echo("No config.yaml file needed - covered by parent config.")
