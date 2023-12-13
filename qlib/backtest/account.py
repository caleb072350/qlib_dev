from __future__ import annotations 

import copy 
from typing import Dict, List, Optional, Tuple, cast 

import pandas as pd 

from qlib.utils import init_instance_by_config

"""
rtn & earning in the Account
    rtn: 
        from order's view
        1. change if any order is executed, sell order or buy order 
        2. change at the end of today, (today_close - stock_price) * amount
    earning:
        from value of current position
        earning will be updated at the end of trade date
        earning = today_value - pre_value
    **is consider cost**
       while earning is the difference of two position value, so it considers cost, it is the true return rate
       in the specific accomplishment for rtn, it does not consider cost, in other words, rtn - cost = earning
"""

class AccumulatedInfo:
    """
    accumulated trading info, including accumulated return/cost/turnover
    AccumulatedInfo should be shared across difference levels
    """

    def __init__(self) -> None:
        self.reset()
    
    def reset(self) -> None:
        self.rtn: float = 0.0 # accumulated return, do not consider cost
        self.cost: float = 0.0 # accumulated cost
        self.to: float = 0.0 # accumulated turnover
    
    def add_return_value(self, value: float) -> None:
        self.rtn += value
    
    def add_cost(self, value: float) -> None:
        self.cost += value
    
    def add_turnover(self, value: float) -> None:
        self.to += value
    
    @property
    def get_cost(self) -> float:
        return self.cost
    
    @property
    def get_turnover(self) -> float:
        return self.to
    
class Account:
    """
    The correctness of the metrics of Account in nested execution depends on the shallow copy of `trade_account` in
    qlib/backtest/executor.py:NestdExecutor
    Different level of executor has different Account object when calculating metrics. But the position object is 
    shared cross all the Account object.
    """

    def __init__(self, init_cash: float = 1e9, position_dict: dict = {}, freq: str = "day", benchmark_config: dict = {}, pos_type: str = "Position",
                 port_metr_enabled: bool = True) -> None:
        """
        the trade account of backtest.
        
        Parameters
        ----------
        init_cash : float, optional
            initial cash, by default 1e9
        position_dict : Dict[
                             stock_id,
                             Union[
                                int, # it is equal to {"amount": int}
                                {"amount": int, "price"(optional): float},
                             ]
                        ]
            initial stocks with parameters amount and price,
            if there is no price key in the dict of stocks, it will be filled by _fill_stock_value.
            by default {}
        """
        self._pos_type = pos_type
        self._port_metr_enabled = port_metr_enabled
        self.benchmark_config: dict = {} # avoid no attribute error
        self.init_vars(init_cash, position_dict, freq, benchmark_config)

    def init_vars(self, init_cash: float, position_dict: dict, freq: str, benchmark_config: dict) -> None:
        # 1) the following variables are shared by multiple layers
        # - you will see a shallow copy instead of deepcopy in the NestedExecutor
        self._init_cash = init_cash
        # self.current_position: BasePosition = init_instance_by_config(
        #     {
        #         "class": self._pos_type,
        #         "kwargs": {
        #             "cash": init_cash,
        #             "position": position_dict,
        #         },
        #         "module_path": "qlib.backtest.position",
        #     },
        # )
