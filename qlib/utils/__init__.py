
from __future__ import division
from __future__ import print_function  

import os
import redis
import json
import hashlib
import pandas as pd
from packaging import version
from pathlib import Path

from ..config import C 
from ..log import get_module_logger, set_log_with_config

log = get_module_logger("utils")
# MultiIndex.is_lexsorted() is a deprecated method in Pandas 1.3.0
is_deprecated_lexsorted_pandas = version.parse(pd.__version__) > version.parse("1.3.0")

####################### Server ######################
def get_redis_connection():
    return redis.StrictRedis(host=C.redis_host, port=C.redis_port, db=C.redis_task_db, password=C.redis_password)

def hash_args(*args):
    string = json.dumps(args, sort_keys=True, default=str)
    return hashlib.md5(string.encode()).hexdigest()

def can_use_cache():
    res = True
    r = get_redis_connection()
    try:
        r.client()
    except redis.exceptions.ConnectionError:
        res = False
    finally:
        r.close()
    return res

from .mod import (
    init_instance_by_config,
)

def exists_qlib_data(qlib_dir):
    qlib_dir = Path(qlib_dir).expanduser()
    if not qlib_dir.exists():
        return False

    calendars_dir = qlib_dir.joinpath("calendars")
    instruments_dir = qlib_dir.joinpath("instruments")
    features_dir = qlib_dir.joinpath("features")
    # check dir
    for _dir in [calendars_dir, instruments_dir, features_dir]:
        if not (_dir.exists() and list(_dir.iterdir())):
            return False
    # check calendar bin
    for _calendar in calendars_dir.iterdir():
        if ("_future" not in _calendar.name) and (
            not list(features_dir.rglob(f"*.{_calendar.name.split('.')[0]}.bin"))
        ):
            return False

    # check instruments
    code_names = set(map(lambda x: fname_to_code(x.name.lower()), features_dir.iterdir()))
    _instrument = instruments_dir.joinpath("all.txt")
    miss_code = set(pd.read_csv(_instrument, sep="\t", header=None).loc[:, 0].apply(str.lower)) - set(code_names)
    if miss_code and any(map(lambda x: "sht" not in x, miss_code)):
        return False

    return True


def fname_to_code(fname: str):
    prefix = "_qlib_"
    if fname.startswith(prefix):
        fname = fname.lstrip(prefix)
    return fname

__all__ = [
    "init_instance_by_config",
]
