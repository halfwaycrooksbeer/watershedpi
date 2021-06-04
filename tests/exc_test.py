import traceback
import os
import sys
import time
import datetime as dt 
import random


ERROR_LOGFILE = "test_errors.log"
ENTRY_TIME_FORMAT = "%m/%d/%Y,%I:%M:%S %p"


def get_timestamp(dt_obj=None):
	if dt_obj is None:
		dt_obj = dt.datetime.now()
	dt_str = dt_obj.strftime(ENTRY_TIME_FORMAT)
	m_str = dt_str.split('/')[0]
	if m_str[0] == '0':
		m_str = m_str[1:]
	d_str  = dt_str.split('/')[1]
	if d_str[0] == '0':
		d_str = d_str[1:]
	dt_str = '/'.join([m_str, d_str, *(dt_str.split('/')[2:])])
	return dt_str



if __name__ == "__main__":
	
	exc_string = ""
	cnt = 0
	pH = 6.66

	while True:
		try:
			cnt += 1

			pH = float(random.randrange(1, 14, 1)) + (cnt * 0.01)

			if pH < 6.0:
				print(' << caught pH of {:.2f} >>'.format(pH))
				pH = (float(random.randrange(61, 69, 1)) / 10.0) + ((int(pH * 100.0) % 10) * 0.01)
			elif pH > 12.0:
				print(' << caught pH of {:.2f} >>'.format(pH))
				pH = (float(random.randrange(111, 119, 1)) / 10.0) + ((int(pH * 100.0) % 10) * 0.01)

			print("[ {} ]\tpH = {:.2f}".format(get_timestamp(), pH))
			time.sleep(0.25)

			if (cnt % 75) == 0:
				cnt /= (cnt-cnt)	## Divide by zero error

		# except KeyboardInterrupt as exc:
		# 	exc_string = "KeyboardInterrupt\n"
		# 	tb = sys.exc_info()[0]
		# 	print("\n\n~~~~~~\n{}\n~~~~~~\n\n".format(tb))
			# exc_string = '{}\n'.format(exc.__class__.__name__)
			# break

		except (KeyboardInterrupt, SystemExit, Exception) as exc:
			exc_string = '{}  (line #: {})\n'.format(exc.__class__.__name__, sys.exc_info()[2].tb_lineno)
			# lineno = sys.exc_info()[2].tb_lineno

			# with open(ERROR_LOGFILE, 'a') as f:
			# 	f.write('\n[ {} ]\t--> watershed.py exited the program loop\n\t>>> Cause:\t{}'.format(get_timestamp(), exc_string))
			# tb = sys.exc_info()[0]
			# print("\n\n~~~~~~\n{}\n~~~~~~\n\n".format(tb))
			# print("\n\n~~~~~~\n{}  (line {})\n~~~~~~\n\n".format(exc_string, lineno))
			break

		# finally:
		# 	if exc_string != "":
		# 		with open(ERROR_LOGFILE, 'a') as f:
		# 			f.write('\n[ {} ]\t--> watershed.py exited the program loop\n\t>>> Cause:\t{}'.format(get_timestamp(), exc_string))

	with open(ERROR_LOGFILE, 'a') as f:
		f.write('\n[ {} ]\t--> watershed.py exited the program loop\n\t>>> Cause:\t{}'.format(get_timestamp(), exc_string))
