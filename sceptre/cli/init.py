import os
import errno

import click
import yaml

from sceptre.config_reader import ENVIRONMENT_CONFIG_ATTRIBUTES
from sceptre.cli.helpers import catch_exceptions
from sceptre.exceptions import ProjectAlreadyExistsError, TemplateAlreadyExistsError


@click.group(name="init")
def init_group():
    """
    Commands for initialising Sceptre projects.

    """
    pass


@init_group.command("env")
@click.argument('environment')
@catch_exceptions
@click.pass_context
def init_environment(ctx, environment):
    """
    Initialises an environment in a project.

    Creates ENVIRONMENT folder in the project and a config.yaml with any
    required properties.
    """
    cwd = ctx.obj["sceptre_dir"]
    for item in os.listdir(cwd):
        # If already a config folder create a sub environment
        if os.path.isdir(item) and item == "config":
            config_dir = os.path.join(os.getcwd(), "config")
            _create_new_environment(config_dir, environment)


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
    cwd = os.getcwd()
    sceptre_folders = {"config", "templates"}
    project_folder = os.path.join(cwd, project_name)
    try:
        os.mkdir(project_folder)
    except OSError as e:
        # Check if environment folder already exists
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


@init_group.command("template")
@catch_exceptions
@click.argument('template_filename')
@click.option('--env', '-e', multiple=True)
@click.pass_context
def init_template(ctx, template_filename, env):
    """
    Initialises a new template.

    Creates TEMPLATE_FILENAME file in templates/ and optionally
    adds an appropriate config for multiple environments.
    """
    cwd = os.getcwd()

    template_folder = os.path.join(cwd, "templates")
    config_folder = os.path.join(cwd, "config")

    template_path = os.path.join(template_folder, template_filename)
    if os.path.isfile(template_path):
        print('Template \"{0}\" already exists.'.format(template_filename))
    else:
        # create template file
        with open(template_path, 'w') as f:
            print('Created template: \"{0}\"'.format(template_filename))

    # create stack config in each specified environment
    for e in env:
        env_folder = os.path.join(config_folder, e)

        # Check if environment folder does not exist
        if not os.path.isdir(env_folder):
            print('Environment \"{0}\" does not exist.'.format(e))
            continue

        config_filename = os.path.join(env_folder, template_filename)
        with open(config_filename, 'w') as f:
            f.write('template_path: templates/{0}'.format(template_filename))
            print('Created config file in environment \"{0}\" for \"{1}\"'.format(e, template_filename))


def _create_new_environment(config_dir, new_path):
    """
    Creates the subfolder for the environment specified by `path` starting
    from the `config_dir`. Even if folder path already exists, ask the user if
    they want to initialise `config.yaml`.

    :param config_dir: The directory path to the top-level config folder.
    :type config_dir: str
    :param path: The directory path to the environment folder.
    :type path: str
    """
    # Create full path to environment
    folder_path = os.path.join(config_dir, new_path)
    init_config_msg = 'Do you want initialise config.yaml?'

    # Make folders for the environment
    try:
        os.makedirs(folder_path)
    except OSError as e:
        # Check if environment folder already exists
        if e.errno == errno.EEXIST:
            init_config_msg = 'Environment path exists. ' + init_config_msg
        else:
            raise

    if click.confirm(init_config_msg):
        _create_config_file(config_dir, folder_path)


def _get_nested_config(config_dir, path):
    """
    Collects nested config from between `config_dir` and `path`. Config at
    lower level as greater precedence.

    :param config_dir: The directory path to the top-level config folder.
    :type config_dir: str
    :param path: The directory path to the environment folder.
    :type path: str
    :returns: The nested config.
    :rtype: dict
    """
    config = {}
    for root, _, files in os.walk(config_dir):
        # Check that folder is within the final environment path
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
    :param path: The directory path to the environment folder.
    :type path: str
    :param defaults: Defaults to present to the user for config.
    :type defaults: dict
    """
    config = dict.fromkeys(ENVIRONMENT_CONFIG_ATTRIBUTES.required, "")
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
