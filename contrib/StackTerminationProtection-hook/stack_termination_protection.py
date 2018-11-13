from sceptre.hooks import Hook


class StackTerminationProtection(Hook):

    ALLOWED_ARG_VALUES = ['enabled', 'disabled']

    def __init__(self, *args, **kwargs):
        super(StackTerminationProtection, self).__init__(*args, **kwargs)

    def run(self):
        argument = (self.argument if self.argument else '').lower()

        assert argument in self.ALLOWED_ARG_VALUES, \
            "As the argument for !stack_termination_protection, " \
            "please choose one of {0}".format(self.ALLOWED_ARG_VALUES)

        cf_stack_name = self.stack_config["stack_name"]

        enable = argument == 'enabled'

        self.logger.info(
            "Setting termination protection of stack '%s' to '%s'",
            cf_stack_name, argument)

        self.connection_manager.call('cloudformation',
                                     'update_termination_protection',
                                     kwargs={
                                         'StackName': cf_stack_name,
                                         'EnableTerminationProtection': enable
                                         }
                                     )
