from __future__ import annotations

from datetime import datetime, timedelta
from typing import Union, overload


class Date:
    """Date object using datetime"""

    def __init__(self, date: Union[str, datetime]) -> None:
        self.date_obj: datetime
        date_str: str = ""
        if isinstance(date, datetime):
            date_obj: datetime = date
            year: int = int(date_obj.year)
            month: int = int(date_obj.month)
            day: int = int(date_obj.day)
            date_str = "-".join([str(year), str(month), str(day)])
        else:
            date_str = date
        date_str = date_str.split("T")[0] if "T" in date_str else date_str
        self.date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    def __str__(self) -> str:
        return str(self.date_obj.date())

    def __add__(self, other: int) -> Date:
        new_date: Date = Date(self.date_obj + timedelta(days=other))
        return new_date

    @overload
    def __sub__(self, other: int) -> Date:
        return Date("")  # never called

    @overload
    def __sub__(self, other: Date) -> int:
        return 0  # never called

    def __sub__(self, other: Union[int, Date]) -> Union[int, Date]:
        if isinstance(other, int):
            return Date(self.date_obj - timedelta(days=other))
        else:
            return abs((self.date_obj - other.date_obj).days)

    def __lt__(self, other: Date) -> bool:
        return self.date_obj < other.date_obj

    def __le__(self, other: Date) -> bool:
        return self.date_obj <= other.date_obj

    def __gt__(self, other: Date) -> bool:
        return self.date_obj > other.date_obj

    def __ge__(self, other: Date) -> bool:
        return self.date_obj >= other.date_obj

    def year(self) -> int:
        return self.date_obj.year

    def month(self) -> int:
        return self.date_obj.month

    def day(self) -> int:
        return self.date_obj.day


today = Date(datetime.now())
