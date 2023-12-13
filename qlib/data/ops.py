
from __future__ import division
from __future__ import print_function

import numpy as np 
import pandas as pd

from .base import Expression, ExpressionOps, Feature, PFeature

################################## Element-wise Operator ##################################
class ElemOperator(ExpressionOps):
    def __init__(self, feature):
        self.feature = feature
    
    def __str__(self):
        return "{}({})".format(type(self).__name__, self.feature)
    
    def get_longest_back_rolling(self):
        return self.feature.get_longest_back_rolling()
    
    def get_extended_window_size(self):
        return self.feature.get_extended_window_size()
    
class ChangeInstrument(ElemOperator):
    def __init__(self, instrument, feature):
        self.instrument = instrument
        self.feature = feature
    
    