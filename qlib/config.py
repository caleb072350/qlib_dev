from __future__ import annotations

import os
import copy
import multiprocessing
import logging
import re
import platform

from pathlib import Path
from typing import Callable, Optional, Union 
from typing import TYPE_CHECKING

from qlib.constant import REG_CN, REG_US, REG_TW

if TYPE_CHECKING:
    from qlib.utils.time import Freq

class Config:
    def __init__(self, default_conf):
        self.__dict__["_default_config"] = copy.deepcopy(default_conf)
        self.reset()

    def __setitem__(self, key, value):
        self.__dict__["_config"][key] = value
    
    def __getitem__(self, key):
        return self.__dict__["_config"][key]
    
    def __setattr__(self, attr, value):
        self.__dict__["_config"][attr] = value
    
    def __getattr__(self, attr):
        if attr == "_default_conf":
            return self.__dict__["_default_config"]
    
        if attr in self.__dict__["_config"]:
            return self.__dict__["_config"][attr]
        
        raise AttributeError(f"No such attribute `{attr}` in self._config or as an internal attribute")
        
    
    def __contains__(self, item):
        return item in self.__dict__["_config"]
    
    # pickle序列化的时候自动调用
    def __getstate__(self):
        return self.__dict__
    
    # 反序列化的时候自动调用
    def __setstate__(self, state) -> None:
        self.__dict__.update(state)

    def __str__(self):
        return str(self.__dict__["_config"])
    
    def __repr__(self):
        return str(self.__dict__["_config"])
    
    def get(self, key, default=None):
        return self.__dict__["_config"].get(key, default)
    
    def reset(self):
        self.__dict__["_config"] = copy.deepcopy(self._default_config)
    
    def update(self, *args, **kwargs):
        self.__dict__["_config"].update(*args, **kwargs)

    def set_conf_from_C(self, config_c):
        self.update(**config_c.__dict__["_config"])

    @staticmethod
    def register_from_C(config, skip_register=True):
        from .utils import set_log_with_config

        if C.registered and skip_register:
            return
        
        C.set_conf_from_C(config)
        if C.logging_config:
            set_log_with_config(C.logging_config)
        C.register()

PROTOCOL_VERSION = 4

NUM_USABLE_CPU = max(multiprocessing.cpu_count() - 2, 1)

DISK_DATASET_CACHE = "DiskDatasetCache"
SIMPLE_DATASET_CACHE = "SimpleDatasetCache"
DISK_EXPRESSION_CACHE = "DiskExpressionCache"

DEPENDENCY_REDIS_CACHE = (DISK_DATASET_CACHE, DISK_EXPRESSION_CACHE)

_default_config = {
    "calendar_provider": "LocalCalendarProvider",
    "instrument_provider": "LocalInstrumentProvider",
    "feature_provider": "LocalFeatureProvider",
    "pit_provider": "LocalPITProvider",
    "expression_provider": "LocalExpressionProvider",
    "dataset_provider": "LocalDatasetProvider",
    "provider": "LocalProvider",
    "provider_uri": "",
    "expression_cache": None,
    "calendar_cache": None,
    "local_cache_path": None,
    "kernels": NUM_USABLE_CPU,
    "dump_protocol_version": PROTOCOL_VERSION,
    "maxtasksperchild": None,
    "joblib_backend": "multiprocessing",
    "default_disk_cache": 1,  # 0:skip/1:use
    "mem_cache_size_limit": 500,
    "mem_cache_limit_type": "length",
    "mem_cache_expire": 60 * 60,
    "dataset_cache_dir_name": "dataset_cache",
    "features_cache_dir_name": "features_cache",
    "redis_host": "127.0.0.1",
    "redis_port": 6379,
    "redis_task_db": 1,
    "redis_password": "072350",
    "logging_level": logging.INFO,
    "log_level": logging.INFO,
    "logging_config": {
        "version": 1,
        "formatters": {
            "logger_format": {
                "format": "[%(process)s:%(threadName)s](%(asctime)s) %(levelname)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s"
            }
        },
        "filters": {
            "field_not_found": {
                "()": "qlib.log.LogFilter",
                "param": [".*?WARN: data not found for.*?"],
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": logging.DEBUG,
                "formatter": "logger_format",
                "filters": ["field_not_found"],
            }
        },
        "loggers": {"qlib": {"level": logging.DEBUG, "handlers": ["console"]}},
        "disable_existing_loggers": False,
    },
    "exp_manager": {
        "class": "MLflowExpManager",
        "module_path": "qlib.workflow.expm",
        "kwargs": {
            "uri": "file:" + str(Path(os.getcwd()).resolve() / "mlruns"),
            "default_exp_name": "Experiment",
        },
    },
    "pit_record_type": {
        "date": "I",  # uint32
        "period": "I",  # uint32
        "value": "d",  # float64
        "index": "I",  # uint32
    },
    "pit_record_nan": {
        "date": 0,
        "period": 0,
        "value": float("NAN"),
        "index": 0xFFFFFFFF,
    },
    "mongo": {
        "task_url": "mongodb://localhost:27017/",
        "task_db_name": "default_task_db",
    },
    "min_data_shift": 0,
}

MODE_CONF = {
    "server": {
        "provider_uri": "",
        "redis_host": "127.0.0.1",
        "redis_port": 6379,
        "redis_task_db": 1,
        "expression_cache": DISK_EXPRESSION_CACHE,
        "dataset_cache": DISK_DATASET_CACHE,
        "local_cache_path": Path("~/.cache/qlib_simple_cache").expanduser().resolve(),
        "mount_path": None,
    },
    "client": {
        "provider_uri": "~/.qlib/qlib_data/cn_data",
        "dataset_cache": None,
        "local_cache_path": Path("~/.cache/qlib_simple_cache").expanduser().resolve(),
        "mount_path": None,
        "auto_mount": False,
        "timeout": 100,
        "logging_level": logging.INFO,
        "region": REG_CN,
        "custom_ops": [],
    },
}

HIGH_FREQ_CONFIG = {
    "provider_uri": "~/.qlib/qlib_data/cn_data_1min",
    "dataset_cache": None,
    "expression_cache": "DiskExpressionCache",
    "region": REG_CN,
}

_default_region_config = {
    REG_CN: {
        "trade_unit": 100,
        "limit_threshold": 0.095,
        "deal_price": "close",
    },
    REG_US: {
        "trade_unit": 1,
        "limit_threshold": None,
        "deal_price": "close",
    },
    REG_TW: {
        "trade_unit": 1000,
        "limit_threshold": 0.1,
        "deal_price": "close",
    },
}

class QlibConfig(Config):
    LOCAL_URI = "local"
    NFS_URI = "nfs"
    DEFAULT_FREQ = "__DEFAULT_FREQ"

    def __init__(self, default_conf):
        super().__init__(default_conf)
        self._registered = False 
    
    class DataPathManager:
        """
        Motivation:
        - get the right path (e.g. data uri) for accessing data based on given information(e.g. provider_uri, mount_path and frequency)
        - some helper functions to process uri.
        """

        def __init__(self, provider_uri: Union[str, Path, dict], mount_path: Union[str, Path, dict]):
            """
            The relation of `provider_uri` and `mount_path`
            - `mount_path` is used only if provider_uri is an NFS path
            - otherwise, provider_uri will be used for accessing data"""
            self.provider_uri = provider_uri
            self.mount_path = mount_path
        
        @staticmethod
        def format_provider_uri(provider_uri: Union[str, dict, Path]) -> dict:
            if provider_uri is None:
                raise ValueError("provider_uri is None")
            if isinstance(provider_uri, (str, dict, Path)):
                if not isinstance(provider_uri, dict):
                    provider_uri = {QlibConfig.DEFAULT_FREQ: provider_uri}
            else:
                raise TypeError(f"provider_uri does not support {type(provider_uri)}")
            for freq, _uri in provider_uri.items():
                if QlibConfig.DataPathManager.get_uri_type(_uri) == QlibConfig.LOCAL_URI:
                    provider_uri[freq] = str(Path(_uri).expanduser().resolve())
            return provider_uri
        
        @staticmethod
        def get_uri_type(uri: Union[str, Path]):
            uri = uri if isinstance(uri, str) else str(uri.expanduser().resolve())
            is_win = re.match("^[a-zA-Z]:.*", uri) is not None # such as 'C:\\data', 'D:/data'
            # such as 'host:/data/' (Users may define short hostname by themselves or use localhost)
            is_nfs_or_win = re.match("^[^/]+:.+", uri) is not None 
            if is_nfs_or_win and not is_win:
                return QlibConfig.NFS_URI
            else:
                return QlibConfig.LOCAL_URI
        
        def get_data_uri(self, freq: Optional[Union[str, Freq]] = None) -> Path:
            """
            please refer DataPathManager's __init__ and class doc
            """
            if freq is not None:
                freq = str(freq) # converting Freq to string
            if freq is None or freq not in self.provider_uri:
                freq = QlibConfig.DEFAULT_FREQ 
            _provider_uri = self.provider_uri[freq]
            if self.get_uri_type(_provider_uri) == QlibConfig.LOCAL_URI:
                return Path(_provider_uri)
            elif self.get_uri_type(_provider_uri) == QlibConfig.NFS_URI:
                if "win" in platform.system().lower():
                    # windows, mount_path is the drive
                    _path = str(self.mount_path[freq])
                    return Path(f"{_path}:\\") if ":" not in _path else Path(_path)
                return Path(self.mount_path[freq])
            else:
                raise NotImplementedError(f"This type of uri is not supported")        

    def set_mode(self, mode):
        self.update(MODE_CONF[mode])

    def set_region(self, region):
        self.update(_default_region_config[region])
    
    @staticmethod
    def is_depend_redis(cache_name: str):
        return cache_name in DEPENDENCY_REDIS_CACHE
    
    @property
    def dpm(self):
        return self.DataPathManager(self["provider_uri"], self["mount_path"])
    
    def resolve_path(self):
        _mount_path = self["mount_path"]
        _provider_uri = self.DataPathManager.format_provider_uri(self["provider_uri"])
        if not isinstance(_mount_path, dict):
            _mount_path = {_freq: _mount_path for _freq in _provider_uri.keys()}
        
        _miss_freq = set(_provider_uri.keys()) - set(_mount_path.keys())
        assert len(_miss_freq) == 0, f"mount_path does not contain {_miss_freq}"

        for _freq in _provider_uri.keys():
            _mount_path[_freq] = (
                _mount_path[_freq] if _mount_path[_freq] is None else str(Path(_mount_path[_freq]).expanduser())
            )
        self["provider_uri"] = _provider_uri
        self["mount_path"] = _mount_path
    
    def set(self, default_conf: str = "client", **kwargs):
        from .utils import set_log_with_config, get_module_logger, can_use_cache

        print("test")
        self.reset()

        _logging_config = kwargs.get("logging_config", self.logging_config)

        if _logging_config:
            set_log_with_config(_logging_config)
        
        logger = get_module_logger("Initialization", kwargs.get("logging_level", self.logging_level))
        logger.info(f"default_conf: {default_conf}")

        self.set_mode(default_conf)
        self.set_region(kwargs.get("region", self["region"] if "region" in self else REG_CN))

        for k,v in kwargs.items():
            if k not in self:
                logger.warning("Unrecognized config %s" % k)
            self[k] = v 

        self.resolve_path()

        if not (self["expression_cache"] is None and self["dataset_cache"] is None):
            if not can_use_cache():
                log_str = ""
                if self.is_depend_redis(self["expression_cache"]):
                    log_str += self["expression_cache"] 
                    self["expression_cache"] = None
                if self.is_depend_redis(self["dataset_cache"]):
                    log_str += f" and {self['dataset_cache']}" if log_str else self["dataset_cache"]
                    self["dataset_cache"] = None
                if log_str:
                    logger.warning(
                        f"redis connection failed(host={self['redis_host']}, port={self['redis_port']}), "
                        f"{log_str} will not be used!"
                    )
    def register(self):
        from .utils import init_instance_by_conifg

        #register_all_ops(self)
        #register_all_wrappers(self)
        self._registered = True
    
    @property
    def registered(self):
        return self._registered
    
C = QlibConfig(_default_config)