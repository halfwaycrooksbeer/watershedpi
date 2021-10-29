import os
import ast
import sys
import json
import datetime as dt
from date_enums import WeekdayEnum, MonthEnum
from print_json import print_json

## TODO: Add support for year input/CLI arg + source data naming convention

## TODO: Make another script that takes in a CSV/XLSX (or Google Sheet) & parses into list of data tuples for this program

def parse_data_tuples(month_data_tuples):
	month_data_dict = {}
	weekday_occurrences = {}
	week_number = None
	month_id = None
	month_name = None
	banner = '*'*36
	print(banner, banner, sep='\n')

	for data_tuple in month_data_tuples:
		date_str = data_tuple[0]
		year, day, month = ([int(v) for v in date_str.split('/')][::-1])
		date_obj = dt.date(year, month, day)

		if month_id is None:
			month_id = '/'.join([str(month), str(year)])  # i.e., "7/2021"
		print('[             {}           ]'.format(month_id))
		if not month_id in month_data_dict:
			month_data_dict[month_id] = {}
			week_number = 1
		print('[ {} ] <---> [ {} ]\n'.format(date_obj.isoformat(), date_str))

		month_of_year = MonthEnum(month)
		if month_name is None:
			month_name = month_of_year.name
		print('>> Month of Year:   {!s}'.format(month_of_year.name))

		# `isoweekday`: Return the day of the week as an integer, where Monday is 1 and Sunday is 7
		day_of_week = WeekdayEnum(date_obj.isoweekday())
		dow_key = day_of_week.name
		if not dow_key in weekday_occurrences:
			weekday_occurrences[dow_key] = 1
		else:
			weekday_occurrences[dow_key] += 1
		if week_number < weekday_occurrences[dow_key]:
			week_number += 1
		print('>> Week Number:     {!s}'.format(week_number))
		print('>> Day of Week:     {!s}  (occur. #{})'.format(day_of_week.name, weekday_occurrences[dow_key]))

		is_weekend = day_of_week == WeekdayEnum.SATURDAY or day_of_week == WeekdayEnum.SUNDAY
		print('>> Is Weekend:      {}'.format(is_weekend))
		
		gpd = float(data_tuple[1].replace(',', ''))
		print('>> Gallons per Day: {:,.2f}'.format(gpd))  # i.e., "2,099.49"
		ph_min, ph_max = ([float(v.strip()) for v in data_tuple[-1].split('/')])
		print('>> pH Minumum:      {:.2f}\n>> pH Maximum:      {:.2f}'.format(ph_min, ph_max))
		
		month_data_dict[month_id][str(day)] = {
			"id": str(day),
			"date": date_obj,
			"day_of_week": day_of_week,
			"is_weekend": is_weekend,
			"month_of_year": month_of_year,
			"week_number": week_number,
			"weekday_occurrence": weekday_occurrences[dow_key],
			"gallons_per_day": gpd,
			"ph_min": ph_min,
			"ph_max": ph_max,
		}

		print('\n' + banner + '\n')

	suggested_filename = '_'.join([month_id.split('/')[1], month_name.lower(), 'data.json']) 
	return month_data_dict, month_id, suggested_filename


month_json = {
	'id': None,
	'name': None,
	'path': None,
	'data': None,
	'obj': None
}

if __name__ == '__main__':
	cur_dir = os.path.join(os.getcwd(), os.path.dirname(__file__))

	# with open(os.path.join(cur_dir, 'july_data_tuples.txt'), 'w+') as init_file:
	# 	print(july_data_tuples.__str__())
	# 	init_file.write((july_data_tuples.__str__()))

	if len(sys.argv) < 2:
		month_input = input("Enter name of month: ")
	else:
		month_input = sys.argv[1]
	month_input = month_input.lower().strip()

	month_input_file = os.path.join(cur_dir, 'inputs', '{}_data_tuples.txt'.format(month_input))
	print('Searching for input file: {}'.format(month_input_file))
	with open(month_input_file, 'r') as input_file:
		month_data_tuples_str = input_file.read()
		month_data_tuples = ast.literal_eval(month_data_tuples_str)
	print('Data tuples fetched for {}'.format(month_input))

	# month_json['data'], month_json['id'], month_json['name'] = parse_data_tuples(july_data_tuples)
	month_json['data'], month_json['id'], month_json['name'] = parse_data_tuples(month_data_tuples)

	month_json['path'] = os.path.join(cur_dir, 'outputs', month_json['name'])

	# Serializing json 
	month_json['obj'] = print_json(month_json['data'])
	print('\nDATA REPORT FOR MONTH [{}]:\n{!s}'.format(month_json['id'], month_json['obj']))

	# Writing to sample.json
	with open(month_json['path'], 'w+') as outfile:
		outfile.write(month_json['obj'])
	print('\n\nFile Saved: {}'.format(month_json['path']))