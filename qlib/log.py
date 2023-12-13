import logging
import re
from logging import config as logging_config
from typing import Optional, Text, Dict, Any
from time import time
from contextlib import contextmanager

from .config import C

class MetaLogger(type):
    def __new__(mcs, name, bases, attrs):
        wrapper_dict = logging.Logger.__dict__.copy()
        for key, value in wrapper_dict.items():
            if key not in attrs and key != "__reduce__":
                attrs[key] = value
        return type.__new__(mcs, name, bases, attrs)
    
class QlibLogger(metaclass=MetaLogger):
    def __init__(self, module_name):
        self.module_name = module_name
        self.__level = 0
    
    @property
    def logger(self):
        logger = logging.getLogger(self.module_name)
        logger.setLevel(self.__level)
        return logger
    
    def setLevel(self, level):
        self.__level = level

    def __getattr__(self, name):
        if name in {"__setstate__"}:
            raise AttributeError
        return self.logger.__getattribute__(name)
    
class _QLibLoggerManager:
    def __init__(self):
        self._loggers = {}

    def setLevel(self, level):
        for logger in self._loggers.values():
            logger.setLevel(level)
    
    def __call__(self, module_name, level: Optional[int] = None) -> QlibLogger:
        if level is None:
            level = C.log_level
        if not module_name.startswith("qlib."):
            module_name = "qlib.{}".format(module_name)
        
        module_logger = self._loggers.setdefault(module_name, QlibLogger(module_name))
        module_logger.setLevel(level)
        return module_logger

get_module_logger = _QLibLoggerManager()

def set_log_with_config(log_config: Dict[Text, Any]):
    logging_config.dictConfig(log_config)

class LogFilter(logging.Filter):
    def __init__(self, param=None):
        super().__init__()
        self.param = param

    @staticmethod
    def match_msg(filter_str, msg):
        match = False
        try:
            if re.match(filter_str, msg):
                match = True
        except Exception:
            pass
        return match

    def filter(self, record):
        allow = True
        if isinstance(self.param, str):
            allow = not self.match_msg(self.param, record.msg)
        elif isinstance(self.param, list):
            allow = not any(self.match_msg(p, record.msg) for p in self.param)
        return allow
    
def set_global_logger_level(level: int, return_orig_handler_level: bool = False):
    """set qlib.xxx logger handlers level

    Parameters
    ----------
    level: int
        logger level

    return_orig_handler_level: bool
        return origin handler level map

    Examples
    ---------

        .. code-block:: python

            import qlib
            import logging
            from qlib.log import get_module_logger, set_global_logger_level
            qlib.init()

            tmp_logger_01 = get_module_logger("tmp_logger_01", level=logging.INFO)
            tmp_logger_01.info("1. tmp_logger_01 info show")

            global_level = logging.WARNING + 1
            set_global_logger_level(global_level)
            tmp_logger_02 = get_module_logger("tmp_logger_02", level=logging.INFO)
            tmp_logger_02.log(msg="2. tmp_logger_02 log show", level=global_level)

            tmp_logger_01.info("3. tmp_logger_01 info do not show")

    """
    _handler_level_map = {}
    qlib_logger = logging.root.manager.loggerDict.get("qlib", None)  # pylint: disable=E1101
    if qlib_logger is not None:
        for _handler in qlib_logger.handlers:
            _handler_level_map[_handler] = _handler.level
            _handler.level = level
    return _handler_level_map if return_orig_handler_level else None

@contextmanager
def set_global_logger_level_cm(level: int):
    """set qlib.xxx logger handlers level to use contextmanager

    Parameters
    ----------
    level: int
        logger level

    Examples
    ---------

        .. code-block:: python

            import qlib
            import logging
            from qlib.log import get_module_logger, set_global_logger_level_cm
            qlib.init()

            tmp_logger_01 = get_module_logger("tmp_logger_01", level=logging.INFO)
            tmp_logger_01.info("1. tmp_logger_01 info show")

            global_level = logging.WARNING + 1
            with set_global_logger_level_cm(global_level):
                tmp_logger_02 = get_module_logger("tmp_logger_02", level=logging.INFO)
                tmp_logger_02.log(msg="2. tmp_logger_02 log show", level=global_level)
                tmp_logger_01.info("3. tmp_logger_01 info do not show")

            tmp_logger_01.info("4. tmp_logger_01 info show")

    """
    _handler_level_map = set_global_logger_level(level, return_orig_handler_level=True)
    try:
        yield
    finally:
        for _handler, _level in _handler_level_map.items():
            _handler.level = _level