from logging import LoggerAdapter, Logger
from typing import MutableMapping, Any, Tuple


class StackLoggerAdapter(LoggerAdapter):
    def __init__(self, logger: Logger, stack_name: str, extra: dict = None):
        """A small wrapper around a Logger that prefixes log messages with the stack name.

        :param logger: The logger to wrap
        :param stack_name: The name of the stack to every log message
        :param extra: Extra kwargs to add to the log context (if any)
        """
        super().__init__(logger, extra or {})
        self.stack_name = stack_name

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> Tuple[Any, MutableMapping[str, Any]]:
        msg = f"{self.stack_name} - {msg}"
        return super().process(msg, kwargs)
