from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd 

class BasePosition:
    """
    The Position wants to maintain the position like a dictionary
    Please refer to the `Position` class for the position
    """

    def __init__(self, *args: Any, cash: float = 0.0, **kwargs: Any) -> None:
        self._settle_type = self.ST_NO
        self.position: dict = {}

    def fill_stock_value(self, start_time: Union[str, pd.Timestamp], freq: str, last_days: int = 30) -> None:
        pass

    def skip_update(self) -> bool:
        """
        Should we skip updating operation for this position
        For example, updating is meaningless for InfPosition

        Returns
        -------
        bool:
            should we skip the updating operator
        """
        return False

    def check_stock(self, stock_id: str) -> bool:
        """
        check if is the stock in the position

        Parameters
        ----------
        stock_id : str
            the id of the stock

        Returns
        -------
        bool:
            if is the stock in the position
        """
        raise NotImplementedError(f"Please implement the `check_stock` method")
    
    # def update_order(self, order: Order, trade_val: float, cost: float, trade_price: float) -> None:
    #     """
    #     Parameters
    #     ----------
    #     order : Order
    #         the order to update the position
    #     trade_val : float
    #         the trade value(money) of dealing results
    #     cost : float
    #         the trade cost of the dealing results
    #     trade_price : float
    #         the trade price of the dealing results
    #     """
    #     raise NotImplementedError(f"Please implement the `update_order` method")