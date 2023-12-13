from __future__ import division
from __future__ import print_function

import re
import abc
import copy
import queue
import bisect
import numpy as np
import pandas as pd
from typing import List, Union, Optional

from .cache import H

# For supporting multiprocessing in outer code, joblib is used
from joblib import delayed

from ..config import C

from ..utils import init_instance_by_config

class ProviderBackendMixin:
    def get_default_backend(self):
        backend = {}
        provider_name: str = re.findall("[A-Z][^A-Z]*", self.__class__.__name__)[-2]
        backend.setdefault("class", f"File{provider_name}Storage")
        backend.setdefault("module_path", "qlib.data.storage.file_storage")
        return backend
    
    def backend_obj(self, **kwargs):
        backend = self.backend if self.backend else self.get_default_backend()
        backend = copy.deepcopy(backend)
        backend.setdefault("kwargs", {}).update(**kwargs)
        return init_instance_by_config(backend)
    
class CalendarProvider(abc.ABC):
    def calendar(self, start_time=None, end_time=None, freq="day", future=False):
        _calendar, _calendar_index = self._get_calendar(freq, future)
        if start_time == "None":
            start_time = None
        if end_time == "None":
            end_time = None
        if start_time:
            start_time = pd.Timestamp(start_time)
            if start_time > _calendar[-1]:
                return np.array([])
        else:
            start_time = _calendar[0]
        if end_time:
            end_time = pd.Timestamp(end_time)
            if end_time < _calendar[0]:
                return np.array([])
        else:
            end_time = _calendar[-1]
        
        _,_,si,ei = self.locate_index(start_time, end_time, freq, future)
        return _calendar[si:ei+1]
    
    def locate_index(self, start_time: Union[pd.Timestamp, str], end_time: Union[pd.Timestamp, str], freq: str, future: bool=False):
        start_time = pd.Timestamp(start_time)
        end_time = pd.Timestamp(end_time)
        calendar, calendar_index = self._get_calendar(freq, future)
        if start_time not in calendar_index:
            try:
                start_time = calendar[bisect.bisect_left(calendar, start_time)]
            except IndexError as index_e:
                raise IndexError(
                    "`start_time` uses a future date, if you want to get future trading days, you can use: `future=True`"
                ) from index_e
        start_index = calendar_index[start_time]
        if end_time not in calendar_index:
            end_time = calendar[bisect.bisect_right(calendar, end_time) - 1]
        end_index = calendar_index[end_time]
        return start_time, end_time, start_index, end_index

    def _get_calendar(self, freq, future):
        flag = f"{freq}_future_{future}"
        if flag not in H["c"]:
            _calendar = np.array(self.load_calendar(freq, future))
            _calendar_index = {x: i for i, x in enumerate(_calendar)}
            H["c"][flag] = _calendar, _calendar_index
        return H["c"][flag]
    
    def load_calendar(self, freq, future):
        raise NotImplementedError("Subclass of CalendarProvider must implement load_calendar method")

class InstrumentProvider(abc.ABC):
    @staticmethod
    def instruments(market: Union[List, str] = "all", filter_pipe: Union[List, None] = None):
        if isinstance(market, list):
            return market
        from .filter import SeriesDFilter
        