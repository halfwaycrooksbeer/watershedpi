import os
import sys
import ast
import json
import itertools
from time import sleep
import datetime as dt

# print(sys.argv[0])
# print(__file__)
# print(__name__)

JSON_CAPACITY = 20
NUM_PAYLOADS_FILE = "num_payloads.txt"
# FAILED_PAYLOADS_FILE = "missed_payloads.json"
FAILED_PAYLOADS_FILE = "missed_payloads.txt"
total_failed_payloads = 0

payload1 = [ 
	{'10/4/2020,12:00:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:00:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:00:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:00:45 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:01:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:01:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:01:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:01:45 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:02:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:02:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:02:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:02:45 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:03:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:03:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:03:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:03:45 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:04:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:04:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:04:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/4/2020,12:04:45 AM': {'p': 7.83, 'l': 1.7}}
]

payload2 = [ 
	{'10/5/2020,12:00:00 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:00:15 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:00:30 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:00:45 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:01:00 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:01:15 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:01:30 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:01:45 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:02:00 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:02:15 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:02:30 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:02:45 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:03:00 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:03:15 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:03:30 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:03:45 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:04:00 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:04:15 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:04:30 PM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:04:45 PM': {'p': 7.83, 'l': 1.7}}
]

def setup():
	global total_failed_payloads
	if os.path.isfile(NUM_PAYLOADS_FILE):
		with open(NUM_PAYLOADS_FILE) as f:
			n = f.read()
		try:
			total_failed_payloads = int(n)
			print('[setup] Discovered {} missed payloads to be delivered.'.format(total_failed_payloads))
		except ValueError:
			print('[setup] ValueError --> NUM_PAYLOADS_FILE read out non-number:  "{}"'.format(total_failed_payloads))
			total_failed_payloads = 0
	else:
		print('[setup] No NUM_PAYLOADS_FILE exists yet.')
		total_failed_payloads = 0


def update_num_failed_payloads(diff=0):
	global total_failed_payloads
	total_failed_payloads += diff 
	with open(NUM_PAYLOADS_FILE, 'w') as f:
		f.write(str(total_failed_payloads))


def cache_payload(list_of_json):
	update_num_failed_payloads(1)

	print("(#{})\tNow caching missed payload".format(total_failed_payloads))
	with open(FAILED_PAYLOADS_FILE, 'a') as j:
		for entry in list_of_json:
			# json.dump(entry, j)
			j.write(str(entry).replace("'",'"')+'\n')


def extract_date_from_entry(entry_dict, as_dt_object=False):
	date_str = list(entry_dict.keys())[0]
	if as_dt_object:
		return datestr_to_datetime(date_str)
	return date_str

def datestr_to_datetime(date_str):
	if not ',' in date_str:
		return None 
	if not isinstance(date_str, str):
		return None 
	entry_date, entry_time = date_str.split(',')
	m, d, y = entry_date.split('/')
	hr, mn, scampm = entry_time.split(':')
	hr = int(hr) #-1
	mn = int(mn)
	sc, ampm = scampm.split(' ')
	sc = int(sc)
	# if ampm == 'PM':
		# hr += 12
	if ampm == 'AM':
		hr -= 12
	dt_obj = dt.datetime(int(y), int(m), int(d), hour=hr, minute=mn, second=sc)
	return dt_obj


def get_dt_obj_from_entry_time(et=None):	## Don't use...
	if et is None:
		return dt.datetime.now()
	entry_time_date, entry_time_time = et.split(',')
	m, d, y = entry_time_date.split('/')
	hr, mn, scampm = entry_time_time.split(':')
	hr = int(hr)-1
	mn = int(mn)
	sc, ampm = scampm.split(' ')
	sc = int(sc)
	if ampm == 'PM':
		hr += 12
	return dt.datetime(int(y), int(m), int(d), hour=hr, minute=mn, second=sc)
"""
def get_timestamp(dt_obj=None):
	if dt_obj is None:
		dt_obj = get_datetime_now()
	dt_str = dt_obj.strftime(ENTRY_TIME_FORMAT)
	m_str = dt_str.split('/')[0]
	if m_str[0] == '0':
		m_str = m_str[1:]
	d_str  = dt_str.split('/')[1]
	if d_str[0] == '0':
		d_str = d_str[1:]
	dt_str = '/'.join([m_str, d_str, *(dt_str.split('/')[2:])])
	return dt_str
"""

def process_missed_payloads():
	num = total_failed_payloads
	for i in range(num):
		missed_payload = list()
		start_line = i * JSON_CAPACITY
		stop_line = start_line + JSON_CAPACITY

		with open(FAILED_PAYLOADS_FILE) as f:
			## Syntax:  itertools.islice(iterable, start, stop, step)
			for line in itertools.islice(f, start_line, stop_line, 1):	## Skip already processed entries
				line = line.replace("}}", "}},")
				for str_dict in line.split('},'): 
					if len(str_dict) > 1:
						str_dict = str(str_dict).replace("'",'"') + '}'
						# converted_dict = json.loads(str_dict)
						
						converted_dict = ast.literal_eval(str_dict)	## Using ast.literal_eval() to convert dict string to a dict object (an alternative to json.loads())
						missed_payload.append(converted_dict)

		date = None 
		print("[process_missed_payloads]\n-->  Payload #{}:".format(i))
		# print(missed_payload)
		for entry in missed_payload:

			# date = list(entry.keys())[0]	## Extracts the date string from the entry dict key
			date = extract_date_from_entry(entry, as_dt_object=True)
			# print("{} _({})".format(date, type(date)), end="")
			dt_str = date.strftime("%-m/%-d/%Y,%I:%M:%S %p")
			dt_str2 = extract_date_from_entry(entry, as_dt_object=False)
			print("\ndt_str:  {} _ extracted str:  {}".format(dt_str, dt_str2))
			print("{} _({}) __[{}]".format(date, type(date), dt_str))
			print("(date:  {}) _ (time:  {})".format(*dt_str2.split(',')))
			# date = get_dt_obj_from_entry_time(list(entry.keys())[0])
			# print("{} _({}) __[{}]".format(date, type(date), date.strftime("%m/%d/%Y,%I:%M:%S %p")))

			print("\t{}".format(entry))
		update_num_failed_payloads(-1)


if __name__ == "__main__":
	setup()
	cache_payload(payload1)
	sleep(3)
	cache_payload(payload2)
	sleep(3)
	print("... now recovering missed payloads ...\n")
	try:
		process_missed_payloads()
	# except Exception as e:
	# 	print(e)
	finally:
		os.system("rm {} && rm {}".format(NUM_PAYLOADS_FILE, FAILED_PAYLOADS_FILE))