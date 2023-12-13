"""
All module related class, e.g. :
- importing a module, class
- walkiing a module
- operations on class or module...
"""
import os
import pickle
import re
import importlib
import sys
from typing import Any, Dict, List, Tuple, Union
from pathlib import Path
from types import ModuleType
from urllib.parse import urlparse 
from qlib.typehint import InstConf

def get_module_by_module_path(module_path: Union[str, ModuleType]):
    """
    Load module path
    :param module_path:
    :return:
    :raises: ModuleNotFoundError
    """
    if module_path is None:
        raise ModuleNotFoundError("None is passed as parameters as module_path")
    if isinstance(module_path, ModuleType):
        module = module_path
    else:
        if module_path.endswith(".py"):
            module_name = re.sub("^[^a-zA-Z_]+", "", re.sub("[^0-9a-zA-Z_]", "", module_path[:-3].replace("/", "_")))
            module_spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(module_spec)
            sys.modules[module_name] = module
            module_spec.loader.exec_module(module)
        else:
            module = importlib.import_module(module_path)
    return module

def split_module_path(module_path: str) -> Tuple[str, str]:
    *m_path, cls = module_path.split(".")
    m_path = ".".join(m_path)
    return m_path, cls

def get_callable_kwargs(config: InstConf, default_module: Union[str, ModuleType] = None) -> (type, dict):
    if isinstance(config, dict):
        key = "class" if "class" in config else "func"
        if isinstance(config[key], str):
            m_path, cls = split_module_path(config[key])
            if m_path == "":
                m_path = config.get("module_path", default_module)
            module = get_module_by_module_path(m_path)

def init_instance_by_config(config: InstConf, default_module=None, accept_types: Union[type, Tuple[type]] = (),
        try_kwargs: Dict = {}, **kwargs) -> Any:
    if isinstance(config, accept_types):
        return config
    
    if isinstance(config, (str, Path)):
        if isinstance(config, str):
            # path like 'file:///<path to pickle file>/obj.pkl'
            pr = urlparse(config)
            if pr.scheme == "file":
                pr_path = os.path.join(pr.netloc, pr.path) if bool(pr.path) else pr.netloc
                with open(os.path.normpath(pr_path), "rb") as f:
                    return pickle.load(f)
        else:
            with config.open("rb") as f:
                return pickle.load(f)
    
    klass, cls_kwargs = get_callable_kwargs(config, default_module=default_module)

    try:
        return klass(**cls_kwargs, **try_kwargs, **kwargs)
    except (TypeError,):
        # TypeError for handling errors like
        # 1: `XXX() got multiple values for keyword argument 'YYY'`
        # 2: `XXX() got an unexpected keyword argument 'YYY'
        return klass(**cls_kwargs, **kwargs)

