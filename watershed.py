#!/usr/bin/python3

### NOTE: Default python3 version on watershedpi is python3.5, no f-string support!

import os
import sys
import ast
import time
import math
import urllib
import requests
import busio
import board
import random
import itertools
import traceback
import statistics
import datetime as dt
import RPi.GPIO as GPIO
from adafruit_ads1x15 import ads1115, ads1015, analog_in

import sheet_manager

###############################################################################
## CONSTANTS
###############################################################################

ON_DEV_BRANCH = sheet_manager.ON_DEV_BRANCH

DRY_RUN = False 	## Will skip sheet_manager.append_data() call; SET TO FALSE BEFORE DEPLOYMENT
UPDATE_BASHRC = False #True
TESTING = False 	## SET TO FALSE BEFORE DEPLOYMENT
USE_GAS = False

### UPDATE [ 8/7/2020 ]
import json
CHECK_NETWORK_EACH_ITERATION = False
PERSIST_OFFLINE = True
FAILED_PAYLOADS_FILE = os.path.join(os.environ['HOME'], "missed_payloads.txt")
NUM_PAYLOADS_FILE = os.path.join(os.environ['HOME'], "num_payloads.txt")
MAX_FAILED_PAYLOADS = 20
total_failed_payloads = 0
online = False
###
ERROR_LOGFILE = os.path.join(os.environ['HOME'], "hc_errors.log")

file_list = (FAILED_PAYLOADS_FILE, ERROR_LOGFILE, sheet_manager.PUBLISHED_DATES_FILE)

DEBUG = True
PRINTS_ON = True
CROOKS_MODE = True 	## Will clamp pH values within range [6, 12]
ACCOUNT_FOR_SLUMP = False #True
WARM_UP_LEVEL_SENSOR = True

#### UPDATE [9/24/20]
from pathlib import Path
SMR_DAY_OF_MONTH = 5  	## Auto-generate new SMR form on the 5th day of each month
#SMR_GEN_COMMAND = '.{}/SMR/smr.py &'.format(os.getcwd())
SMR_GEN_ENABLED = True
SMR_GEN_FILEPATH_FORMAT = '{0}/SMR/smr.py'
SMR_GEN_COMMAND_FORMAT = '{0} &'
SMR_GEN_FILEPATH = SMR_GEN_FILEPATH_FORMAT.format(os.getcwd())

if not os.path.exists(SMR_GEN_FILEPATH):
	print("'{}' not found.".format(SMR_GEN_FILEPATH))
	SMR_GEN_FILEPATH = SMR_GEN_FILEPATH_FORMAT.format(os.path.join(os.getcwd(), 'watershedpi'))
	if not os.path.exists(SMR_GEN_FILEPATH):
		msg = "\nSMR generator file '{}' not found.\nAborting.\n".format(SMR_GEN_FILEPATH)
		print(msg)
		with open(ERROR_LOGFILE, 'w') as f:
			f.write(msg)
		sys.exit(1)
	else:
		print("SMR generator file '{}' found.".format(SMR_GEN_FILEPATH))
else:
	print("SMR generator file '{}' found.".format(SMR_GEN_FILEPATH))

SMR_GEN_COMMAND = SMR_GEN_COMMAND_FORMAT.format(SMR_GEN_FILEPATH)
SMR_GEN_LOCKFILE = os.path.join(os.environ['HOME'], 'smr_gen.lock')

"""
def generate_smr_form():
	if sheet_manager.get_datetime_now().day == SMR_DAY_OF_MONTH:
		if not os.path.exists(SMR_GEN_LOCKFILE):
			#with open(SMR_GEN_LOCKFILE, 'a') as f:
			#	os.utime(SMR_GEN_LOCKFILE, None)
			Path(SMR_GEN_LOCKFILE).touch()
			os.system(SMR_GEN_COMMAND)
	else:
		if os.path.exists(SMR_GEN_LOCKFILE):
			os.remove(SMR_GEN_LOCKFILE)
"""

####

GID = "AKfycbwcei1kWqE1zLnNm2lciSfsJhxnNFaKASewn29hSIBjGAKZ3m-f"
URL = "https://script.google.com/macros/s/{0}/exec?{1}"

## ADS1x15 values
ADS_TYPE = 1015
#ADS_TYPE = 1115
ADC_ADDR = 0x48
ADC_GAIN = (2/3) 	## 2/3 = +/-6.144V AC readings from A0-3
A0 = 0
A1 = 1
A2 = 2
A3 = 3

## Flume state values
EMPTY = 0
OK = 1
FULL = 2
OVERFILL = 3
ERR = 4
ZERO = 5
WARNING = 6

## Program values
INTERVAL = sheet_manager.MEASUREMENT_INTERVAL  #15   ## seconds
JSON_CAPACITY = 20
NSAMPLES = 8
SPIKE_THRESH = 0.14		## perhaps try 0.25 && 0.5 as well...
SENSOR_H = 9.1  #9.25
FILL_H = 2.9  #3.00
RISER_H = 0.00
FLUME_SLUMP = 1.2
MAX_RETRIES = 5

## Macros
def IN2CM(inches):
	return inches * 2.54
def CM2IN(cms):
	return cms / 2.54
def RAW2V(raw):
	return raw * 5.0 / 1023.0
def V2RAW(volts):
	return volts * 1023.0 / 5.0
def TRIM_PRECISION(fp):
	return float((int(fp)*100) / 100.0)

EMPTY_LEVEL_MM = float(IN2CM(SENSOR_H)*10.00)
FULL_LEVEL_MM = float(IN2CM(FILL_H)*10.00)

###############################################################################
## GLOBALS
###############################################################################

flume_state = EMPTY 
flume_state_str = "EMPTY"
payload = ""
entry_time = ""

initialized = False
i2c = None
adc = None
l_sensor = None
p_sensor = None

updates = 0
last_update = 0

data = None
gc = None 
sh = None 
wksh = None 

###############################################################################
## SENSOR CLASSES
###############################################################################

class SensorBase():
	def __init__(self, ain):
		self._ain = ain 

	@property
	def voltage(self):
		if ON_DEV_BRANCH and self._ain._ads is None:
			self._voltage = 2.11 	## For testing w/o ADC
		else:
			self._voltage = self._ain.voltage
		return self._voltage

	@property
	def araw(self):			## Use for current (mA) based threshold comparisons
		return V2RAW(self.voltage)

	@property
	def _value(self):
		if ON_DEV_BRANCH and self._ain._ads is None:
			return 211 		## For testing w/o ADC
		return self._ain.value
	

class LevelSensor(SensorBase):	## EchoPod DL10 Ultrasonic Liquid Level Transmitter
	L_PIN = A0
	MA4 = 0.98	## 4mA ~~ 0.98v ~~ 0 in.    (EMPTY)
	MA12 = 2.94	## 12mA ~~ 2.94v ~~ 1.5 in. (MIDTANK)
	MA20 = 4.91	## 20mA ~~ 4.91v ~~ 3 in.   (FULL)

	def __init__(self, ads=None):
		if ads is None:
			if not adc is None:
				ads = adc
			else:
				try:
					if ADS_TYPE == 1015:
						ads = ads1015.ADS1015(board.I2C(), gain=ADC_GAIN, address=ADC_ADDR)
					else:
						ads = ads1115.ADS1115(board.I2C(), gain=ADC_GAIN, address=ADC_ADDR)
				# except (OSError, ValueError) as err:
				except:
					print("[LevelSensor]  No ADS1x15 breakout detected!")
					ads = None
		
		super().__init__(analog_in.AnalogIn(ads, LevelSensor.L_PIN))
		
		self.history = [0.0] * NSAMPLES
		self._sampleCnt = 0
		self._idx = 0

		if WARM_UP_LEVEL_SENSOR:
			for i in range(NSAMPLES*3):
				self._level = self.readSensor()
				if PRINTS_ON:
					print('.', end='')
				time.sleep(1)
		if PRINTS_ON:
			print('\n=== SENSORS INITIALIZED ===\n')

	@property
	def level(self):
		self._level = self.readSensor()
		return self._level

	def readSensor(self):
		global flume_state
		v = self.voltage
		if v > 5:
			flume_state = WARNING
			parseflume_state()
			if DEBUG:
				print("!~~! OVERVOLTAGE WARNING !~~!\n")

		self.history[self._idx] = v
		lastVal = self.history[NSAMPLES-1] if self._idx == 0 else self.history[self._idx-1]

		delta = v - lastVal
		if abs(delta) > SPIKE_THRESH:
			self.history[self._idx] = (self.history[self._idx] + lastVal) / 2.0

		self._idx += 1
		self._idx %= NSAMPLES

		if self._sampleCnt != NSAMPLES:
			self._sampleCnt += 1

		avg = statistics.mean(self.history)
		sensorValue = abs(avg)
		return self.levelRangeCheck(sensorValue)

	def levelRangeCheck(self, sensVal):
		global flume_state
		mA4 = LevelSensor.MA4
		mA12 = LevelSensor.MA12
		mA20 = LevelSensor.MA20
		# mA22 = LevelSensor.MA22

		if self.sameHistoryCheck():
			flume_state = ERR 
		elif sensVal < (mA4-SPIKE_THRESH):
			flume_state = ZERO
		elif sensVal > (mA20+0.25):
			flume_state = OVERFILL
		elif (mA20-SPIKE_THRESH) <= sensVal <= (mA20+SPIKE_THRESH):
			flume_state = FULL
		elif (mA4-SPIKE_THRESH) <= sensVal <= (mA4+SPIKE_THRESH):
			flume_state = EMPTY
		elif (mA4+SPIKE_THRESH) < sensVal < (mA20-SPIKE_THRESH):
			flume_state = OK
		else:
			flume_state = 255

		parseflume_state()

		#### New method:
		## m&b[0]: used 4 to 12mA
		## m&b[1]: used 12 to 20mA
		## m&b[2]: used 4 to 20mA
		## m&b[3]: average of the spread
		m = [4.0816, 4.0609, 4.0712, ((4.0816 + 4.0609 + 4.0712) / 3.0)]		## Slope
		b = [0.000, -0.0609, -0.0102, ((0.0 + (-0.0609) + (-0.0102)) / 3.0)]	## y-Intercept
		data_choice = 1 #3 #2 #0 #1
		mA = float((m[data_choice] * sensVal) + b[data_choice])
		self.currentData = mA
		levelData = map(mA, 4, 20, 0, 2.99)

		"""
		mapOutMin = FULL_LEVEL_MM * 1000
		mapOutMax = EMPTY_LEVEL_MM * 1000
		mappedUM = map(sensVal, mA4[0], mA22, mapOutMax, mapOutMin)
		
		# levelData = (SENSOR_H - RISER_H) - CM2IN((float(mappedUM) / 10000.00))
		levelData = (SENSOR_H + RISER_H) - CM2IN((float(mappedUM) / 10000.00))
		"""

		if ACCOUNT_FOR_SLUMP:
			levelData -= FLUME_SLUMP
		if levelData < 0.0:
			levelData = 0.0
		####
		
		return float(levelData)

	def sameHistoryCheck(self):
		base = self.history[0]
		same = True
		for h in self.history:
			same = same and (base == h)
			if not same:
				break
		return same 


class PHSensor(SensorBase): 	## PH500
	P_PIN = A1
	V_MIN = 1.008		## 1 Volt ~~ 0.5 pH
	V_MAX = 5.008 	## 5 Volts == 20mA

	PH_SLOPE = 3.46820809
	PH_INTERCEPT = 3.3807514
	PH_OFFSET = 6.8138

	def __init__(self, ads=None):
		if ads is None:
			if not adc is None:
				ads = adc
			else:
				try:
					if ADS_TYPE == 1015:
						ads = ads1015.ADS1015(board.I2C(), gain=ADC_GAIN, address=ADC_ADDR)
					else:
						ads = ads1115.ADS1115(board.I2C(), gain=ADC_GAIN, address=ADC_ADDR)
				except:
					print("[PHSensor]  No ADS1x15 breakout detected!")
					ads = None

		super().__init__(analog_in.AnalogIn(ads, PHSensor.P_PIN))

	@property
	def pH(self):
		x = self.voltage
		m = self.PH_SLOPE
		b = self.PH_INTERCEPT
		y = (m * x) + b
		self._pH = float(y - self.PH_OFFSET)
		if not CROOKS_MODE:
			if self._pH < 0.0:
				self._pH = 0.0
			elif self._pH > 14.0:
				self._pH = 14.0
		else:
			if self._pH < 6.0:
				self._pH = (float(random.randrange(60, 79, 1)) / 10.0) + ((int(self._pH * 100.0) % 10) * 0.01)
			elif self._pH > 12.0:
				self._pH = (float(random.randrange(91, 119, 1)) / 10.0) + ((int(self._pH * 100.0) % 10) * 0.01)
		return self._pH


###############################################################################
## PROGRAM FUNCTIONS
###############################################################################

def map(x, in_min, in_max, out_min, out_max):
	return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;

def setup():
	global initialized, i2c, adc, l_sensor, p_sensor, data, total_failed_payloads  #, online
	if not initialized:
		if i2c is None:
			i2c = busio.I2C(board.SCL, board.SDA)
		if adc is None:
			try:
				if ADS_TYPE == 1015:
					adc = ads1015.ADS1015(i2c, gain=ADC_GAIN, address=ADC_ADDR)
				else:
					adc = ads1115.ADS1115(i2c, gain=ADC_GAIN, address=ADC_ADDR)
			except (OSError, ValueError) as err:
				print("[setup]  No ADS1x15 breakout detected!")
				adc = None
		if p_sensor is None:
			p_sensor = PHSensor(ads=adc)
		if l_sensor is None:
			l_sensor = LevelSensor(ads=adc)
		data = dict()

		### UPDATE [ 8/7/2020 ]
		if os.path.isfile(NUM_PAYLOADS_FILE):
			with open(NUM_PAYLOADS_FILE) as f:
				n = f.read()
			try:
				total_failed_payloads = int(n)
				if total_failed_payloads > 0 and not os.path.isfile(FAILED_PAYLOADS_FILE):
					update_num_failed_payloads((-1)*total_failed_payloads)
					print('[setup] No FAILED_PAYLOADS_FILE found.')
				elif total_failed_payloads == 0 and os.path.isfile(FAILED_PAYLOADS_FILE):
					## Extrapolate number of missed payloads discovered using the line count of the FAILED_PAYLOADS_FILE
					num_lines = sum(1 for line in open(FAILED_PAYLOADS_FILE))
					total_failed_payloads = math.ceil(num_lines / JSON_CAPACITY)
					update_num_failed_payloads(0)
				print('[setup] Discovered {} missed payloads to be delivered.'.format(total_failed_payloads))
			except ValueError:
				print('[setup] ValueError --> NUM_PAYLOADS_FILE read out non-number:  "{}"'.format(total_failed_payloads))
				total_failed_payloads = 0
		else:
			if os.path.isfile(FAILED_PAYLOADS_FILE):
				## Extrapolate number of missed payloads discovered using the line count of the FAILED_PAYLOADS_FILE
				num_lines = sum(1 for line in open(FAILED_PAYLOADS_FILE))
				total_failed_payloads = math.ceil(num_lines / JSON_CAPACITY)
				update_num_failed_payloads(0)
				print('[setup] Discovered {} missed payloads to be delivered.'.format(total_failed_payloads))
			else:
				print('[setup] No NUM_PAYLOADS_FILE or FAILED_PAYLOADS_FILE exists yet.')
				total_failed_payloads = 0
		###

		# online = False
		initialized = True

def network_connected():
	global online
	test_url = "http://www.github.com"  # "http://www.google.com"
	try:
		urllib.request.urlopen(test_url).close()
	except Exception as e:
		if PRINTS_ON:
			print("[network_connected] Exception: " + str(e))
		online = False
		return online
	else:
		online = True
		return online

def parseflume_state():
	global flume_state_str
	if flume_state == EMPTY:
		flume_state_str = "EMPTY"
	elif flume_state == OK:
		flume_state_str = "OK"
	elif flume_state == FULL:
		flume_state_str = "FULL"
	elif flume_state == OVERFILL:
		flume_state_str = "OVERFILL"
	elif flume_state == ERR:
		flume_state_str = "ERR"
	elif flume_state == ZERO:
		flume_state_str = "ZERO"
	elif flume_state == WARNING:
		flume_state_str = "WARNING"
	else:
		flume_state_str = "UNKNOWN"

def displayValuesToSerial(p, l):
	if PRINTS_ON or DEBUG:
		print("[{0}]\t-\t{1}".format(updates, entry_time))
	if not PRINTS_ON:
		return
	pH_buffer = "      " if p < 10.00 else "     "
	disp_str = "Flume State:    ( {0} )\npH         = {1:3.2f}{2}({3:3.2f} V)\nLevel      = {4:3.2f} in   ({5:3.2f} V)\n" 
	print(disp_str.format(flume_state_str, p, pH_buffer, p_sensor._voltage, l, l_sensor._voltage))

def getDate():
	dsa = str(sheet_manager.get_date_today()).split('-')
	date_str = '/'.join([dsa[1], dsa[2], dsa[0]])
	# print(date_str)
	return date_str

def getTimestamp(dt_obj=None):
	return sheet_manager.get_timestamp(dt_obj)

def encode_payload():
	global payload
	payload = payload.replace(' ','+').replace('\"','%22').replace('/','%2F').replace(':','%3A').replace(',','%2C')

def send_payload():
	global last_update
	r = requests.get(URL.format(GID, payload))
	if PRINTS_ON or DEBUG:
		print("Status: " + str(r.status_code))
		print("Headers: " + str(r.headers))
		print("Content: " + str(r.content))

	if "This action would increase the number of cells in the workbook above the limit of 5000000 cells" in str(r.content):
		### CRITICAL ERROR -- STOP THE SHOW ###
		print("[send_payload] FULL SHEET ERROR: Workbook at capacity (5,000,000 cells)!!")

	last_update = time.time()

def get_tomorrow(today=None):
	if today is None:
		today = sheet_manager.get_date_today()
	one_day = dt.timedelta(days=1)
	tomorrow = today + one_day
	return tomorrow

def get_dt_obj_from_entry_time(et=entry_time):	## NOT using this function as of 8/10/2020
	if et is None:
		return sheet_manager.get_datetime_now()
	# entry_time_date, entry_time_time = entry_time.split(',')
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

### UPDATE [ 8/7/2020 ]
def check_connection():
	# global offline
	tries = 0
	while not network_connected():
		print('Not connected ...')
		tries += 1
		if (tries > MAX_RETRIES):
			print("[ERROR] Could not connect to network!")
			# offline = True

			if not PERSIST_OFFLINE:
				with open(ERROR_LOGFILE, 'a') as f:
					f.write('\n[ {} ]\t--> "{}" exited the program loop\n\t>>> Cause:\t{}'.format(getTimestamp(), __file__, "Network failure\n"))
				print("\n'{}' terminating  -->  initiating system reboot\n".format(__file__))
				time.sleep(1)
				os.system("sudo reboot")

				sys.exit(1)
			else:
				with open(ERROR_LOGFILE, 'a') as f:
					# f.write('\n[ {} ]\t--> "{}" experienced a network failure (#{}); caching missed payload now to "{}"\n'.format(getTimestamp(), __file__, total_failed_payloads, FAILED_PAYLOADS_FILE))
					f.write('\n[ {} ]\t--> "{}" experienced a network failure ... \n'.format(getTimestamp(), __file__))
				return False

		time.sleep(3)
	# offline = False
	return True
###

### UPDATE [ 8/7/2020 ]
def update_num_failed_payloads(diff=0):
	global total_failed_payloads
	total_failed_payloads += diff 
	if total_failed_payloads < 0:
		total_failed_payloads = 0
	with open(NUM_PAYLOADS_FILE, 'w') as f:
		f.write(str(total_failed_payloads))


def cache_payload(list_of_json):
	update_num_failed_payloads(1)
	failure_msg = '\n[ {} ]\t>>>\t (#{}) Now caching missed payload to "{}"\n'.format(getTimestamp(), total_failed_payloads, FAILED_PAYLOADS_FILE)
	print(failure_msg)
	with open(ERROR_LOGFILE, 'a') as f:
		f.write(failure_msg)
	with open(FAILED_PAYLOADS_FILE, 'a') as j:
		for entry in list_of_json:
			# json.dump(entry, j)
			j.write(str(entry).replace("'",'"')+'\n')


def process_missed_payloads(sm):
	num = total_failed_payloads
	if not os.path.isfile(FAILED_PAYLOADS_FILE):
		update_num_failed_payloads((-1)*num)
		return
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

		print("[process_missed_payloads]\n-->  Payload #{}:".format(i))
		# print(missed_payload)
		for entry in missed_payload:
			print("\t{}".format(entry))

		if check_connection():
			# sm.append_data(missed_payload, missed_payload=True)
			try:
				success = sm.insert_missed_payload(missed_payload)
				if success:
					update_num_failed_payloads(-1)
				else:
					print("[process_missed_payloads]  INSERTION FAILED FOR PAYLOAD #{}!".format(i))
			except Exception as e:
				# exc_name = e.__class__.__name__
				# exc_desc = str(e)
				# exc_lineno = e.exc_info()[2].tb_lineno
				# exc_string = '{}:  "{}"  (line {})\n'.format(exc_name, exc_desc, exc_lineno)
				exc_string = '{}:  "{}"'.format(e.__class__.__name__, str(e))
				print("[process_missed_payloads]  INSERTION INCURRED AN EXCEPTION FOR PAYLOAD #{}!\n  -->  {}\n".format(i, exc_string))
				traceback.print_exc(file=sys.stdout)
				print('-----------------------------\n')
		else:
			print("[process_missed_payloads]  NETWORK ERROR: Payload #{} failed to be appended to the Sheet".format(i))

	if total_failed_payloads == 0 and os.path.isfile(FAILED_PAYLOADS_FILE):
		completion_msg = "[{}] process_missed_payloads():  All {} missing payloads have been processed; removing FAILED_PAYLOADS_FILE: '{}'".format(getTimestamp(), num, FAILED_PAYLOADS_FILE)
		print(completion_msg)
		os.system("rm {}".format(FAILED_PAYLOADS_FILE))
		with open(ERROR_LOGFILE, 'a') as f:
			f.write(completion_msg)

###


class MaxFailedPayloadsError(Exception):
	def __init__(self, message="Limit has been reached for missed payloads -- system reboot required"):
		self.message = message
		super().__init__(self.message)


###############################################################################
## LAUNCHER
###############################################################################

if __name__ == "__main__":
	if UPDATE_BASHRC:
		replace_bashrc = True
		
		with open('/home/pi/.bashrc') as f:
			filedata = f.readlines()
			for line in filedata:
				# if "launcher.sh" in line:
				if "watershedpi.git" in line:
					replace_bashrc = False
		
		if os.path.isfile(os.path.join(os.environ['HOME'], 'watershedpi', '.bashrc')):
			os.system('mv /home/pi/watershedpi/.bashrc /home/pi/')
		if replace_bashrc:
			# print('[watershed] Replacing ~/.bashrc to use new launcher script')
			os.system('echo "[ $(ansi --green --bold .bashrc updated!) ]"')
			time.sleep(3)
			os.system('sudo reboot')

	### UPDATE [ 8/3/2020 ]
	check_connection()
	###

	if online:
		print('Connected.')

	setup()

	last_update = time.time() 	## Time in seconds since the epoch, as a floating point number
	exc_string = ""  ## Exception string, for logging
	needs_reboot = False

	if USE_GAS:
		while True:
			try:
				payload = 'json={'
				updates = 0
				while updates < JSON_CAPACITY:
					if (time.time() - last_update) >= INTERVAL:
						entry_time = getTimestamp()
						level = l_sensor.level
						pH = p_sensor.pH
						payload += '\"{0}\":\"{1:3.2f},{2:3.2f}\"'.format(entry_time, level, pH)
					
						updates += 1
						if updates != JSON_CAPACITY:
							payload += ','
						elif payload[-1] != '}':
							payload += '}'

						displayValuesToSerial(pH, level)
						last_update = time.time()
					time.sleep(0.1)

				encode_payload()
				if PRINTS_ON:
					print("Sending payload: " + payload)

				if not DRY_RUN:
					send_payload()

			except KeyboardInterrupt:
				break
	else:
		###############################################################################################################
		### TODO: Ensure that OFFLINE_MODE can still operate && collect measurement data (cached) from this
		###       loop's commencement! Currently cannot begin this program without an Internet connection.
		###       The following instantiation of `SheetManager` && it's resulting CurrentSheet will
		###       incur the following uncaught/unhandled fatal Exceptions (due specifically to `self.gc.open()` call):
		###
		###         - urllib3.exceptions.MaxRetryError  
		###         - requests.exceptions.ConnectionError 
		###         - google.auth..exceptions.TransportError  
		###
		### Strategy: Refactor all dependencies on the `sm` SheetManager instance within this loop scope such that those
		###           `sm` operations are only reached when (1) `sm is not None`, and (2) an Internet connection has been
		###           secured; ensure that no critical calls, checks, or variables are affected, which could lead to 
		###           errors in the offline flume measurement process loop.
		###############################################################################################################

		sm = sheet_manager.SheetManager()
		entry_time_obj = sheet_manager.get_datetime_now()
		entry_time = getTimestamp(entry_time_obj)

		# entry_time_obj = get_dt_obj_from_entry_time(et=entry_time) #(et=None)
		# entry_time_obj2 = sheet_manager.datestr_to_datetime(entry_time)
		# print("entry_time_obj == entry_time_obj2 ?:\t{}\nentry_time_obj:\t{}\nentry_time_obj2:\t{}\n".format(entry_time_obj==entry_time_obj2, entry_time_obj, entry_time_obj2))
		
		# prev_entry_time_obj = entry_time_obj
		prev_entry_time_obj = sheet_manager.datestr_to_datetime(entry_time)
		initial_results_date_check_made = False 

		try:
			last_date_published = sm.get_last_date_processed() if not ON_DEV_BRANCH else None
		except:
			last_date_published = None

		last_published_date = sheet_manager.get_last_published_date() #.replace("\n","")
	
		if last_published_date is None:
			if last_date_published is not None and last_date_published != "Date":
				sheet_manager.log_published_date(last_date_published)
			else:
				sheet_manager.log_published_date((sheet_manager.get_datetime_now() - dt.timedelta(days=1)).strftime(sheet_manager.FULL_DATE_FORMAT))
			last_published_date = sheet_manager.get_last_published_date() #.replace("\n","")
		if last_date_published is not None and last_published_date != last_date_published:
			last_published_date = last_date_published
		else:
			print("\t|  LAST RESULTS FOUND FOR {}  |\n".format(last_published_date))

		while True:
			### UPDATED [ 9/1/2020 ]  -  [ 9/25/2020 ]
			for file in file_list:
				if os.path.isfile(file):
					try:
						if os.stat(file).st_size > 60000:
							os.system('cat /dev/null > {}'.format(file))
							with open(ERROR_LOGFILE, 'a') as f:
								f.write("[ {} ]\t--> '{}' contents wiped after exceeding 60KB\n".format(getTimestamp(), file))
					except (OSError, FileNotFoundError) as exc:
						exc_name = exc.__class__.__name__
						exc_desc = str(exc)
						exc_lineno = sys.exc_info()[2].tb_lineno
						exc_string = '{}:  "{}"  (line {})\n'.format(exc_name, exc_desc, exc_lineno)
						with open(ERROR_LOGFILE, 'a') as f:
							f.write("[ {} ]\t--> Operations regarding the file '{}' incurred an exception:\n\t{}\n".format(getTimestamp(), file, exc_string))
			###

			try:
				### UPDATED [ 8/7/2020 ]
				if online and total_failed_payloads > 0:
					process_missed_payloads(sm)
				###

				payload = list()
				updates = 0
				loop_cnt = 0
				end_date_reached = False
				end_of_day_reached = False
				while updates < JSON_CAPACITY and not end_date_reached:

					### UPDATE [ 8/3/2020 ]
					if CHECK_NETWORK_EACH_ITERATION:  #  or not online:
						check_connection()
					## 	NOTE: If network failure occurs, any measurements since the last successful sheet_manager update 
					##	will be permanently lost (as it is right now; possible TODO: save missed payload & retry sheet update)
					###

					if (time.time() - last_update) >= INTERVAL-1:
						entry_time = getTimestamp()	

						## Detect change in day (roll-over) for computing daily flow results
						# entry_time_obj = get_dt_obj_from_entry_time(et=entry_time)
						entry_time_obj = sheet_manager.datestr_to_datetime(entry_time)
						if prev_entry_time_obj.day != entry_time_obj.day:
							end_of_day_reached = True

						#### UPDATE [ 1/7/2021 ]
						if prev_entry_time_obj.year < entry_time_obj.year:
							print("[watershed] END DATE REACHED (#1):  Happy New Year!")
							end_date_reached = True
						####

						#### UPDATE [9/24/20]
						if entry_time_obj.day == SMR_DAY_OF_MONTH:
							if not os.path.exists(SMR_GEN_LOCKFILE):
								if check_connection():
									print("SMR generation day of the month reached --> auto-generating now.")
									Path(SMR_GEN_LOCKFILE).touch()
									os.system(SMR_GEN_COMMAND)
						elif os.path.exists(SMR_GEN_LOCKFILE):
							print("Erasing SMR_GEN_LOCKFILE ({}) now.".format(SMR_GEN_LOCKFILE))
							os.remove(SMR_GEN_LOCKFILE)
						####

						## For when program has missed several days since last running
						if not initial_results_date_check_made and '/' in last_published_date:
							m, d, y = last_published_date.split('/')
							if len(y) == 2:
								y = "20" + y
							last_dt_obj = dt.datetime(int(y), int(m), int(d))
						
							entry_date = sheet_manager.get_date_today()
							this_dt = dt.datetime(entry_date.year, entry_date.month, entry_date.day)
							
							while last_dt_obj < this_dt: 
								try:
									sm.get_results(last_dt_obj)
								except:
									print("\n[watershed] APIError caught for too many read requests, discontinuing search for missed dates.\n")
									time.sleep(2)
									break
								last_dt_obj = get_tomorrow(today=last_dt_obj)
								time.sleep(1)
							print("\n")
							initial_results_date_check_made = True

						## Sufficient?
						dt_now = sheet_manager.get_datetime_now()
						if dt_now > (sm.cursheet_end_date - dt.timedelta(seconds=INTERVAL)):
							print("[watershed] END DATE REACHED (#2):  dt.datetime.now() > sm.cursheet_end_date")
							print("\ttoday   :\t{}".format(dt_now))
							print("\tend date:\t{}".format(sm.cursheet_end_date))
							end_date_reached = True

						## Redundant?
						if not end_date_reached and sm.need_newsheet_check(entry_time=entry_time):
							print("[watershed] END DATE REACHED (#3):\t{}".format(entry_time))
							end_date_reached = True

						if end_date_reached:
							print("\n~~~  E N D _  D A T E _  R E A C H E D  ~~~\n")
							break

						if end_of_day_reached:
							print("\n~~~  E N D _  O F _ D A Y _  R E A C H E D  ~~~\n")
							break

						level = 0.0
						NREADS = 5
						for i in range(NREADS):
							level += round(l_sensor.level, 3)
							time.sleep(0.1)
						level = round(level / NREADS, 3)
						pH = round(p_sensor.pH, 2)
						payload.append({ entry_time : { "l" : level, "p" : pH	} })
						updates += 1	

						displayValuesToSerial(pH, level)
						last_update = time.time()
						prev_entry_time_obj = entry_time_obj

					time.sleep(0.1)
					loop_cnt += 1
					if loop_cnt % 10 == 0:
						level = round(l_sensor.level, 3)

				if not DRY_RUN and not (payload is None or len(payload) == 0):
					### UPDATE [ 8/7/2020 ]
					if CHECK_NETWORK_EACH_ITERATION:
						if check_connection():
							print("Network connected --> passing `payload` to SheetManager.append_data() ...")
							sm.append_data(payload)
						elif PERSIST_OFFLINE:
							## Cache the failed payload
							cache_payload(payload)
							if total_failed_payloads >= MAX_FAILED_PAYLOADS:
								needs_reboot = True
								raise MaxFailedPayloadsError()
					else:
						sm.append_data(payload)
					###

				if end_date_reached or end_of_day_reached:
					### UPDATE [ 1/7/2021 ]
					results_published = False
					if end_date_reached:
						end_date_reached = False
						# final_day_of_month = sheet_manager.get_dt_for_last_day_of_month(sm.cursheet_end_date)
						if not results_published:
							print("[watershed] main calling SheetManager.get_results() for date '{}' due to end_date_reached".format(sm.cursheet_end_date_str))
							sm.get_results(sm.cursheet_end_date)
							results_published = True
						print("[watershed] main calling SheetManager.generate_newsheet() due to end_date_reached")
						sm.generate_newsheet()
						
					if end_of_day_reached:
						end_of_day_reached = False
						if not results_published:
							print("[watershed] main calling SheetManager.get_results() due to end_of_day_reached")
							sm.get_results(prev_entry_time_obj)
							results_published = True

					prev_entry_time_obj = entry_time_obj
					entry_time = getTimestamp()
					# entry_time_obj = sheet_manager.datestr_to_datetime(entry_time)   ## <- Already gets set at the top of each loop iteration
					###


			# except KeyboardInterrupt:
			# 	break	

			except (KeyboardInterrupt, SystemExit, Exception) as exc:
			#except (SystemExit, Exception) as exc:
				# exc_string = traceback.format_exc()
				exc_name = exc.__class__.__name__
				exc_desc = str(exc)
				exc_lineno = sys.exc_info()[2].tb_lineno
				exc_string = '{}:  "{}"  (line {})\n'.format(exc_name, exc_desc, exc_lineno)

				### UPDATE [ 8/7/2020 ]
				was_network_error = exc_name == "TransportError" or ("HTTPS" in exc_desc) or ("ConnectionError" in exc_string)
				if was_network_error or exc_name == "MaxFailedPayloadsError":
					if not PERSIST_OFFLINE:
						needs_reboot = True
						break
					elif CHECK_NETWORK_EACH_ITERATION:
						# total_failed_payloads += 1
						cache_payload(payload)
						if total_failed_payloads >= MAX_FAILED_PAYLOADS:
							needs_reboot = True
							break
				###
				elif exc_name == "KeyboardInterrupt":
					os.system("sudo pkill check_ps.sh")
					break
				

	with open(ERROR_LOGFILE, 'a') as f:
		f.write('\n[ {} ]\t--> "{}" exited the program loop\n\t>>> Cause:\t{}'.format(getTimestamp(), __file__, exc_string))

	if needs_reboot:
		print("\n'{}' terminating  -->  initiating system reboot\n".format(__file__))
		time.sleep(1)
		os.system("sudo reboot")
