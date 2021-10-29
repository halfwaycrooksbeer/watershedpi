import datetime
from calendar import monthrange
from date_enums import WeekdayEnum, MonthEnum
from print_json import print_json


class MonthData():
	def __init__(self, data_dict):
		# Name will be of format "10/2021"
		[self.name, self.days_dict] = [item for item in data_dict.items()][0]
		(self.month, self.year) = [int(v) for v in self.name.split('/')]
		self.days_in_month = monthrange(self.year, self.month)[1]
		self.end_day = str(self.days_in_month)
		self.start_day = "1"
		self.weeks_dict = {}
		for day in self.days_dict:
			day_data = DayData(day, self.days_dict[day])
			self.days_dict[day] = day_data
			week_key = str(day_data.week_number)
			if not week_key in self.weeks_dict:
				self.weeks_dict[week_key] = []
			self.weeks_dict[week_key].append(day_data)
		
		for week in self.weeks_dict:
			self.weeks_dict[week] = WeekData(week, self.weeks_dict[week])

		self._json = data_dict  # For writing to file


	def save_to(self, filepath):
		with open(filepath, 'w+') as outfile:
			outfile.write(print_json(self._json))
		print('\nFile saved for MonthData("{}"): {}'.format(self.name, filepath))

	def __str__(self):
		return print_json(self.__repr__())

	def __repr__(self):
		return ({
			'name': self.name,
			'month': self.month,
			'year': self.year,
			'start_day': self.start_day,
			'end_day': self.end_day,
			'days_in_month': self.days_in_month,
			'days_dict': self.days_dict,
			'weeks_dict': self.weeks_dict,
		})


class DayData():
	def __init__(self, day_id, day_obj):
		self.id = day_id
		if type(day_obj['date']) == datetime.date:
			self.date = day_obj['date']
		else:
			if 'datetime.date(' in day_obj['date']:
				self.date = eval(day_obj['date'])
			else:
				self.date = datetime.date(day_obj['date'])		
		self.day_of_week = eval(day_obj['day_of_week']) if type(day_obj['day_of_week']) != WeekdayEnum else day_obj['day_of_week'] 
		self.is_weekend = bool(day_obj['is_weekend'])
		self.month_of_year = eval(day_obj['month_of_year']) if type(day_obj['month_of_year']) != MonthEnum else day_obj['month_of_year'] 
		self.week_number = int(day_obj['week_number'])
		self.weekday_occurrence = int(day_obj['weekday_occurrence'])
		self.gallons_per_day = float(day_obj['gallons_per_day'])
		self.ph_min = float(day_obj['ph_min'])
		self.ph_max = float(day_obj['ph_max'])
		
	def __str__(self):
		return print_json(self.__repr__())

	def __repr__(self):
		return ({
			'id': self.id,
			'date': self.date,
			'day_of_week': self.day_of_week,
			'is_weekend': self.is_weekend,
			'month_of_year': self.month_of_year,
			'week_number': self.week_number,
			'weekday_occurrence': self.weekday_occurrence,
			'gallons_per_day': self.gallons_per_day,
			'ph_min': self.ph_min,
			'ph_max': self.ph_max,
		})

class WeekData():
	def __init__(self, week_num, day_list):
		self.week_number = week_num
		self.days = day_list
