from logging import LoggerAdapter, Logger
from typing import MutableMapping, Any, Tuple


class StackLoggerAdapter(LoggerAdapter):
    def __init__(self, logger: Logger, stack_name: str, extra: dict = None):
        super().__init__(logger, extra or {})
        self.stack_name = stack_name

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> Tuple[Any, MutableMapping[str, Any]]:
        msg = f"{self.stack_name} - {msg}"
        return super().process(msg, kwargs)
