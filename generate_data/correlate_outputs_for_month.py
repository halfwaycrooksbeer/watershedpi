import os
import sys
import csv
import json
import datetime
import calendar
import statistics
from print_json import print_json
from parse_data_tuples_to_json import parse_data_tuples
from date_enums import WeekdayEnum, MonthEnum
from MonthData import MonthData, DayData, WeekData

cur_dir = os.path.join(os.getcwd(), os.path.dirname(__file__))
json_dir = os.path.join(cur_dir, 'outputs')
tuples_dir = os.path.join(cur_dir, 'inputs')

def main():
	dst_year_input = '2021'
	src_year_input = '2021'

	if len(sys.argv) < 3:
		dst_month_input = input("Enter name of target month: ")
		src_months_input = input("Enter all source month names (separated by spaces): ").split(' ')
	else:
		dst_month_input = sys.argv[1]
		src_months_input = sys.argv[2:]
	dst_month_input = dst_month_input.lower().strip()
	src_months_input = [src.lower().strip() for src in src_months_input]

	dst_month_enum = eval('MonthEnum.{}'.format(dst_month_input.upper()))
	dst_month_name = '/'.join([str(dst_month_enum.value), dst_year_input])  # i.e., "8/2021"

	month_output_file = os.path.join(json_dir, '{}_{}_data.json'.format(dst_year_input, dst_month_input))
	print('Targeting output file: "{}"'.format(month_output_file))
	month_input_file_list = [os.path.join(json_dir, '{}_{}_data.json'.format(src_year_input, src)) for src in src_months_input]

	month_input_jsons = {}
	for in_file in month_input_file_list:
		print('Found input file: "{}"'.format(os.path.basename(in_file)))
		if os.path.exists(in_file):
			with open(in_file, 'r') as src:
				month_name = os.path.basename(in_file).split('_')[1]
				month_input_jsons[month_name] = MonthData(json.loads(src.read()))
		else:
			print('Error: Could not find input source file "{}"'.format(in_file))

	# for month_name in month_input_jsons:
	# 	print(month_name)
	# 	print(month_input_jsons.get(month_name))
	# 	print('\n\n')

	## TODO: Group days of months by temporal proximity, average their values for those days, then map generated values out to new target month
	## TODO: Map days into Weeks -- using `is_weekend` & `week_number` to delimit

	input_month_objects = month_input_jsons.values() #[]
	weekly_outputs = {
		"week1": {},
		"week2": {},
		"week3": {},
		"week4": {},
		"week5": {}
	}
	for month in input_month_objects:
		for week_num in range(1, 6):
			week_input_key = str(week_num)
			week_output_key = 'week{}'.format(week_input_key)
			if not week_input_key in month.weeks_dict:
				continue

			for day in [d for d in month.weeks_dict[week_input_key].days if d.week_number == week_num]:
				day_key = day.day_of_week.name
				if not day_key in weekly_outputs[week_output_key]:
					weekly_outputs[week_output_key][day_key] = list()
				weekly_outputs[week_output_key][day_key].append(day)

	print(print_json(weekly_outputs))

	output_month_object, output_data_tuples = correlate_inputs_to_output(weekly_outputs, dst_month_name)

	# Save data tuples to file
	month_tuples_file = os.path.join(tuples_dir, '{}_data_tuples.txt'.format(dst_month_input))
	with open(month_tuples_file, 'w+') as tuples_file:
		tuples_file.write(output_data_tuples.__str__())
	print('\nSaved data tuples to file: {}'.format(month_tuples_file))

	# Save MonthData object to file
	output_month_object.save_to(month_output_file)

	# Pass data tuples file to `parse_data_tuples_to_json.py` & verify that output JSON matches saved MonthData object
	parsed_data_dict, month_id, suggested_filename = parse_data_tuples(output_data_tuples)
	parsed_dict_path = os.path.join(json_dir, suggested_filename.replace('.json', '(parsed).json'))
	with open(parsed_dict_path, 'w+') as outfile:
		outfile.write(print_json(parsed_data_dict))
	print('\nParsed data dict saved to file: {}'.format(parsed_dict_path))

	# Format data for translation into SMR form
	camel_case_month_name = dst_month_input.replace(dst_month_input[0], dst_month_input[0].upper())
	pseudo_smr_file = os.path.join(json_dir, 'SMR_Form_{}_{}.csv'.format(camel_case_month_name, dst_year_input))
	smr_column_names = ['DATE', 'FLOW - gpd', 'pH - Low', 'pH - High']
	with open(pseudo_smr_file, 'w') as smr:
		csv_out = csv.writer(smr)
		csv_out.writerow(smr_column_names)
		for day in output_month_object.days_dict.values():
			row = (int(day.id), day.gallons_per_day, day.ph_min, day.ph_max) if not day.is_weekend else (int(day.id), 'no production', 'no production', 'no production')
			csv_out.writerow(row)
	print('\nPsuedo SMR form generated for ${}: {}'.format(camel_case_month_name, pseudo_smr_file))

	print('\n\nGENERATED CORRELATION DATA OUTPUT FOR MONTH [{}]:\n{!s}'.format(dst_month_name, output_month_object))
	print('\n\nOUTPUT FILES GENERATED:\n>> {}\n>>{}\n>>{}\n>>{}\n'.format(month_output_file, month_tuples_file, parsed_dict_path, pseudo_smr_file))

	"""
	print('\n\nFlow: Days {} - {}'.format(output_month_object.start_day, output_month_object.end_day))
	for day in output_month_object.days_dict.values():
		print(day.gallons_per_day if not day.is_weekend else 'no production')

	print('\n\npH - Low: Days {} - {}'.format(output_month_object.start_day, output_month_object.end_day))
	for day in output_month_object.days_dict.values():
		print(day.ph_min if not day.is_weekend else 'no production')

	print('\n\npH - High: Days {} - {}'.format(output_month_object.start_day, output_month_object.end_day))
	for day in output_month_object.days_dict.values():
		print(day.ph_max if not day.is_weekend else 'no production')
	"""


def correlate_inputs_to_output(weekly_data_src, month_name_dst):
	month_json = {}
	month_json[month_name_dst] = {}
	m, y = [int(x) for x in month_name_dst.split('/')]
	number_of_days_in_month = calendar.monthrange(y, m)[1]
	week_number = 1
	weekday_occurrences = {}
	data_tuples = []

	for d in range(1, number_of_days_in_month+1):
		day_key = str(d)
		date = datetime.date(y, m, d)
		month_of_year = MonthEnum(m)
		day_of_week = WeekdayEnum(date.isoweekday())
		is_weekend = day_of_week == WeekdayEnum.SATURDAY or day_of_week == WeekdayEnum.SUNDAY
		if not day_of_week.name in weekday_occurrences:
			weekday_occurrences[day_of_week.name] = 1
		else:
			weekday_occurrences[day_of_week.name] += 1
		if week_number < weekday_occurrences[day_of_week.name]:
			week_number += 1

		month_json[month_name_dst][day_key] = {
			"date": date,
			"day_of_week": day_of_week,
			"is_weekend": is_weekend,
			"month_of_year": month_of_year,
			"week_number": week_number,
			"weekday_occurrence": weekday_occurrences[day_of_week.name],
			"gallons_per_day": 0.00,
			"ph_min": 0.00,
			"ph_max": 0.00
		}

		# # 'No production' on weekends
		# if is_weekend:
		# 	continue

		day_data = DayData(day_key, month_json[month_name_dst][day_key])

		week_key = 'week{}'.format(str(week_number))
		week_src = weekly_data_src[week_key]  # week_src will be a dict with WeekdayEnum.name as key & list of DayData objects as value

		if day_of_week.name in week_src:
			day_srcs = week_src[day_of_week.name]

			# Correlate mean GPD
			day_data.gallons_per_day = round(statistics.mean([src_day.gallons_per_day for src_day in day_srcs]), 2)
			month_json[month_name_dst][day_key]['gallons_per_day'] = day_data.gallons_per_day

			# Correlate mean pH limits
			day_data.ph_min = round(statistics.mean([src_day.ph_min for src_day in day_srcs]), 2)
			day_data.ph_max = round(statistics.mean([src_day.ph_max for src_day in day_srcs]), 2)
			month_json[month_name_dst][day_key]['ph_min'] = day_data.ph_min
			month_json[month_name_dst][day_key]['ph_max'] = day_data.ph_max

		# First tuple value: Date
		date_str = '/'.join([str(m), day_key, str(y)])
		# Second typle value: GPD

		gpd_str = '{:,.2f}'.format(day_data.gallons_per_day)
		# Third tuple value: pH_min / pH_max

		ph_str = '{:.2f} / {:.2f}'.format(day_data.ph_min, day_data.ph_max)

		data_tuples.append((date_str, gpd_str, ph_str))


	return MonthData(month_json), data_tuples


if __name__ == '__main__':
	main()