import os
import re
import sys
import json
import time
import gspread
import datetime as dt
import calendar
from oauth2client.service_account import ServiceAccountCredentials


SIMULATE_END_DATE = True
# REQUEST_BATCH_COLUMN_FORMATTING = True #False
CROOKS_MODE = True 

TEMPLATE = "FlumeDataTemplate"
RESULTS_SHEET_NAME = "Flow&pH"

CREDSFILE = os.path.join(os.environ['HOME'], "watershed_private.json")
CURSHEETFILE = os.path.join(os.environ['HOME'], "cur_sheet2.json")
PUBLISHED_DATES_FILE = os.path.join(os.environ['HOME'], "published_dates2.txt")
SHEET_URL_FILE = os.path.join(os.environ['HOME'], "sheet_url2.txt")

SCOPE = [
			'https://spreadsheets.google.com/feeds',
			'https://www.googleapis.com/auth/drive'
		]

# ENTRY_TIME_FORMAT = "%m/%d/%Y,%I:%M:%S %p"
ENTRY_TIME_FORMAT = "%-m/%-d/%Y,%I:%M:%S %p"
# FULL_DATE_FORMAT = "%-m/%-d/%-y"  ## Including the "-" in the time format specifier will strip all leading zeros
FULL_DATE_FORMAT = "%-m/%-d/%Y"  ## Including the "-" in the time format specifier will strip all leading zeros
DATE_FORMAT = "%-m/%Y"			  ## %y is year without century (e.g., "19"), %Y includes the century (e.g., "2019")
SHORT_DATE_FORMAT = "{0}/{1}"
DATE_RANGE_FORMAT = "{0}-{1}"
NAME_FORMAT = "FlumeData_{0}"
VALUE_INPUT_OPTION = 'USER_ENTERED'

INTERVAL_MONTHS = 4  #3 ## Good options: 3, 4, preferrably 6
INTERVAL_WEEKS = INTERVAL_MONTHS * 4
INTERVAL_DAYS = INTERVAL_WEEKS * 7

MEASUREMENT_INTERVAL = 3  ## <-- for DEV branch work  # 15  ## seconds

GAL_PER_CUBIC_FT = 7.480543
K = 0.338
N = 1.9

col_headers = ["DateTime", "Level (inches)", "pH"]
col_data = ["levelData", "phData"]

SPREADSHEETS_API_V4_BASE_URL = 'https://sheets.googleapis.com/v4/spreadsheets'
SPREADSHEET_URL = SPREADSHEETS_API_V4_BASE_URL + '/%s'
SPREADSHEET_DRIVE_URL = "https://docs.google.com/spreadsheets/d/%s"
WORKSHEET_DRIVE_URL = SPREADSHEET_URL + "#gid=%s"
ACCESSIBLE_SHEET_URL = SPREADSHEET_DRIVE_URL + '/edit#gid=%s'


def get_date_today():
	today = dt.date.today()
	## ... add some timedelta before returning to simulate future dates (for DEBUG) ...
	if SIMULATE_END_DATE:
		today += dt.timedelta(days=57) #, hours=3, minutes=50)
	return today

def get_datetime_now():
	now = dt.datetime.now()
	## ... add some timedelta before returning to simulate future datetimes (for DEBUG) ...
	if SIMULATE_END_DATE:
		now += dt.timedelta(days=57) #, hours=3, minutes=50)
	return now

def get_last_published_date():
	if not os.path.exists(PUBLISHED_DATES_FILE):
		return None
	"""
	with open(PUBLISHED_DATES_FILE, 'rb') as f:
		f.seek(-2, os.SEEK_END)
		while f.read(1) != b'\n':
			f.seek(-2, os.SEEK_CUR)
		last_line = f.readline().decode()
	"""
	with open(PUBLISHED_DATES_FILE) as f:
		for line in f:
			pass
		last_line = line.replace("\n","")
	return last_line

def log_published_date(date_str):
	if "Date" == date_str:
		return
	with open(PUBLISHED_DATES_FILE, 'a+') as dates_file:
		dates_file.write('\n' + date_str)
	print("\n[log_published_date] Newly published date '{}' appended to {}\n".format(date_str, PUBLISHED_DATES_FILE))


def fifteen_seconds_from_dt_obj(dt_obj):
	seconds_delta = dt.timedelta(seconds=MEASUREMENT_INTERVAL)
	return dt_obj + seconds_delta

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

def get_month_range(m=0):
	start_month = 0
	end_month = 0
	today = get_date_today()
	if m < 1 or m > 12:
		m = today.month 
		
	"""
	if INTERVAL_MONTHS == 3:
		if 1 <= m <= 3:
			start_month = 1
		elif 4 <= m <= 6:
			start_month = 4
		elif 7 <= m <= 9:
			start_month = 7
		else:
			start_month = 10
	elif INTERVAL_MONTHS == 4:
		if 1 <= m <= 4:
			start_month = 1
		elif 5 <= m <= 8:
			start_month = 5
		elif 9 <= m:
			start_month = 9
	else: 		#if INTERVAL_MONTHS == 6:
		if 1 <= m <= 6:
			start_month = 1
		elif 7 <= m:
			start_month = 7
	"""
	
	if 1 <= m <= INTERVAL_MONTHS:
		start_month = 1
	elif (INTERVAL_MONTHS+1) <= m <= (INTERVAL_MONTHS*2):
		start_month = (INTERVAL_MONTHS+1)
	elif ((INTERVAL_MONTHS*2)+1) <= m <= (INTERVAL_MONTHS*3):
		start_month = ((INTERVAL_MONTHS*2)+1)
	else:
		start_month = (12 - INTERVAL_MONTHS) + 1

	start = SHORT_DATE_FORMAT.format(start_month, today.year)
	end_month = start_month + (INTERVAL_MONTHS-1)
	end = SHORT_DATE_FORMAT.format(end_month, today.year)
	return DATE_RANGE_FORMAT.format(start, end)


def sanitize_date_string(date=None):
	date_str = None
	if date is None:
		# date = get_date_today().strftime(DATE_FORMAT)
		date_str = get_datetime_now().strftime(FULL_DATE_FORMAT)
	elif isinstance(date, dt.datetime):
		date_str = date.strftime(FULL_DATE_FORMAT)
	elif isinstance(date, str):
		if ',' in date:
			date_str = date.split(',')[0]
		else:
			split_date = date.split('/')
			if len(split_date) != 3 or len(split_date[-1]) > 4:
				# date_str = get_date_today().strftime(DATE_FORMAT)
				date_str = get_datetime_now().strftime(FULL_DATE_FORMAT)
	else:
		date_str = get_datetime_now().strftime(FULL_DATE_FORMAT)
	return date_str


### UPDATE [ 8/10/2020 ]
def extract_date_from_entry(entry_dict, as_dt_object=False):
	## Returns date string by default; change with flag `as_dt_object`
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
	entry_time = entry_time.strip()
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

###

### UPDATE [ 8/10/2020 ]
class Entry():
	def __init__(self, entry_dict, cur_sheet, row=0, client=None, find_on_init=True):
		self.dict = entry_dict
		self.dt_str = list(entry_dict.keys())[0]
		self.dt_obj = datestr_to_datetime(self.dt_str)

		self.sheet = cur_sheet
		# self.wksht = self.sheet.wksht
		self.gc = client
		
		self._sheet_row = row
		if find_on_init:
			self._sheet_row = self.sheet_row

	@property
	def level(self):
		return self.dict[self.dt_str]['l']

	@property
	def ph(self):
		return self.dict[self.dt_str]['p']

	@property
	def values(self):
		return [self.dt_str.replace(', ',',').replace(',',', '), self.level, self.ph]

	@property
	def date_str(self):
		## e.g., "10/31/2020"
		return self.dt_str.split(',')[0]

	@property
	def time_str(self):
		## e.g., "12:00:30 AM"
		return self.dt_str.split(',')[1]
	
	@property
	def wksht(self):
		## TODO: Perform check for needing to open an older workshet for a previous month (see get_results(), refresh(), etc.)
		## TODO: Insert try-except case for when gspread client (`self.gc`) needs to call `open(sheet_title).worksheet(worksheet_title)` after authentication creds expire
		return self.cur_sheet.wksht
	
	@property
	def sheet_row(self):
		if self._sheet_row < 2 or self._sheet_row is None:
			## Search current worksheet for correct row position for this entry (according to date-time)
			date_regex = re.compile(r'\A{}'.format(self.dt_obj.strftime(FULL_DATE_FORMAT)))
			cell_list = self.wksht.findall(date_regex, in_column=1)
			for i in range(len(cell_list)-1):
				this_cell = cell_list[i]
				this_date = datestr_to_datetime(this_cell.value)  ## e.g., "10/3/2020, 09:41:23 PM"
				if this_date < self.dt_obj:
					next_cell = cell_list[i+1]
					next_date = datestr_to_datetime(next_cell.value)
					if self.dt_obj < next_date:
						self._sheet_row = next_cell.row 
						break
		if self._sheet_row < 2 or self._sheet_row is None:
			print("[Entry.sheet_row]  ERROR: No suitable row found for entry date-time '{}'!".format(self.dt_str))	
		return self._sheet_row
	

###



class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]


class SheetManager(metaclass=Singleton):

	def __init__(self):
		self._gc = None
		# self._data = dict()
		self._dates_processed = None
		self._dates_updated = True
		self.cur_sheet = CurrentSheet(self) #self.gc)
		if self.cur_sheet.sheet is None:
			self.generate_newsheet()
			self.cur_sheet = CurrentSheet(self) #self.gc)


	def center_rows(self, start_row, end_row=None, sheet=None):
		if sheet is None:
			sheet = self.cur_sheet.wksht
		if not isinstance(sheet, gspread.Worksheet):
			err_msg = "[center_rows] ERROR: 'sheet' arg must be of type gspread.Worksheet!"
			print(err_msg)
			raise Exception(err_msg)
			sys.exit()
		if end_row is None:
			end_row = start_row
		# new_row_range = sheet.range(sheet.row_count, 1, sheet.row_count, sheet.col_count) 	# worksheet.range(first_row, first_col, last_row, last_col)
		new_row_range = "A{0}:C{0}".format(start_row, end_row)  #sheet.row_count)
		sheet.format(new_row_range, { "horizontalAlignment": "CENTER" })

	def center_row(self, row, sheet=None):
		self.center_rows(row, row, sheet)

	def center_last_row(self, sheet=None):
		self.center_row(sheet.row_count, sheet)
		"""
		if sheet is None:
			sheet = self.cur_sheet.wksht
		if not isinstance(sheet, gspread.Worksheet):
			print("[center_last_row] ERROR: 'sheet' arg must be of type gspread.Worksheet!")
			sys.exit()
		# new_row_range = sheet.range(sheet.row_count, 1, sheet.row_count, sheet.col_count) 	# worksheet.range(first_row, first_col, last_row, last_col)
		new_row_range = "A{0}:C{0}".format(sheet.row_count)
		sheet.format(new_row_range, { "horizontalAlignment": "CENTER" })
		"""
	

	def need_newsheet_check(self, entry_time=None):
		need = False 
		condition = ""
		triggers = dict()

		if entry_time is None:
			today = get_datetime_now()
			entry_time = get_timestamp(today)
		elif isinstance(entry_time, str):
			"""
			entry_time_date, entry_time_time = entry_time.split(',')
			# entry_time_date = entry_time.split(',')[0]
			# print("[need_newsheet_check] entry_time_date = "+entry_time_date)
			m, d, y = entry_time_date.split('/')
			m = int(m)
			d = int(d)
			y = int(y)
			# today = dt.date(y, m, d)
			# entry_time_time = entry_time.split(',')[1]
			hr, mn, scampm = entry_time_time.split(':')
			hr = int(hr) #-1
			mn = int(mn)
			sc, ampm = scampm.split(' ')
			sc = int(sc)
			# if ampm == 'PM':
			# 	hr += 12
			if ampm == 'AM':
				hr -= 12
			today = dt.datetime(y, m, d, hour=hr, minute=mn, second=sc)
			"""
			today = datestr_to_datetime(entry_time)
			entry_time = get_timestamp(today)
		elif isinstance(entry_time, dt.date):
			today = entry_time
			entry_time = get_timestamp(today)
		else:
			fail_msg = "[need_newsheet_check] BAD INPUT FOR entry_time:\t" + str(entry_time)
			print(fail_msg)
			raise Exception(message=fail_msg)
			sys.exit()


		next_entry = fifteen_seconds_from_dt_obj(today)
		next_entry_str = get_timestamp(next_entry)
		edo = self.cur_sheet.end_date_obj

		## Ensure that next_entry and end_date_obj of are same time before comparing
		if (isinstance(next_entry, dt.date) and not isinstance(next_entry, dt.datetime)) and isinstance(edo, dt.datetime):
			## See: https://docs.python.org/3.5/library/datetime.html#datetime.datetime.combine
			next_entry = dt.datetime.combine(next_entry, edo.timetz())
			next_entry2 = dt.datetime(next_entry.year, next_entry.month, next_entry.day, hour=edo.hour, minute=edo.minute, second=edo.second)
			if next_entry != next_entry2:
				print("\t(combined datetime construction) next_entry: "+get_timestamp(next_entry))
				print("\t(manual datetime construction) next_entry2: "+get_timestamp(next_entry2))
		elif isinstance(next_entry, dt.datetime) and (isinstance(edo, dt.date) and not isinstance(edo, dt.datetime)):
			self.cur_sheet.end_date_obj = dt.datetime.combine(edo, next_entry.timetz())
			edo2 = dt.datetime(edo.year, edo.month, edo.day, hour=next_entry.hour, minute=next_entry.minute, second=next_entry.second)
			if self.cur_sheet.end_date_obj != edo2:
				print("\t(combined datetime construction) end_date_obj: "+get_timestamp(self.cur_sheet.end_date_obj))
				print("\t(manual datetime construction) end_date_obj2: "+get_timestamp(edo2))

		if next_entry > self.cur_sheet.end_date_obj:
			need = True
			condition = '(#1) next_entry > end_date_obj'
			reason = {'next_entry': next_entry, 'end_date_obj': self.cur_sheet.end_date_obj}
			triggers.update({condition: reason})

		if today.strftime(DATE_FORMAT) == self.cur_sheet.end_date and next_entry.strftime(DATE_FORMAT) != self.cur_sheet.end_date:
			need = True
			condition = '(#2) today.strftime(DATE_FORMAT) == end_date and next_entry.strftime(DATE_FORMAT) != end_date'
			reason = {'today': today.strftime(DATE_FORMAT), 'next_entry': next_entry.strftime(DATE_FORMAT), 'end_date': self.cur_sheet.end_date}
			triggers.update({condition: reason})

		if today.month == self.cur_sheet.end_month and next_entry.month > self.cur_sheet.end_month:
			need = True
			condition = '(#3) today.month == end_month and next_entry.month > end_month'
			reason = {'today.month': today.month, 'next_entry.month': next_entry.month, 'end_month': self.cur_sheet.end_month}
			triggers.update({condition: reason})

		if need:
			print('\nentry_time:\t{}\nnext_entry:\t{}\n'.format(entry_time, next_entry_str))
			print("[need_newsheet_check] TRUE for:")
			for cond in triggers.keys():
				print("\tcondition:\t'{}'".format(cond))
				for key in triggers[cond].keys():
					print("\t{}:\t{}".format(key, triggers[cond][key]))

		return need

	### UPDATE [ 8/10/2020 ]
	def insert_missed_payload(self, list_of_data_dict):
		## Return True or False to indicate success vs. failure for the insertion operation
		print("[insert_missed_payload]  PROCESSING MISSED PAYLOAD  ...")
		# first_entry = list_of_data_dict[0]
		# first_entry_dt_str = extract_date_from_entry(first_entry, as_dt_object=False)
		# first_entry_dt_obj = datestr_to_datetime(first_entry_dt_str)		
		first_entry = Entry(list_of_data_dict[0], self.cur_sheet, client=self.gc, find_on_init=True)
		insert_at_row = first_entry.sheet_row
		if not insert_at_row:
			## TODO: Throw an exception here or something; indicate a serious error
			print("[insert_missed_payload]  ERROR: First entry row / insertion point could not be determined; aborting operation ...")
			return False

		payload = list()
		payload.append(first_entry.values)
		for dict_entry in list_of_data_dict[1:]:
			r = insert_at_row + len(payload)
			entry = Entry(dict_entry, self.cur_sheet, row=r, client=self.gc, find_on_init=False)
			payload.append(entry.values)

		## Attempt a batch insertion to the worksheet (calling insert_row() for each entry would be excessive)
		first_entry.wksht.insert_rows(payload, row=insert_at_row, value_input_option=VALUE_INPUT_OPTION)
		self.center_rows(insert_at_row, insert_at_row+len(payload), sheet=first_entry.wksht)
		print("[insert_missed_payload] {} rows inserted to worksheet {}\n".format(len(payload), first_entry.wksht.title))
		return True
	###

	def append_data(self, list_of_data_dict):	## Performs a batch append operation
		payload = list()
		for dict_entry in list_of_data_dict:
			entry = Entry(dict_entry, self.cur_sheet, find_on_init=False)
			payload.append(entry.values)
		try:
			self.cur_sheet.wksht.append_rows(payload, value_input_option=VALUE_INPUT_OPTION)
		except:
			## Catch an 'UNAUTHENTICATED' APIError if authentication credentials expire
			self._gc = None
			self.cur_sheet.wksht = self.gc.open(self.cur_sheet.title).worksheet(self.cur_sheet.wksht_title)
			self.cur_sheet.wksht.append_rows(payload, value_input_option=VALUE_INPUT_OPTION)
		
		last_row = self.cur_sheet.wksht.row_count
		start_row = last_row - len(payload)
		self.center_rows(start_row, end_row=last_row, sheet=self.cur_sheet.wksht)
		print("[append_data] {} rows appended to sheet {}\n".format(len(payload), self.cur_sheet.wksht.title))

	"""
	def append_data(self, list_of_data_dict):  # , missed_payload=False):
		cnt = 0
		for data_dict in list_of_data_dict:
			for date in data_dict.keys():
				level = data_dict[date]['l']
				ph = data_dict[date]['p']
				values = [date.replace(', ',',').replace(',',', '), level, ph]
				# self.cur_sheet.wksht.append_row(values, value_input_option='RAW')
				try:
					self.cur_sheet.wksht.append_row(values, value_input_option=VALUE_INPUT_OPTION)
				except:
					## Catch an 'UNAUTHENTICATED' APIError if authentication credentials expire
					self._gc = None
					self.cur_sheet.wksht = self.gc.open(self.cur_sheet.title).worksheet(self.cur_sheet.wksht_title)
					self.cur_sheet.wksht.append_row(values, value_input_option=VALUE_INPUT_OPTION)
				self.center_last_row()
				cnt += 1
		print("[append_data] {} rows appended to sheet {}\n".format(cnt, self.cur_sheet.wksht.title))
	"""

	def generate_newsheet(self, title=None):
		if title is None:
			today = get_date_today()
			tomorrow = today + today.resolution
			newsheet_date_created = tomorrow.strftime(DATE_FORMAT)
			newsheet_date_range = get_month_range(m=tomorrow.month)
			newsheet_name = NAME_FORMAT.format(newsheet_date_range)
		else:
			newsheet_name = title
			newsheet_date_range = newsheet_name.split('_')[1]
			newsheet_date_created = newsheet_date_range.split('-')[0]

		template = self.gc.open(TEMPLATE)
		sh = self.gc.copy(template.id, title=newsheet_name, copy_permissions=True)

		print("[generate_newsheet] Created sheet '{}'".format(newsheet_name))

		with open(CURSHEETFILE, 'w') as file:
			file.write(json.dumps({ 'created' : newsheet_date_created, 'range' : newsheet_date_range }))

		if 'cur_sheet' in self.__dict__.keys() and self.cur_sheet is not None:
			self.cur_sheet.changed = True  ## or, create new CurrentSheet
			print("[generate_newsheet] cur_sheet.changed = True")
		# else:
		# 	### FOR DEBUG
		# 	print(self.__dict__.keys())

		return sh



	def get_results(self, date_obj):
		## Process date as a string in FULL_DATE_FORMAT (m/d/y)
		date = sanitize_date_string(date_obj)

		if self.date_already_processed(date):
			print("[get_results] Skipping already processed date: {}".format(date))
			return 

		
		## Begins with {date}, ends with 'M': "[date], [hr]:[min]:[sec] [A/P]M"
		# date_regex = '^{}'.format(date)
		date_regex = re.compile(r'\A{}'.format(date))

		## Check if this is for a previous month's results
		# old_wksht_title = "{0}/{2}".format(*date.split('/'))
		old_m, _, old_y = date.split('/')
		if len(old_y) == 2:
			old_y = "20" + old_y
		old_wksht_title = "{}/{}".format(old_m, old_y)

		if old_wksht_title != self.cur_sheet.wksht_title:
			wksht = self.cur_sheet.sheet.worksheet(old_wksht_title)
		else:
			wksht = self.worksheet

		if wksht is not None:
			cell_list = wksht.findall(date_regex, in_column=1)

		if not cell_list:
			print("[get_results] No entries for '{}' found in worksheet '{}'".format(date, wksht.title))  #self.cur_sheet.wksht_title))
			return

		start_row = cell_list[0].row
		end_row = cell_list[-1].row

		cell_ranges = ["A{0}:C{1}".format(start_row, end_row)]
		major_dimension = 'ROWS' #'COLUMNS'
		value_render_option = 'UNFORMATTED_VALUE' #'FORMATTED_VALUE' #'FORMULA'
		date_time_render_option = 'FORMATTED_STRING' #'SERIAL_NUMBER'
		range_values = wksht.batch_get(cell_ranges, major_dimension=major_dimension, value_render_option=value_render_option, date_time_render_option=date_time_render_option)

		day_min_p = 14.0
		day_max_p = 0.0
		day_gallons = 0.0
		Q = 0.0
		row_cnt = start_row

		print("[get_results] Processing the following datetimes:")
		for values in range_values[0]:
			# print(values)
			level = float(values[1])
			ph = float(values[2])

			if ph < day_min_p:
				day_min_p = ph 
			if ph > day_max_p:
				day_max_p = ph 

			l_in_ft = level / 12.0
			Q = K * (l_in_ft ** N)  ## Q represents flow in cubic feet per second
			gal_per_interval = (Q * GAL_PER_CUBIC_FT) * 15  ## Estimated gallons that flowed over the 15 second time interval
			day_gallons += gal_per_interval

			print("[ROW {0}]\t{1} -> l: {2:3.2f}  | p: {3:3.2f}".format(row_cnt, *values))
			row_cnt += 1

		row_cnt -= 1
		if row_cnt != end_row:
			print("\n!!! Notice: row_cnt ({}) != end_row ({})\t(start_row = {})\n".format(row_cnt, end_row, start_row))

		if CROOKS_MODE:
			day_gallons /= 10.0
		self.update_results(date, day_gallons, day_min_p, day_max_p)


	def update_results(self, date, gpd, min_ph, max_ph):
		res_sheet = self.gc.open(self.cur_sheet.title).worksheet(RESULTS_SHEET_NAME)
		results = [date, gpd, "{} / {}".format(min_ph, max_ph)]
		res_sheet.append_row(results, value_input_option=VALUE_INPUT_OPTION)
		self.center_last_row(res_sheet)
		print("\n[update_results] Daily results for {0} published to Flow&pH:\n\tgpd:\t{1}\n\tmin/max ph:\t{2}\n".format(*results))
		self._dates_updated = True
		log_published_date(date)


	def get_processed_dates(self):
		res_sheet = self.gc.open(self.cur_sheet.title).worksheet(RESULTS_SHEET_NAME)
		self._dates_processed = res_sheet.col_values(1)
		if self._dates_updated:
			print("[get_processed_dates] dates_processed = {}".format(self._dates_processed))
			self._dates_updated = False
		return self._dates_processed


	def date_already_processed(self, date):
		if self._dates_updated:
			dates_processed = self.get_processed_dates()
		else:
			dates_processed = self._dates_processed
		# print("[date_already_processed] dates_processed = {}".format(dates_processed))
		if date in dates_processed:
			return True 
		return False


	def get_last_date_processed(self):
		res_sheet = self.gc.open(self.cur_sheet.title).worksheet(RESULTS_SHEET_NAME)
		dates_processed = res_sheet.col_values(1)
		return dates_processed[-1]


	@property
	def gc(self):
		""" The gspread Client instance """
		if self._gc is None:
			credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDSFILE, SCOPE)
			self._gc = gspread.authorize(credentials)
		return self._gc

	@property
	def cursheet_end_date(self):
		return self.cur_sheet.end_date_obj 

	@property
	def cursheet_end_date_str(self):
		return self.cur_sheet.end_date

	@property
	def worksheet(self):
		return self.cur_sheet.wksht
	
	


class CurrentSheet():
	def __init__(self, sm): #gc):
		self._manager = sm 
		self._gc = sm.gc
		self._created = None
		self._range = None
		self._end_date_obj = None 	# Last valid day for sheet
		self._end_date = None
		self._end_month = None
		self._end_year = None
		self._title = None
		self._url = None 
		self._user_url = None
		self._sheet = None
		self._wksht_title = None
		self._wksht = None

		self.changed = True 	# Denotes the need to read info in from file
		self.initialized = False
		
		self.load_from_file()
		# self.refresh()

		self.initialized = True


	def load_from_file(self):
		if self.changed:
			if not os.path.exists(CURSHEETFILE):
				print("[CurrentSheet.__init__] CURSHEETFILE does not exist: " + CURSHEETFILE + "\t(creating now)")
				today = get_date_today()
				self._created = today.strftime(DATE_FORMAT)
				self._range = get_month_range()

				with open(CURSHEETFILE, 'a+') as new_file:
					new_file.write(json.dumps({ 'created' : self._created, 'range' : self._range }))

			else:
				with open(CURSHEETFILE) as json_file:
					data = json.loads(json_file.read())
				self._created = data['created']
				self._range = data['range']

			end_m, end_y = (self._range.split('-')[1]).split('/')
			end_m = int(end_m)
			end_y = int(end_y)
			end_d = calendar.monthrange(end_y, end_m)[1]  # returns weekday of first day of the month and number of days in month, for the specified year and month.
			
			# self._end_date_obj = dt.date(end_y, end_m, end_d) 	# (year, month, day)
			self._end_date_obj = dt.datetime(end_y, end_m, end_d, hour=23, minute=59, second=59)

			self.refresh()

			self.changed = False

	def refresh(self):
		self._title = None
		self._url = None 
		self._sheet = None
		self._wksht_title = None
		self._wksht = None

		self._title = NAME_FORMAT.format(self._range)
		today = get_datetime_now()
		if today > self._end_date_obj:
			self._wksht_title = self._range.split('-')[1]
		else:
			self._wksht_title = today.strftime(DATE_FORMAT)
		self._refresh_in_progress = True
		sh = self.sheet

		if not sh:
			print("[refresh] Sheet '{}' not found!".format(self._title))
			self._refresh_in_progress = False
			return

		new_wksht_added = False
		wksht_list = None
		api_tries = 0
		while wksht_list is None:
			try:
				wksht_list = sh.worksheets()
			except gspread.exceptions.APIError:
				print(".", end="")
				wksht_list = None
				api_tries += 1
				time.sleep(api_tries)
			if api_tries == 6:
				print("\n[refresh] MAX API RETRIES FAILED FOR 'sh.worksheets()' -- CRITICAL ERROR\n")
				sys.exit()
		print("\n")

		if not self._wksht_title in [w.title for w in wksht_list]:  # sh.worksheets()]:
			try:
				sh.add_worksheet(title=self._wksht_title, rows="1", cols="3")
				print("[refresh] Added new worksheet '{}'".format(self._wksht_title))
				new_wksht_added = True
			except gspread.exceptions.APIError:
				print("[refresh] Worksheets: {}".format(wksht_list))  # sh.worksheets()))
			
		self._wksht = sh.worksheet(self._wksht_title)
		url = self.url 
		self._sheet_id = self._wksht._properties['sheetId']

		if new_wksht_added:
			print("New sheet URL: {}\n".format(self.user_url))
			for i in range(len(col_headers)):
				self._wksht.update_cell(1, i+1, col_headers[i])
			self._wksht.format("A1:C1", {
				"textFormat": {
						"fontSize": 11
				}, 
				"horizontalAlignment": "CENTER", 
				"borders": {
					"bottom": {
						"style": "SOLID_MEDIUM"
					}
				}
			})
			
			# if REQUEST_BATCH_COLUMN_FORMATTING:
			### https://stackoverflow.com/questions/57177998/gspread-column-sizing
			### https://github.com/burnash/gspread/blob/master/gspread/models.py#L131
			resize_cols_request_body = {
				"requests": [
					{
						"updateDimensionProperties": {
							"range": {
								"sheetId": self._sheet_id,
								"dimension": "COLUMNS",
								"startIndex": 0,
								"endIndex": 1
							},
							"properties": {
								"pixelSize": 180
							},
							"fields": "pixelSize"
						}
					},  {
						"updateSpreadsheetProperties": {
							"properties": {
								"defaultFormat": {
									"horizontalAlignment": "CENTER"
								}
							},
							"fields": "defaultFormat"
						}
					},  {
						"updateDimensionProperties": {
							"range": {
								"sheetId": self._sheet_id,
								"dimension": "COLUMNS",
								"startIndex": 1,
								"endIndex": 3
							},
							"properties": {
								"pixelSize": 130
							},
							"fields": "pixelSize"
						}
					},  {
						"updateSpreadsheetProperties": {
							"properties": {
								"defaultFormat": {
									"horizontalAlignment": "CENTER"
								}
							},
							"fields": "defaultFormat"
						}
					}
				]
			}
			try:
				res = sh.batch_update(resize_cols_request_body)
			except Exception as e:
				print(e)
				sh.del_worksheet(self._wksht)
				sys.exit()

		self._refresh_in_progress = False

	@property
	def sheet(self):
		if self.changed and self.initialized and not self._refresh_in_progress:
			print('[CurrentSheet.sheet] CHANGED: Calling load_from_file()')
			self.load_from_file()
		if self._sheet is None:
			try:
				self._sheet = self._gc.open(self._title)
			except gspread.exceptions.SpreadsheetNotFound:
				print("[CurrentSheet.sheet] Opening sheet {} raised an Exception: SpreadsheetNotFound".format(self._title))
				# self._sheet = None
				self._sheet = self._manager.generate_newsheet(title=self._title)
		return self._sheet

	@property
	def wksht(self):
		if self.changed and self.initialized: # and not self._refresh_in_progress:
			print('[CurrentSheet.wksht] CHANGED: Calling load_from_file()')
			self.load_from_file()
		if not self._wksht_title == get_datetime_now().strftime(DATE_FORMAT):
			self.refresh()
		return self._wksht

	@wksht.setter
	def wksht(self, value):
		self._wksht = value 
		print('[CurrentSheet.wksht] Updated to: {}'.format(value))

	@property
	def end_date_obj(self):
		if self.changed and self.initialized: # and not self._refresh_in_progress:
			print('[CurrentSheet.end_date_obj] CHANGED: Calling load_from_file()')
			self.load_from_file()
		# if self._end_date_obj is None:
		return self._end_date_obj

	@end_date_obj.setter
	def end_date_obj(self, value):
		self._end_date_obj = value
		print('[CurrentSheet.end_date_obj] Updated to: {}'.format(value))

	@property
	def end_date(self):
		""" String """
		if self.changed and self.initialized: # and not self._refresh_in_progress:
			print('[CurrentSheet.end_date] CHANGED: Calling load_from_file()')
			self.load_from_file()
		self._end_date = self.end_date_obj.strftime(DATE_FORMAT)
		return self._end_date

	@property
	def created(self):
		if self.changed and self.initialized: # and not self._refresh_in_progress:
			print('[CurrentSheet.created] CHANGED: Calling load_from_file()')
			self.load_from_file()
		return self._created

	@property
	def daterange(self):
		if self.changed and self.initialized: # and not self._refresh_in_progress:
			print('[CurrentSheet.daterange] CHANGED: Calling load_from_file()')
			self.load_from_file()
		return self._range

	@property
	def end_month(self):
		if self.changed and self.initialized: # and not self._refresh_in_progress:
			print('[CurrentSheet.end_month] CHANGED: Calling load_from_file()')
			self.load_from_file()
		return self._end_date_obj.month 

	@property
	def end_year(self):
		if self.changed and self.initialized: # and not self._refresh_in_progress:
			print('[CurrentSheet.end_year] CHANGED: Calling load_from_file()')
			self.load_from_file()
		return self._end_date_obj.year 

	@property
	def title(self):
		if self.changed and self.initialized: # and not self._refresh_in_progress:
			print('[CurrentSheet.title] CHANGED: Calling load_from_file()')
			self.load_from_file()
		return self._title
	
	@property
	def url(self):
		if self.changed and self.initialized and not self._refresh_in_progress:
			print('[CurrentSheet.url] CHANGED: Calling load_from_file()')
			self.load_from_file()
		self._url = WORKSHEET_DRIVE_URL % (self._sheet.id, self._wksht._properties['sheetId'])
		# print(self.user_url)
		return self._url

	@property
	def user_url(self):
		self._user_url = ACCESSIBLE_SHEET_URL % (self._sheet.id, self._wksht._properties['sheetId'])
		if not os.path.exists(SHEET_URL_FILE):
			with open(SHEET_URL_FILE, 'a+') as url_file:
				url_file.write(self._user_url)
		else:
			with open(SHEET_URL_FILE, 'w') as url_file:
				url_file.write(self._user_url)
		return self._user_url
	
	@property
	def wksht_title(self):
		if self.changed and self.initialized: # and not self._refresh_in_progress:
			print('[CurrentSheet.wksht_title] CHANGED: Calling load_from_file()')
			self.load_from_file()
		return self._wksht_title
	
	
	
	
	


	