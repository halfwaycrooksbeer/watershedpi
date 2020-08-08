import os
import sys

# print(sys.argv[0])
# print(__file__)
# print(__name__)
from time import sleep
from itertools import islice
import json

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
	{'10/5/2020,12:00:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:00:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:00:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:00:45 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:01:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:01:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:01:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:01:45 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:02:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:02:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:02:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:02:45 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:03:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:03:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:03:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:03:45 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:04:00 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:04:15 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:04:30 AM': {'p': 7.83, 'l': 1.7}},
	{'10/5/2020,12:04:45 AM': {'p': 7.83, 'l': 1.7}}
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


def process_missed_payloads():
	num = total_failed_payloads
	for i in range(num):
		missed_payload = list()
		start_line = i * JSON_CAPACITY

		with open(FAILED_PAYLOADS_FILE) as f:
			for line in islice(f, start_line, None):	## Skip already processed entries
				line = line.replace("}}", "}},")
				for str_dict in line.split('},'): 
					if str_dict:
						str_dict = str(str_dict).replace("'",'"') + '}'
						# converted_dict = json.loads(str_dict)
						import ast
						converted_dict = ast.literal_eval(str_dict)
						print(converted_dict)
						missed_payload.append(converted_dict)	## Use json.loads() to convert dict string to a dict object

		print("[process_missed_payloads]\n-->\tPayload #{}:".format(i))
		for entry in missed_payload:
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