"""
Time related utils are compiled in this script
"""

import bisect
from datetime import datetime, time, date, timedelta
from typing import List, Optional, Tuple, Union
import functools
import re 

import pandas as pd

from qlib.config import C
from qlib.constant import REG_CN, REG_US, REG_TW

CN_TIME = [
    datetime.strptime("9:30", "%H:%M"),
    datetime.strptime("11:30", "%H:%M"),
    datetime.strptime("13:00", "%H:%M"),
    datetime.strptime("15:00", "%H:%M"),
]

US_TIME = [datetime.strptime("9:30", "%H:%M"), datetime.strptime("16:00", "%H:%M")]
TW_TIME = [datetime.strptime("9:00", "%H:%M"), datetime.strptime("13:30", "%H:%M")]

@functools.lru_cache(maxsize=240)
def get_min_cal(shift: int = 0, region: str = REG_CN) -> List[time]:
    cal = []

    if region == REG_CN:
        for ts in list(pd.date_range(CN_TIME[0], CN_TIME[1] - timedelta(minutes=1), freq="1min") - pd.Timedelta(minutes=shift)
        )   + list(pd.date_range(CN_TIME[2], CN_TIME[3] - timedelta(minutes=1), freq="1min") - pd.Timedelta(minutes=shift)):
            cal.append(ts.time())
    elif region == REG_TW:
        for ts in list(pd.date_range(TW_TIME[0], TW_TIME[1] - timedelta(minutes=1), freq="1min") - pd.Timedelta(minutes=shift)):
            cal.append(ts.time())
    elif region == REG_US:
        for ts in list(pd.date_range(US_TIME[0], US_TIME[1] - timedelta(minutes=1), freq="1min") - pd.Timedelta(minutes=shift)):
            cal.append(ts.time())
    else:
        raise ValueError(f"{region} is not supported")
    return cal

def is_single_value(start_time, end_time, freq, region: str = REG_CN):
    if region == REG_CN:
        if end_time - start_time < freq:
            return True
        if start_time.hour == 11 and start_time.minute == 29 and start_time.second == 0:
            return True
        if start_time.hour == 14 and start_time.minute == 59 and start_time.second == 0:
            return True
        return False
    elif region == REG_TW:
        if end_time - start_time < freq:
            return True
        if start_time.hour == 13 and start_time.minute == 25 and start_time.second == 0:
            return True
        return False
    elif region == REG_US:
        if end_time - start_time < freq:
            return True
        if start_time.hour == 15 and start_time.minute == 59 and start_time.second == 0:
            return True
        return False
    else:
        raise NotImplementedError(f"please implement the is_single_value func for {region}")
    
class Freq:
    NORM_FREQ_MONTH = "month"
    NORM_FREQ_WEEK = "week"
    NORM_FREQ_DAY = "day"
    NORM_FREQ_MINUTE = "min" # using min instead of minute for align Qlib's data filename
    SUPPORT_CAL_LIST = [NORM_FREQ_MINUTE, NORM_FREQ_DAY] # FIXME: this list should from data

    def __init__(self, freq: Union[str, "Freq"]) -> None:
        if isinstance(freq, str):
            self.count, self.base = self.parse(freq)
        elif isinstance(freq, Freq):
            self.count, self.base = freq.count, freq.base
        else:
            raise NotImplementedError(f"This type of input is not supported")
        
    def __eq__(self, freq):
        freq = Freq(freq)
        return self.count == freq.count and self.base == freq.base
    
    def __str__(self):
        # trying to align to the filename of Qlib: day, 30min, 5min, 1min...
        return f"{self.count if self.count != 1 or self.base != 'day' else ''}{self.base}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)})"
    
    @staticmethod
    def parse(freq: str) -> Tuple[int, str]:
        freq = freq.lower()
        match_obj = re.match("^([0-9]*)(month|mon|week|w|day|d|minute|min)$", freq)
        if match_obj is None:
            raise ValueError(f"{freq} is not supported")
        _count = int(match_obj.group(1)) if match_obj.group(1) else 1
        _freq = match_obj.group(2)
        _freq_format_dict = {
            "month": Freq.NORM_FREQ_MONTH,
            "mon": Freq.NORM_FREQ_MONTH,
            "week": Freq.NORM_FREQ_WEEK,
            "w": Freq.NORM_FREQ_WEEK,
            "day": Freq.NORM_FREQ_DAY,
            "d": Freq.NORM_FREQ_DAY,
            "minute": Freq.NORM_FREQ_MINUTE,
            "min": Freq.NORM_FREQ_MINUTE,
        }
        return _count, _freq_format_dict[_freq]
    
    @staticmethod
    def get_timedelta(n: int, freq: str) -> pd.Timedelta:
        return pd.Timedelta(f"{n}{freq}")
    
    @staticmethod
    def get_min_delta(left_freq: str, right_freq: str):
        """Calculate freq delta
        Parameters
        ----------
        left_freq: str
        right_freq: str
        Returns
        -------
        """
        minutes_map = {
            Freq.NORM_FREQ_MINUTE: 1,
            Freq.NORM_FREQ_DAY: 24 * 60,
            Freq.NORM_FREQ_WEEK: 7 * 24 * 60,
            Freq.NORM_FREQ_MONTH: 30 * 24 * 60,
        }
        left_freq = Freq(left_freq)
        left_minutes = left_freq.count * minutes_map[left_freq.base]
        right_freq = Freq(right_freq)
        right_minutes = right_freq.count * minutes_map[right_freq.base]
        return left_minutes - right_minutes
    
    @staticmethod
    def get_recent_freq(base_freq: Union[str, "Freq"], freq_list: List[Union[str, "Freq"]]) -> Optional["Freq"]:
        """Get the closest freq to base_freq from freq_list
        Parameters
        ----------
        base_freq: Union[str, "Freq"]
        freq_list: List[Union[str, "Freq"]]

        Returns
        -------
        if the recent frequency is found, return
        else return None
        """
        base_freq = Freq(base_freq)
        # use the nearest freq greater than 0
        min_freq = None
        for _freq in freq_list:
            _min_delta = Freq.get_min_delta(base_freq, _freq)
            if _min_delta < 0:
                continue
            if min_freq is None:
                min_freq = (_min_delta, str(_freq))
                continue
            min_freq = min_freq if min_freq[0] < _min_delta else (_min_delta, str(_freq))
        return min_freq[1] if min_freq else None
    
def time_to_day_index(time_obj: Union[str, datetime], region: str = REG_CN):
    if isinstance(time_obj, str):
        time_obj = datetime.strptime(time_obj, "%H:%M")
    if region == REG_CN:
        if CN_TIME[0] <= time_obj < CN_TIME[1]:
            return int((time_obj - CN_TIME[0]).total_seconds() / 60)
        elif CN_TIME[2] <= time_obj < CN_TIME[3]:
            return int((time_obj - CN_TIME[2]).total_seconds() / 60) + 120
        else:
            raise ValueError(f"{time_obj} is not in the trading time")
    elif region == REG_TW:
        if TW_TIME[0] <= time_obj < TW_TIME[1]:
            return int((time_obj - TW_TIME[0]).total_seconds() / 60)
        else:
            raise ValueError(f"{time_obj} is not in the trading time")
    elif region == REG_US:
        if US_TIME[0] <= time_obj < US_TIME[1]:
            return int((time_obj - US_TIME[0]).total_seconds() / 60)
        else:
            raise ValueError(f"{time_obj} is not in the trading time")
    else:
        raise ValueError(f"{region} is not supported")
    
def get_day_min_idx_range(start: str, end: str, freq: str, region: str) -> Tuple[int, int]:
    """
    get the min-bar index in a day for a time range (both left and right is closed) given a fixed frequency
    Parameters
    ----------
    start: str
        e.g. "9:30"
    end: str
        e.g. "14:30"
    
    Returns
    -------
    Tuple[int, int]:
        The index of start and end in the calendar. Both left and right are **closed**.
    """
    start = pd.Timestamp(start).time()
    end = pd.Timestamp(end).time()
    freq = Freq(freq)
    in_day_cal = get_min_cal(region=region)[:: freq.count]
    left_idx = bisect.bisect_left(in_day_cal, start)
    right_idx = bisect.bisect_right(in_day_cal, end) - 1
    return left_idx, right_idx

def concat_date_time(date_obj: date, time_obj: time) -> pd.Timestamp:
    return pd.Timestamp(
        datetime(
            date_obj.year,
            month=date_obj.month,
            day=date_obj.day,
            hour=time_obj.hour,
            minute=time_obj.minute,
            second=time_obj.second,
            microsecond=time_obj.microsecond,
        )
    )


