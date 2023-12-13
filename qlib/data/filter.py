from __future__ import print_function
from abc import abstractmethod
import abc
import pandas as pd

class BaseDFilter(abc.ABC):
    def __init__(self):
        pass

    @staticmethod
    def from_config(config):
        raise NotImplementedError("Subclass of BaseDFilter must implement `from_config` method")
    
    @abstractmethod
    def to_config(self):
        raise NotImplementedError("Subclass of BaseDFilter must implement `to_config` method")
    
class SeriesDFilter(BaseDFilter):
    def __init__(self, fstart_time=None, fend_time=None, keep=False):
        super(SeriesDFilter, self).__init__()
        self.filter_start_time = pd.Timestamp(fstart_time) if fstart_time else None
        self.filter_end_time = pd.Timestamp(fend_time) if fend_time else None
        self.keep = keep 
    
    

    