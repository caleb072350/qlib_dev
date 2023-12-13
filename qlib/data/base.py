
from __future__ import division
from __future__ import print_function

import abc 
import pandas as pd
from ..log import get_module_logger

class Expression(abc.ABC):
    def __str__(self):
        return type(self).__name__
    
    def __repr__(self):
        return str(self)
    
    def __gt__(self, other):
        from .ops import Gt
        return Gt(self, other)
    
    def __ge__(self, other):
        from .ops import Ge  

        return Ge(self, other)

    def __lt__(self, other):
        from .ops import Lt  

        return Lt(self, other)

    def __le__(self, other):
        from .ops import Le  

        return Le(self, other)

    def __eq__(self, other):
        from .ops import Eq 

        return Eq(self, other)
    
    def __ne__(self, other):
        from .ops import Ne

        return Ne(self, other)
    
    def __add__(self, other):
        from .ops import Add

        return Add(self, other)
    
    def __radd__(self, other):
        from .ops import Add  

        return Add(other, self)
    
    def __sub__(self, other):
        from .ops import Sub  

        return Sub(self, other)

    def __rsub__(self, other):
        from .ops import Sub  

        return Sub(other, self)

    def __mul__(self, other):
        from .ops import Mul  

        return Mul(self, other)

    def __rmul__(self, other):
        from .ops import Mul  

        return Mul(self, other)
    
    def __div__(self, other):
        from .ops import Div  

        return Div(self, other)

    def __rdiv__(self, other):
        from .ops import Div  

        return Div(other, self)
    
    def __truediv__(self, other):
        from .ops import Div  

        return Div(self, other)

    def __rtruediv__(self, other):
        from .ops import Div  

        return Div(other, self)
    
    def __pow__(self, other):
        from .ops import Power  

        return Power(self, other)
    
    def __rpow__(self, other):
        from .ops import Power  

        return Power(other, self)
    
    def __and__(self, other):
        from .ops import And  

        return And(self, other)

    def __rand__(self, other):
        from .ops import And  

        return And(other, self)
    
    def __or__(self, other):
        from .ops import Or  

        return Or(self, other)

    def __ror__(self, other):
        from .ops import Or 

        return Or(other, self)
    

class Feature(Expression):
    def __init__(self, name=None):
        if name:
            self._name = name
        else:
            self._name = type(self).__name__

    def __str__(self):
        return "$"+ self._name
    
    def _load_internal(self, instrument, start_index, end_index, freq):
        from .data import FeatureD 
        return FeatureD.feature(instrument, str(self), start_index, end_index, freq)
    
    def get_longest_back_rolling(self):
        return 0
    
    def get_extended_window_size(self):
        return 0
    
class PFeature(Feature):
    def __str__(self):
        return "$$" + self._name
    
    def _load_internal(self, instrument, start_index, end_index, cur_time, period=None):
        from .data import PITD
        return PITD.period_feature(instrument, str(self), start_index, end_index, cur_time, period)
    
class ExpressionOps(Expression):
    """
    """