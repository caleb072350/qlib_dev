from __future__ import annotations
from typing import Union, Any, Set
import pandas as pd
import warnings
from abc import abstractmethod

class TradeCalendarManager:
    """
    Manager for trading calendar
        - BaseStrategy and BaseExecutor will use it
    """

    def __init__(self, freq: str, start_time: Union[str, pd.Timestamp] = None, end_time: Union[str, pd.Timestamp] = None,
                 level_infra: LevelInfrastructure | None = None) -> None:
        """
        Parameters
        ----------
        freq : str
            frequency of trading calendar, also trade time per trading step
        start_time : Union[str, pd.Timestamp]
            closed start time of trading calendar, by default None
            If `start_time` is None, it must be reset before trading
        end_time : Union[str, pd.Timestamp]
            closed end time of trading calendar, by default None
            If `end_time` is None, it must be reset before trading
        """
        self.level_infra = level_infra
        self.reset(freq=freq, start_time=start_time, end_time=end_time)
    
    def reset(self, freq: str, start_time: Union[str, pd.Timestamp] = None, end_time: Union[str, pd.Timestamp] = None) -> None:
        """
        Please refer to the docs of `__init__`

        Reset the trade calendar
        - self.trade_len : The total count for trading step
        - self.trade_step : The number of trading step finished, self.trade_step can be
            [0, 1, 2, ..., self.trade_len - 1]
        """
        self.freq = freq
        self.start_time = pd.Timestamp(start_time) if start_time else None
        self.end_time = pd.Timestamp(end_time) if end_time else None
        
        

class BaseInfrastructure:
    def __init__(self, **kwargs: Any) -> None:
        self.reset_infra(**kwargs)
    
    @abstractmethod
    def get_support_infra(self) -> Set[str]:
        raise NotImplementedError("`get_support_infra` is not implemented!")

    def reset_infra(self, **kwargs: Any) -> None:
        support_infra = self.get_support_infra()
        for k, v in kwargs.items():
            if k in support_infra:
                setattr(self, k, v)
            else:
                warnings.warn(f"{k} is ignored in `reset_infra`!")

    def get(self, infra_name: str) -> Any:
        if hasattr(self, infra_name):
            return getattr(self, infra_name)
    
    def has(self, infra_name: str) -> bool:
        return infra_name in self.get_support_infra() and hasattr(self, infra_name)
    
    def update(self, other: BaseInfrastructure) -> None:
        support_infra = other.get_support_infra()
        infra_dict = {_infra: getattr(other, _infra) for _infra in support_infra if hasattr(other, _infra)}
        self.reset_infra(**infra_dict)

    
class CommonInfrastructure(BaseInfrastructure):
    def get_support_infra(self) -> Set[str]:
        return {"trade_account", "trade_exchange"}
    
class LevelInfrastructure(BaseInfrastructure):
    """
    level infrastructure is created by executor, and then shared to strategies on the same level
    """
    def get_support_infra(self) -> Set[str]:
        return {"trade_calendar", "sub_level_infra", "common_infra", "executor"}
    
    def reset_cal(self, freq: str, start_time: Union[str, pd.Timestamp, None], end_time: Union[str, pd.Timestamp, None]) -> None:
        """reset trade calendar manager """
        if self.has("trade_calendar"):
            self.get("trade_calendar").reset(freq, start_time=start_time, end_time=end_time)
        else:
            self.reset_infra(trade_calendar=TradeCalendarManager(freq, start_time=start_time, end_time=end_time, level_infra=self))

    def set_sub_level_infra(self, sub_level_infra: LevelInfrastructure) -> None:
        """this will make the calendar access easier when crossing multi-levels"""
        self.reset_infra(sub_level_infra=sub_level_infra)
    
# def get_start_end_idx(trade_calendar: TradeCalendarManager, outer_trade_decision: BaseTradeDecision) -> Tuple[int, int]:
#     """
#     A helper function for getting the decision-level index range limitation for inner strategy
#     - NOTE: this function is not applicable to order-level

#     Parameters
#     ----------
#     trade_calendar : TradeCalendarManager
#     outer_trade_decision : BaseTradeDecision
#         the trade decision made by outer strategy

#     Returns
#     -------
#     Union[int, int]:
#         start index and end index
#     """
#     try:
#         return outer_trade_decision.get_range_limit(inner_calendar=trade_calendar)
#     except NotImplementedError:
#         return 0, trade_calendar.get_trade_len() - 1
    
