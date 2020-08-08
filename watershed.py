#!/usr/bin/python3
import os
import sys
import time
import urllib
import requests
import busio
import board
import random
import traceback
import statistics
import datetime as dt
import RPi.GPIO as GPIO
from adafruit_ads1x15 import ads1115, ads1015, analog_in

# import sheet_manager
import sheet_manager2 as sheet_manager

###############################################################################
## CONSTANTS
###############################################################################

DRY_RUN = False  #True  ## Will skip sheet_manager.append_data() call; SET TO FALSE BEFORE DEPLOYMENT
UPDATE_BASHRC = False #True
TESTING = False #True 	## SET TO FALSE BEFORE DEPLOYMENT
USE_GAS = False 

### UPDATE [ 8/7/2020 ]
import json
CHECK_NETWORK_EACH_ITERATION = False
PERSIST_OFFLINE = True
FAILED_PAYLOADS_FILE = os.path.join(os.environ['HOME'], "missed_payloads.json")
MAX_FAILED_PAYLOADS = 20
total_failed_payloads = 0
###
ERROR_LOGFILE = os.path.join(os.environ['HOME'], "hc_errors.log")

DEBUG = True
PRINTS_ON = True
CROOKS_MODE = False #True
ACCOUNT_FOR_SLUMP = False #True
WARM_UP_LEVEL_SENSOR = True

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
INTERVAL = 15 	## seconds
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
		self._voltage = self._ain.voltage
		return self._voltage

	@property
	def araw(self):			## Use for current (mA) based threshold comparisons
		return V2RAW(self.voltage)

	@property
	def _value(self):
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
				if ADS_TYPE == 1015:
					ads = ads1015.ADS1015(board.I2C(), gain=ADC_GAIN, address=ADC_ADDR)
				else:
					ads = ads1115.ADS1115(board.I2C(), gain=ADC_GAIN, address=ADC_ADDR)
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
				if ADS_TYPE == 1015:
					ads = ads1015.ADS1015(board.I2C(), gain=ADC_GAIN, address=ADC_ADDR)
				else:
					ads = ads1115.ADS1115(board.I2C(), gain=ADC_GAIN, address=ADC_ADDR)
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
				self._pH = (float(random.randrange(61, 69, 1)) / 10.0) + ((int(self._pH * 100.0) % 10) * 0.01)
			elif self._pH > 12.0:
				self._pH = (float(random.randrange(111, 119, 1)) / 10.0) + ((int(self._pH * 100.0) % 10) * 0.01)
		return self._pH


###############################################################################
## PROGRAM FUNCTIONS
###############################################################################

def map(x, in_min, in_max, out_min, out_max):
	return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;

def setup():
	global initialized, i2c, adc, l_sensor, p_sensor, data
	if not initialized:
		if i2c is None:
			i2c = busio.I2C(board.SCL, board.SDA)
		if adc is None:
			if ADS_TYPE == 1015:
				adc = ads1015.ADS1015(i2c, gain=ADC_GAIN, address=ADC_ADDR)
			else:
				adc = ads1115.ADS1115(i2c, gain=ADC_GAIN, address=ADC_ADDR)
		if p_sensor is None:
			p_sensor = PHSensor(ads=adc)
		if l_sensor is None:
			l_sensor = LevelSensor(ads=adc)
		data = dict()
		initialized = True

def network_connected():
	test_url = "http://www.github.com"  # "http://www.google.com"
	try:
		urllib.request.urlopen(test_url).close()
	except Exception as e:
		if PRINTS_ON:
			print("[network_connected] Exception: " + str(e))
		return False
	else:
		return True

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

def get_dt_obj_from_entry_time(et=entry_time):
	if et is None:
		return sheet_manager.get_datetime_now()
	entry_time_date, entry_time_time = entry_time.split(',')
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
	global total_failed_payloads
	tries = 0
	while not network_connected():
		print('Not connected ...')
		tries += 1
		if (tries > MAX_RETRIES):
			print("[ERROR] Could not connect to network!")

			if not PERSIST_OFFLINE:
				with open(ERROR_LOGFILE, 'a') as f:
					f.write('\n[ {} ]\t--> "{}" exited the program loop\n\t>>> Cause:\t{}'.format(getTimestamp(), __file__, "Network failure\n"))
				print("\n'{}' terminating  -->  initiating system reboot\n".format(__file__))
				time.sleep(1)
				os.system("sudo reboot")

				sys.exit(1)
			else:
				# if not CHECK_NETWORK_EACH_ITERATION:
				# 	total_failed_payloads += 1

				with open(ERROR_LOGFILE, 'a') as f:
					# f.write('\n[ {} ]\t--> "{}" experienced a network failure (#{}); caching missed payload now to "{}"\n'.format(getTimestamp(), __file__, total_failed_payloads, FAILED_PAYLOADS_FILE))
					f.write('\n[ {} ]\t--> "{}" experienced a network failure ... \n'.format(getTimestamp(), __file__))
			
				return False

		time.sleep(3)

	return True
###

### UPDATE [ 8/7/2020 ]
def cache_payload(list_of_json):
	global total_failed_payloads
	total_failed_payloads += 1

	failure_msg = '\n[ {} ]\t>>>\t (#{}) Now caching missed payload to "{}"\n'.format(getTimestamp(), total_failed_payloads, FAILED_PAYLOADS_FILE)
	print(failure_msg)
	with open(ERROR_LOGFILE, 'a') as f:
		f.write(failure_msg)
	
	with open(FAILED_PAYLOADS_FILE, 'a') as j:
		for entry in list_of_json:
			json.dump(entry, j)

def process_missed_payloads(sm):
	global total_failed_payloads
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
		sm = sheet_manager.SheetManager()
		entry_time = getTimestamp()
		entry_time_obj = get_dt_obj_from_entry_time(et=entry_time) #(et=None)
		prev_entry_time_obj = entry_time_obj
		initial_results_date_check_made = False 

		try:
			last_date_published = sm.get_last_date_processed()
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
			try:
				payload = list()
				updates = 0
				loop_cnt = 0
				end_date_reached = False
				end_of_day_reached = False
				while updates < JSON_CAPACITY and not end_date_reached:

					### UPDATE [ 8/3/2020 ]
					if CHECK_NETWORK_EACH_ITERATION:
						check_connection()
					## 	NOTE: If network failure occurs, any measurements since the last successful sheet_manager update 
					##	will be permanently lost (as it is right now; possible TODO: save missed payload & retry sheet update)
					###

					if (time.time() - last_update) >= INTERVAL:
						entry_time = getTimestamp()	

						## Detect change in day (roll-over) for computing daily flow results
						entry_time_obj = get_dt_obj_from_entry_time(et=entry_time)
						if prev_entry_time_obj.day != entry_time_obj.day:
							end_of_day_reached = True

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
						if dt_now > sm.cursheet_end_date:
							print("dt.datetime.now() > sm.cursheet_end_date")
							print("\ttoday   :\t{}".format(dt_now))
							print("\tend date:\t{}".format(sm.cursheet_end_date))
							end_date_reached = True

						## Redundant?
						if sm.need_newsheet_check(entry_time=entry_time):
							print("[watershed] END DATE REACHED (#1):\t{}".format(entry_time))
							end_date_reached = True

						if end_of_day_reached or end_date_reached:
							break

						level = round(l_sensor.level, 3)
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

				if not DRY_RUN:
					### UPDATE [ 8/7/2020 ]
					if not CHECK_NETWORK_EACH_ITERATION:
						if check_connection():
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

				if end_of_day_reached:
					print("[watershed] main calling SheetManager.get_results() due to end_of_day_reached")
					sm.get_results(prev_entry_time_obj)
					prev_entry_time_obj = entry_time_obj
					end_of_day_reached = False

				if end_date_reached:
					# final_day_of_month = sheet_manager.get_dt_for_last_day_of_month(sm.cursheet_end_date)
					print("[watershed] main calling SheetManager.get_results() for date '{}' due to end_date_reached".format(sm.cursheet_end_date_str))
					sm.get_results(sm.cursheet_end_date)
					print("[watershed] main calling SheetManager.generate_newsheet() due to end_date_reached")
					sm.generate_newsheet()
					prev_entry_time_obj = entry_time_obj
					end_date_reached = False

			# except KeyboardInterrupt:
			# 	break	

			except (KeyboardInterrupt, SystemExit, Exception) as exc:
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
