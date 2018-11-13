from os import path


class SceptreContext(object):

    def __init__(self, project_path, command_path,
                 user_variables=None, options=None, output_format=None,
                 no_colour=False):
        # project_path: absolute path to the base sceptre project folder
        # e.g. absolute_path/to/sceptre_directory
        self.project_path = project_path

        # config_path: holds the project stack_groups
        # e.g {project_path}/config
        self.config_path = "config"  # user definable later in v2

        # command_path path to either stack group or stack
        # e.g. {project_path/config_path}/command_path
        self.command_path = command_path

        # config_file: stack group config. User definable later in v2
        # e.g. {project_path/config/command_path}/config_file
        self.config_file = "config.yaml"

        # templates_path: holds tempaltes. User definable later in v2
        # e.g. {project_path/}templates
        self.templates_path = "templates"

        self.user_variables = user_variables if user_variables else {}
        self.user_variables = user_variables\
            if user_variables is not None else {}
        self.options = options if options else {}
        self.output_format = output_format if output_format else ""
        self.no_colour = no_colour if no_colour is True else False

    def full_config_path(self):
        """
        Returns a path in the format: project_path/config_path
        """
        return path.join(self.project_path, self.config_path)

    def full_command_path(self):
        """
        Returns a path in the format: project_path/config_path/command_path
        """
        return path.join(self.project_path, self.config_path,
                         self.command_path)

    def full_templates_path(self):
        """
        Returns a path in the format: project_path/templates_path
        """
        return path.join(self.project_path, self.templates_path)

    def command_path_is_stack(self):
        return path.isfile(
                    path.join(
                        self.project_path,
                        self.config_path,
                        self.command_path
                    )
                )
