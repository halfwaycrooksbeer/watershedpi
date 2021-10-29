from enum import Enum

class WeekdayEnum(Enum):
	MONDAY = 1
	TUESDAY = 2
	WEDNESDAY = 3
	THURSDAY = 4
	FRIDAY = 5
	SATURDAY = 6
	SUNDAY = 7

class MonthEnum(Enum):
	JANUARY = 1
	FEBRUARY = 2
	MARCH = 3
	APRIL = 4
	MAY = 5
	JUNE = 6
	JULY = 7
	AUGUST = 8
	SEPTEMBER = 9
	OCTOBER = 10
	NOVEMBER = 11
	DECEMBER = 12


if __name__ == '__main__':
	m_str = "MonthEnum.OCTOBER"
	m = eval(m_str)
	print(m)
	print(type(m))
