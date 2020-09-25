import os
import re
import sys
import json
import time
import gspread
import inspect
import datetime as dt
import calendar
from oauth2client.service_account import ServiceAccountCredentials

try:
	if os.getcwd().split('/')[-1] == 'watershedpi':
		from flowreport import flowreport
	else:
		from watershedpi.flowreport import flowreport
except:
	fp_path = os.path.join(os.environ['HOME'], 'watershedpi', 'flowreport')
	print("[sheet_manager]  Appending '{}' to sys.path".format(fp_path))
	sys.path.append(fp_path)
	if os.getcwd().split('/')[-1] == 'watershedpi':
		from flowreport import flowreport
	else:
		from watershedpi.flowreport import flowreport

ON_DEV_BRANCH = False 	## CHANGE ME to False before running in the field
SIMULATE_END_DATE = ON_DEV_BRANCH and True #False
SIM_TIMEDELTA_DAYS = 25
SIM_TIMEDELTA_HOURS = 21
SIM_TIMEDELTA_MINS = 12

# REQUEST_BATCH_COLUMN_FORMATTING = True #False
CROOKS_MODE = False 	## If set to True, will reduce daily flow results by a factor of 10 

TEMPLATE = "FlumeDataTemplate"
RESULTS_SHEET_NAME = "Flow&pH"
# MASTER_SPREADSHEET = "FlowReport"
# MASTER_SHEET_NAME = "Flow"    <-- Moved to flowreport.py

CREDSFILE = os.path.join(os.environ['HOME'], "watershed_private.json")
CURSHEETFILE = os.path.join(os.environ['HOME'], "cur_sheet.json")
PUBLISHED_DATES_FILE = os.path.join(os.environ['HOME'], "published_dates.txt")
SHEET_URL_FILE = os.path.join(os.environ['HOME'], "sheet_urls.txt")

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

MEASUREMENT_INTERVAL = 15   ## <-- 3 sec for DEV branch work, else set to 15 seconds

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
		today += dt.timedelta(days=SIM_TIMEDELTA_DAYS, hours=SIM_TIMEDELTA_HOURS, minutes=SIM_TIMEDELTA_MINS)
	return today

def get_datetime_now():
	now = dt.datetime.now()
	## ... add some timedelta before returning to simulate future datetimes (for DEBUG) ...
	if SIMULATE_END_DATE:
		now += dt.timedelta(days=SIM_TIMEDELTA_DAYS, hours=SIM_TIMEDELTA_HOURS, minutes=SIM_TIMEDELTA_MINS)
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
		count = 0
		for line in f:
			count += 1
			pass
		if count == 0:
			return None 
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
	if ampm == 'PM':
		if hr != 12:
			hr += 12
	elif ampm == 'AM':
		if hr == 12:
			hr = 0
	hr %= 24
	dt_obj = dt.datetime(int(y), int(m), int(d), hour=hr, minute=mn, second=sc)
	return dt_obj
###

### UPDATE [ 8/11/2020 ]
def get_spreadsheet_title_for_datestr(date_str):
	entry_month = int(date_str.split(',')[0].split('/')[0])
	entry_date_range = get_month_range(m=entry_month)
	entry_sheet_name = NAME_FORMAT.format(entry_date_range)
	return entry_sheet_name

def get_worksheet_title_for_datestr(date_str):
	m, _, y = date_str.split(',')[0].split('/')
	if m[0] == '0':
		m = m[1:] 	  ## Trim leading zero
	if len(y) == 2:
		y = "20" + y  ## Add century
	wksht_title = "{}/{}".format(m, y)	## e.g., "9/2020"
	return wksht_title

def all_rows_consecutive(int_list): 
    return sorted(int_list) == list(range(min(int_list), max(int_list)+1)) 
###

### UPDATE [ 8/10/2020 ]
class Entry():
	def __init__(self, entry_dict, cur_sheet, row=0, client=None, find_row_on_init=True):
		## NOTE: cur_sheet should be a gspread.models.Spreadsheet object, not a CurrentSheet object!
		self.dict = entry_dict
		self.dt_str = list(entry_dict.keys())[0]
		self.dt_obj = datestr_to_datetime(self.dt_str)

		if isinstance(cur_sheet, gspread.models.Spreadsheet):
			self.sheet = cur_sheet
		elif isinstance(cur_sheet, CurrentSheet):
			self.sheet = cur_sheet.sheet 
		else:
			self.sheet = None
		self._wksht = None
		self.gc = client 	## gspread client instance
		
		self._next_entry = None
		self._sheet_row = row
		if find_row_on_init:
			self._sheet_row = self.sheet_row

	def __str__(self):
		return self.dt_str

	def __repr__(self):
		return self.dt_str

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
	def sheet_id(self):
		return self.wksht._properties['sheetId']
	
	@property
	def wksht(self):
		## TODO: Perform check for needing to open an older workshet for a previous month (see get_results(), refresh(), etc.)
		## TODO: Insert try-except case for when gspread client (`self.gc`) needs to call `open(sheet_title).worksheet(worksheet_title)` after authentication creds expire
		# return self.sheet.wksht
		if self._wksht is None:
			m, _, y = self.date_str.split('/')
			if m[0] == '0':
				m = m[1:]
			if len(y) == 2:
				y = "20" + y 
			wksht_title = "{}/{}".format(m, y)	## e.g., "9/2020"
			try:
				self._wksht = self.sheet.worksheet(wksht_title)
			except gspread.exceptions.WorksheetNotFound:
				self.create_worksheet(wksht_title)
			except Exception as e:
				try:
					self.sheet = self.gc.open(self.sheet.title)
				except Exception as ee:
					credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDSFILE, SCOPE)
					self.gc = gspread.authorize(credentials)
					self.sheet = self.gc.open(self.sheet.title)
				finally:
					try:
						self._wksht = self.sheet.worksheet(wksht_title)
					except gspread.exceptions.WorksheetNotFound:
						self.create_worksheet(wksht_title)
				"""
				try:
					self._wksht = self.gc.open(self.sheet.title).worksheet(wksht_title)
				except:
					credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDSFILE, SCOPE)
					self.gc = gspread.authorize(credentials)
					self.sheet = self.gc.open(self.sheet.title)
					try:
						self._wksht = self.sheet.worksheet(wksht_title)
					except gspread.exceptions.WorksheetNotFound:
						self.create_worksheet(wksht_title)
				"""
		return self._wksht
	
	@property
	def next_entry(self):
		## Should be a dict of form:  { next_row_number : next_row_datetime_obj }
		if self._next_entry is None:
			self._sheet_row = self.sheet_row
		return self._next_entry
	
	@next_entry.setter
	def next_entry(self, value):
		if isinstance(value, dict):
			self._next_entry = value 
	
	@property
	def sheet_row(self):
		first_row_for_day = self.wksht.row_count
		first_datetime_for_day = None 
		if self._sheet_row is None or self._sheet_row < 2:
			## Search current worksheet for correct row position for this entry (according to date-time)
			date_regex = re.compile(r'\A{}'.format(self.dt_obj.strftime(FULL_DATE_FORMAT)))
			cell_list = self.wksht.findall(date_regex, in_column=1)
			print("[Entry.sheet_row]  Number of cells matching '{}' found:  {}".format(date_regex, len(cell_list)))

			if len(cell_list) == 0:
				first_datetime_for_day = self.dt_obj 
			else:
				for i in range(len(cell_list)-1):
					this_cell = cell_list[i]
					# print("\t-->  this_cell.value = '{}'".format(this_cell.value))
					# this_date = datestr_to_datetime(this_cell.value)  ## e.g., "10/3/2020, 09:41:23 PM"
					this_date = dt.datetime.strptime(this_cell.value.replace(', ',','), ENTRY_TIME_FORMAT.replace('-',''))

					if i == 0:
						first_row_for_day = this_cell.row 
						first_datetime_for_day = this_date

					if this_date < self.dt_obj:
						next_cell = cell_list[i+1]
						# print("\t-->  next_cell.value = '{}'".format(next_cell.value))
						# next_date = datestr_to_datetime(next_cell.value)
						next_date = dt.datetime.strptime(next_cell.value.replace(', ',','), ENTRY_TIME_FORMAT.replace('-',''))

						if self.dt_obj < next_date:
							self._sheet_row = next_cell.row 
							self._next_entry = { (next_cell.row+1) : next_date } 	## Inserting this Entry will bump previous value down 1 row
							break

				### UPDATED 8/28/20
				if self._sheet_row is None or self._sheet_row < 2:
					## Entries were found for this date, but all were earlier than this datetime
					if first_datetime_for_day is not None and first_datetime_for_day != self.dt_obj:  
						## Latest entry will still be in 'next_cell'
						self._sheet_row = next_cell.row + 1
						try:
							following_cell = self.wksht.cell(self._sheet_row, 1)
							self._next_entry = { (self._sheet_row+1) : dt.datetime.strptime(following_cell.value.replace(', ',','), ENTRY_TIME_FORMAT.replace('-','')) }
						except:
							## No cell exists at this row, thus we're at the end of the worksheet
							self._next_entry = { (self._sheet_row+1) : (self.dt_obj + dt.timedelta(seconds=int(MEASUREMENT_INTERVAL*1.25))) }
				###

		else:
			## If a row number was provided at instantiation, create a `next_entry` dict containing superficial data
			if self._next_entry is None:
				self._next_entry = { (self._sheet_row+1) : (self.dt_obj + dt.timedelta(seconds=int(MEASUREMENT_INTERVAL*1.25))) }


		# if first_datetime_for_day is not None and first_datetime_for_day == self.dt_obj: 	## No entries were found for this date...



		if self._sheet_row is None or self._sheet_row < 2:
			## Search the following day on the current worksheet for correct row position for this entry (according to date-time)
			date_regex = re.compile(r'\A{}'.format((self.dt_obj + dt.timedelta(days=1)).strftime(FULL_DATE_FORMAT)))
			cell_list = self.wksht.findall(date_regex, in_column=1)
			print("[Entry.sheet_row]  Number of cells matching '{}' found:  {}".format(date_regex, len(cell_list)))

			if len(cell_list) > 0:
				if first_datetime_for_day is not None and first_datetime_for_day == self.dt_obj: 	## No entries were found for this date... insert at first row of next date
					self._sheet_row = cell_list[0].row 
					self._next_entry = { (cell_list[0].row+1) : dt.datetime.strptime(cell_list[0].value.replace(', ',','), ENTRY_TIME_FORMAT.replace('-','')) }
				else:
					for i in range(len(cell_list)-1):
						this_cell = cell_list[i]
						this_date = dt.datetime.strptime(this_cell.value.replace(', ',','), ENTRY_TIME_FORMAT.replace('-',''))

						if this_date < self.dt_obj:
							next_cell = cell_list[i+1]
							next_date = dt.datetime.strptime(next_cell.value.replace(', ',','), ENTRY_TIME_FORMAT.replace('-',''))

							if self.dt_obj < next_date:
								self._sheet_row = next_cell.row 
								self._next_entry = { (next_cell.row+1) : next_date } 	## Inserting this Entry will bump previous value down 1 row
								break

		## TODO: Handle edge case: what if no entries found for this date or the following date? Should the entire month be scanned (perhaps w/ binary search)?
		# if first_datetime_for_day

		if self._sheet_row is None or self._sheet_row < 2:
			# if first_row_for_day < 2:
			# 	first_row_for_day += 1
			if first_row_for_day == 0:
				first_row_for_day = 1
			self._sheet_row = first_row_for_day
			self._next_entry = { (first_row_for_day+1) : first_datetime_for_day }
			print("[Entry.sheet_row]  ERROR: No suitable row found for later than entry date-time '{}'  -->  assigning the Entry date's first row index instead ({})".format(self.dt_str, self._sheet_row))	

		if self._sheet_row is None or self._sheet_row < 2:
			self._sheet_row = self.wksht.row_count
			self._next_entry = { (self._sheet_row+1) : (self.dt_obj + dt.timedelta(seconds=int(MEASUREMENT_INTERVAL*2.5))) }
			print("[Entry.sheet_row]  ERROR: No suitable row found for entry date-time '{}'  -->  assigning the Worksheet's last row instead ({})".format(self.dt_str, self._sheet_row))	
		return self._sheet_row
	

	def create_worksheet(self, wksht_title):
		self.sheet.add_worksheet(title=wksht_title, rows="1", cols="3")
		print("[Entry::create_worksheet] Added new worksheet '{}'".format(wksht_title))
		self._wksht = self.sheet.worksheet(wksht_title)
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
		## https://stackoverflow.com/questions/57177998/gspread-column-sizing
		## https://github.com/burnash/gspread/blob/master/gspread/models.py#L131
		resize_cols_request_body = {
			"requests": [
				{
					"updateDimensionProperties": {
						"range": {
							"sheetId": self._wksht._properties['sheetId'],
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
							"sheetId": self._wksht._properties['sheetId'],
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
		res = self.sheet.batch_update(resize_cols_request_body)
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
		# try:
		# 	sheet.format(new_row_range, { "horizontalAlignment": "CENTER", "fontSize": 11 })
		# except:  # gspread.exceptions.APIError  <-- 'code': 400
		sheet.format(new_row_range, { "horizontalAlignment": "CENTER", "textFormat": { "fontSize": 11, }, } )

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

	### UPDATE [ 8/11/2020 ]
	def get_spreadsheet_for_entry(self, entry_dict, entry_sheet_title=None):
		## Returns a gspread.models.Spreadsheet object reference 
		entry_datestr = extract_date_from_entry(entry_dict, as_dt_object=False)
		if entry_sheet_title is None:
			entry_sheet_title = get_spreadsheet_title_for_datestr(entry_datestr)
		if entry_sheet_title == self.cur_sheet.sheet.title:
			entry_sheet = self.cur_sheet.sheet
		else:
			print(" >> Entry '{}' using different Spreadsheet than SheetManager.cur_sheet ('{}'):  '{}'".format(entry_datestr, self.cur_sheet.sheet.title, entry_sheet_title))
			try:
				entry_sheet = self.gc.open(entry_sheet_title)
			except gspread.exceptions.SpreadsheetNotFound:
				entry_sheet = self.generate_newsheet(title=entry_sheet_title, update_cur_sheet=False)
			except Exception as e:
				## Catch an 'UNAUTHENTICATED' APIError if authentication credentials expire
				self._gc = None
				try:
					entry_sheet = self.gc.open(entry_sheet_title)
				except gspread.exceptions.SpreadsheetNotFound:
					entry_sheet = self.generate_newsheet(title=entry_sheet_title, update_cur_sheet=False)
		return entry_sheet
	###

	### UPDATE [ 8/10/2020 ]
	def insert_missed_payload(self, list_of_data_dict):
		## Return True or False to indicate success vs. failure for the insertion operation
		print("[insert_missed_payload]  PROCESSING MISSED PAYLOAD  ...")

		## TODO: Check that the date range of `self.cur_sheet` aligns with the first entry's date!
		entry_sheet = self.get_spreadsheet_for_entry(list_of_data_dict[0])
		first_entry = Entry(list_of_data_dict[0], entry_sheet, client=self.gc, find_row_on_init=True)

		insert_at_row = first_entry.sheet_row
		if not insert_at_row:
			## TODO: Throw an exception here or something; indicate a serious error
			print("[insert_missed_payload]  ERROR: First entry row / insertion point could not be determined; aborting operation ...")
			return False
		
		## TODO: Need to keep track of all created Entry instances here?
		first_wksht = first_entry.wksht
		worksheet_map = { first_wksht.title : first_wksht }		## Maps worksheet title (str) --> gspread.models.Worksheet
		worksheet_entries_dict = { first_wksht.title : [first_entry] }  ## Maps worksheet title --> list of associated entries
		print(" >> Adding new worksheet dict key:  '{}'".format(first_wksht.title))

		prev_entry = first_entry
		for dict_entry in list_of_data_dict[1:]:
			needs_row_search = False   ## For the `find_row_on_init` flag of the `Entry` constructor
			row_idx = 0
			entry_datestr = extract_date_from_entry(dict_entry, as_dt_object=False)
			entry_sheet_title = get_spreadsheet_title_for_datestr(entry_datestr)
			entry_wksht_title = get_worksheet_title_for_datestr(entry_datestr)

			if entry_sheet_title != entry_sheet.title:  ## Checking if consecutive entries require different Spreadsheets
				print(">>> Switching Spreadsheet for subsequent payload entry (old: '{}', new: '{}')".format(entry_sheet.title, entry_sheet_title))
				entry_sheet = self.get_spreadsheet_for_entry(dict_entry, entry_sheet_title=entry_sheet_title)
				needs_row_search = True
			else:
				if entry_wksht_title != prev_entry.wksht.title:  ## Checking if consecutive entries belong to the same Worksheet
					print(">>> Switching Worksheet for subsequent payload entry (old: '{}', new: '{}')".format(prev_entry.wksht.title, entry_wksht_title))
					needs_row_search = True
				else:
					## Convert entry datetime string to a datetime object for comparison against the previous entry's replaced row (`next_entry`)
					entry_dt_obj = dt.datetime.strptime(entry_datestr.replace(', ',','), ENTRY_TIME_FORMAT.replace('-',''))

					if prev_entry.dt_obj < entry_dt_obj:
						## Because the prev_entry and this entry belong to the same Spreadsheet && Worksheet, 
						## this entry's insertion row can be determined using the prev_entry's replaced row index
						prevs_next_entry = prev_entry.next_entry  ## Should be a dict of form:  { next_row_number : next_row_datetime_obj }
						prevs_next_entry_row = int(list(prevs_next_entry.keys())[0])

						if prevs_next_entry[prevs_next_entry_row] is not None and entry_dt_obj < prevs_next_entry[prevs_next_entry_row]:
							row_idx = prevs_next_entry_row 	## Should be equivalent to (prev_entry.row + 1)
							# prev_entry.next_entry = { prevs_next_entry_row+1 : prevs_next_entry[prevs_next_entry_row] }
							# consecutive_rows = False
						else:
							needs_row_search = True 
					else:
						needs_row_search = True

			entry = Entry(dict_entry, entry_sheet, row=row_idx, client=self.gc, find_row_on_init=needs_row_search)
			wed_key = entry.wksht 
			if wed_key.title not in worksheet_map.keys():
				worksheet_map[wed_key.title] = wed_key 
			if wed_key.title not in worksheet_entries_dict.keys():
				print(" >> Adding new worksheet dict key:  '{}'".format(wed_key.title))
				worksheet_entries_dict[wed_key.title] = list()
			worksheet_entries_dict[wed_key.title].append(entry)
			prev_entry = entry 

		for ws_title in worksheet_entries_dict.keys():	 ## Dictionary:  { Worksheet.title : [ Entry, Entry, ... ] }
			ws = worksheet_map[ws_title]   ## ws: The corresponding gspread.models.Worksheet instance
			worksheet_entries_dict[ws_title].sort(key=lambda x: x.dt_obj)	## Will sort Entry objects by datetime (in-place)
			# print("\ndict( {} : {} )".format(ws_title, worksheet_entries_dict[ws_title]))

			# all_rows_consecutive = True
			row_indices = [e.sheet_row for e in worksheet_entries_dict[ws_title]]
			if all_rows_consecutive(row_indices) or (len(row_indices) > 0 and (row_indices.count(row_indices[0]) == len(row_indices))) or (len(set(row_indices)) < 3):  # == 1):
				## Perform a batch insertion to the Worksheet if all entry rows are consecutive (can share the same starting row index)
				print("(all rows consecutive for '{}' Worksheet entries)\n".format(ws_title))
				insert_at_row = min(row_indices)
				if insert_at_row == 1:
					## If first entries for this month, cannot insert before the column headers in row 1; thus, append after row 1
					ws.append_rows([e.values for e in worksheet_entries_dict[ws_title]], value_input_option=VALUE_INPUT_OPTION, 
									insert_data_option="INSERT_ROWS", table_range="A1:C1")
				
				## TODO: Also check if row is the very last of the worksheet's! In that case, append to the end!
				elif insert_at_row >= ws.row_count:
					ws.append_rows([e.values for e in worksheet_entries_dict[ws_title]], value_input_option=VALUE_INPUT_OPTION)

				else:
					ws.insert_rows([e.values for e in worksheet_entries_dict[ws_title]], row=insert_at_row, value_input_option=VALUE_INPUT_OPTION)
				self.center_rows(insert_at_row, end_row=max(row_indices), sheet=ws)
			else:
				nonconsec_rows = list()
				# print("row_indices: {}\nnonconsec_rows: {}\n".format(row_indices, nonconsec_rows))
				all_entries = sorted(worksheet_entries_dict[ws_title], key=lambda x: x.sheet_row)
				for i,e in enumerate(all_entries):
					if e == all_entries[-1]:
						break
					if (all_entries[i+1].sheet_row - e.sheet_row) > 1:
						for ee in all_entries[i+1:]:
							if ee not in nonconsec_rows:
								nonconsec_rows.append(ee) ##.sheet_row)
							if ee.sheet_row in row_indices:
								row_indices.remove(ee.sheet_row)
				print("row_indices: {}\nnonconsec_rows: {}\n".format(row_indices, [ee.sheet_row for ee in nonconsec_rows]))

				grouped_entries = [e for e in worksheet_entries_dict[ws_title] if e not in nonconsec_rows]
				## Batch insert first largest grouping of consecutive entries
				insert_at_row = min(row_indices)
				if insert_at_row == 1:
					## If first entries for this month, cannot insert before the column headers in row 1; thus, append after row 1
					ws.append_rows([e.values for e in grouped_entries], value_input_option=VALUE_INPUT_OPTION, 
									insert_data_option="INSERT_ROWS", table_range="A1:C1")

				## TODO: Also check if row is the very last of the worksheet's! In that case, append to the end!
				elif insert_at_row >= ws.row_count:
					ws.append_rows([e.values for e in grouped_entries], value_input_option=VALUE_INPUT_OPTION)

				else:
					ws.insert_rows([e.values for e in grouped_entries], row=insert_at_row, value_input_option=VALUE_INPUT_OPTION)
				self.center_rows(insert_at_row, end_row=(insert_at_row+len(grouped_entries)), sheet=ws)

				for e in nonconsec_rows:
					## Insert non-consecutive entries individually (WARNING: May incur an APIError for too many requests)
					if e.sheet_row == 1:
						e.wksht.append_rows([e.values], value_input_option=VALUE_INPUT_OPTION, 
									insert_data_option="INSERT_ROWS", table_range="A1:C1")

					## TODO: Also check if row is the very last of the worksheet's! In that case, append to the end!
					elif e.sheet_row >= e.wksht.row_count:
						e.wksht.append_rows([e.values], value_input_option=VALUE_INPUT_OPTION)

					else:
						e.wksht.insert_rows([e.values], row=e.sheet_row, value_input_option=VALUE_INPUT_OPTION)
					self.center_row(e.sheet_row, sheet=e.wksht)

			print("[insert_missed_payload] {} rows inserted to worksheet '{}'\n".format(len(worksheet_entries_dict[ws_title]), ws_title))

		"""  Previous implementation:
		payload = list()
		payload.append(first_entry.values)

		## TODO: Check for & handle month/worksheet roll-overs within a group of payload entries
		for dict_entry in list_of_data_dict[1:]:
			r = insert_at_row + len(payload)
			entry_sheet_title = get_spreadsheet_title_for_datestr(extract_date_from_entry(dict_entry, as_dt_object=False))
			if entry_sheet_title != entry_sheet.title:
				print(">>> Switching Spreadsheet for subsequent payload entry (old: '{}', new: '{}')".format(entry_sheet.title, entry_sheet_title))
				entry_sheet = self.get_spreadsheet_for_entry(dict_entry, entry_sheet_title=entry_sheet_title)
			
			entry = Entry(dict_entry, entry_sheet, row=r, client=self.gc, find_row_on_init=False)
			payload.append(entry.values)

		## Attempt a batch insertion to the worksheet (calling insert_row() for each entry would be excessive)
		try:
			first_entry.wksht.insert_rows(payload, row=insert_at_row, value_input_option=VALUE_INPUT_OPTION)
		except:
			## Catch an 'UNAUTHENTICATED' APIError if authentication credentials expire
			self._gc = None
			first_entry.wksht = self.gc.open(first_entry.sheet.title).worksheet(first_entry.sheet.wksht_title)
			first_entry.wksht.insert_rows(payload, row=insert_at_row, value_input_option=VALUE_INPUT_OPTION)
		self.center_rows(insert_at_row, end_row=(insert_at_row+len(payload)), sheet=first_entry.wksht)
		print("[insert_missed_payload] {} rows inserted to worksheet {}\n".format(len(payload), first_entry.wksht.title))
		"""

		return True
	###

	def append_data(self, list_of_data_dict):	## Performs a batch append operation
		payload = list()
		for dict_entry in list_of_data_dict:
			entry = Entry(dict_entry, self.cur_sheet, find_row_on_init=False)
			payload.append(entry.values)
		#try:
		self.cur_sheet.wksht.append_rows(payload, value_input_option=VALUE_INPUT_OPTION)
		#except:
		#	## Catch an 'UNAUTHENTICATED' APIError if authentication credentials expire
		#	self._gc = None
		#	self.cur_sheet.wksht = self.gc.open(self.cur_sheet.title).worksheet(self.cur_sheet.wksht_title)
		#	self.cur_sheet.wksht.append_rows(payload, value_input_option=VALUE_INPUT_OPTION)
		
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

	def generate_newsheet(self, title=None, update_cur_sheet=True):
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

		if update_cur_sheet:
			with open(CURSHEETFILE, 'w') as file:
				file.write(json.dumps({ 'created' : newsheet_date_created, 'range' : newsheet_date_range }))

			if 'cur_sheet' in self.__dict__.keys() and self.cur_sheet is not None:
				self.cur_sheet.changed = True  ## or, create new CurrentSheet
				print("[generate_newsheet] cur_sheet.changed = True")

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
			gal_per_interval = (Q * GAL_PER_CUBIC_FT) * MEASUREMENT_INTERVAL  ## Estimated gallons that flowed over the 15 second time interval
			day_gallons += gal_per_interval

			print("[ROW {0}]\t{1} -> l: {2:3.2f}  | p: {3:3.2f}".format(row_cnt, *values))
			row_cnt += 1

		row_cnt -= 1
		if row_cnt != end_row:
			print("\n!!! Notice: row_cnt ({}) != end_row ({})\t(start_row = {})\n".format(row_cnt, end_row, start_row))

		if CROOKS_MODE:
			day_gallons /= 10.0

		print("[get_results] Calling update_results ...")
		self.update_results(date, day_gallons, day_min_p, day_max_p)

		print("[get_results] Calling update_master_sheet_results ...")
		# self.update_master_sheet_results(date, day_gallons)
		try:
			flowreport.update_master_sheet_results(date, day_gallons)
		except AttributeError:
			## Should auto-handle upgrade of gspread pip package for attribute "service_account"
			flowreport.update_master_sheet_results(date, day_gallons)


	def update_results(self, date, gpd, min_ph, max_ph):
		res_sheet = self.gc.open(self.cur_sheet.title).worksheet(RESULTS_SHEET_NAME)
		results = [date, gpd, "{} / {}".format(min_ph, max_ph)]
		res_sheet.append_row(results, value_input_option=VALUE_INPUT_OPTION)
		self.center_last_row(res_sheet)
		print("\n[update_results] Daily results for {0} published to Flow&pH:\n\tgpd:\t{1}\n\tmin/max ph:\t{2}\n".format(*results))
		self._dates_updated = True
		log_published_date(date)

	"""
	#### UPDATE [9/21/20]
	def update_master_sheet_results(self, date, gpd):
		print("(SheetManager.update_master_sheet_results invoked)")
		# master_sheet_name = "FlowReport"
		# master_worksheet_name = "Flow"
		# master_sheet = self.gc.open(master_sheet_name).worksheet(master_worksheet_name)
		master_sheet = self.gc.open(MASTER_SPREADSHEET).worksheet(MASTER_SHEET_NAME)
		master_sheet.append_row((date, gpd), value_input_option=VALUE_INPUT_OPTION)
		self.center_last_row(sheet=master_sheet)
	####
	"""

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
		frame = inspect.stack()
		print("\t(wksht.setter called from [function '{}', line {}], which was called from [function '{}', line {}]\n)".format(frame[1].function, frame[1].lineno, frame[2].function, frame[2].lineno))

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
	
	
	
	
	


	
