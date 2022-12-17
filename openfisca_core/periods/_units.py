import enum

DAY = "day"
MONTH = "month"
YEAR = "year"
ETERNITY = "eternity"


class DateUnit(enum.IntFlag):
    day = enum.auto()
    month = enum.auto()
    year = enum.auto()
    eternity = enum.auto()
