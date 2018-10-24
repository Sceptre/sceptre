from enum import Enum
from sceptre.stack import Stack
from sceptre.stack_group import StackGroup
from sceptre.template import Template


class PlanType(Enum):
    STACK_GROUP = StackGroup
    STACK = Stack
    TEMPLATE = Template
