# -*- coding: utf-8 -*-

"""
sceptre.plan.plan_custom

Custom code that is inherited in SceptrePlan.
"""


class SceptrePlanCustom():

    def stack_name(self, *args):
        """
        Returns the Stack name for a running stack.

        :returns: A list of Stack Names.
        :rtype: List[str]
        """
        self.resolve(command=self.stack_name.__name__)
        return self._execute(*args)

    def detect_stack_drift(self, *args):
        """
        Detects stack drift for a running stack.

        :returns: A list of detected drift against running stacks.
        :rtype: List[str]
        """
        self.resolve(command=self.detect_stack_drift.__name__)
        return self._execute(*args)
