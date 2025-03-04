from typing import List

from pydantic import BaseModel

from src.models.wrapped.bar import BarData
from src.models.wrapped.calendar import CalendarDayData
from src.models.wrapped.numeric import NumericData
from src.models.wrapped.pie import PieData


class WrappedPackage(BaseModel):
    bar_data: BarData
    calendar_data: List[CalendarDayData]
    numeric_data: NumericData
    pie_data: PieData
