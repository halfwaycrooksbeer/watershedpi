from watershed import PHSensor
from time import sleep
from datetime import datetime as dt
from statistics import mean

N_CALIB_SAMPLES = 32
S_CALIB_DELAY = 1
DATA_STRF = "pH: {:.3f}  |  voltage: {:.3f} V  |  aIn: {:.3f}"

m = 0	## Slope for pH function
b = 0 	## Intercept for pH function

def _read(sensor):
	pH = sensor.pH
	voltage = sensor.voltage
	value = sensor._value
	return pH, voltage, value

def poll_sensor(sensor):
	while True:
		try:
			p, v, a = _read(sensor)
			ts = dt.now().strftime("%m/%d/%Y,%I:%M:%S %p")
			poll_str = "[{}]\t{}".format(ts, DATA_STRF.format(p, v, a))
			print(poll_str)
			sleep(1)
		except KeyboardInterrupt:
			return


def _calib(sensor, const_ph):
	print('-'*24)
	print("Calibrating readings for constant pH of {} ...".format(const_ph))
	samples = [[0]*3]*N_CALIB_SAMPLES
	for i in range(N_CALIB_SAMPLES):
		samples[i] = _read(sensor)
		print("[{}]   {}".format(str(i).zfill(2), DATA_STRF.format(*samples[i])))
		sleep(S_CALIB_DELAY)
	print("\n... finished. Results for pH {}:".format(const_ph))
	print(">>>  Avg. pH: {}".format(mean([s[0] for s in samples])))
	print(">>>  Avg. voltage: {}".format(mean(s[1] for s in samples)))
	print(">>>  Avg. analog value: {}".format(mean([s[2] for s in samples])))
	print('-'*24)


def calibrate_pH_4(sensor):
	_calib(sensor, 4.01)

def calibrate_pH_7(sensor):
	_calib(sensor, 7.01)

def calibrate_pH_10(sensor):
	_calib(sensor, 10.01)

def get_slope_and_intercept(ph4_value, ph7_value):
	global m, b
	## y-axis is pH from 0-14, x-axis is analog value corresponding to pH (could also use voltage?)
	m = ((4.01 - 7.01) / (ph4_value - ph7_value))
	b = (m * ph7_value) - 7.01
	return m, b

def get_pH_from_ain(x):
	if m == 0:
		print("[get_pH_from_ain]  Need to calibrate for pH 4.01 & 7.01, then call get_slope_and_intercept()")
		return -1
	y = (m * x) + b
	return y

tests = {
	1 : poll_sensor,
	2 : calibrate_pH_4,
	3 : calibrate_pH_7,
	4 : calibrate_pH_10,
	5 : get_slope_and_intercept,
	6 : get_pH_from_ain
}

def menu_select():
	menu_prompt = '\nEnter test number to run for the pH500:'
	menu_prompt += '\n\t1. General sensor poll loop'
	menu_prompt += '\n\t2. Calibrate in 4.01 pH solution'
	menu_prompt += '\n\t3. Calibrate in 7.01 pH solution'
	menu_prompt += '\n\t4. Calibrate in 10.01 pH solution'
	menu_prompt += '\n'
	err_str = '[ValueError] Invalid input: "{}" --> Please enter a number from 1 to {}'
	test_num = input(menu_prompt)
	try:
		n = int(test_num)
		if not (1 <= n <= len(tests)):
			print(err_str.format(test_num, len(tests)))
			n = None
	except ValueError:
		print(err_str.format(test_num, len(tests)))
		n = None
	return n


if __name__ == "__main__":
	pH500 = PHSensor()
	n = None
	while n is None:
		n = menu_select()
	if n == 5:
		ph4 = float(input('Enter the mean analog value for pH 4.01:  '))
		ph7 = float(input('Enter the mean analog value for pH 7.01:  '))
		slope, intercept = tests[n](ph4, ph7)
		print('\nSlope (m):  {}\ny-Intercept (b):  {}'.format(slope, intercept))
	elif n == 6:
		analog_val = pH500._value
		ph_from_ain = tests[n](analog_val)
		print('\nanalog_val = {}  -->  pH = {}'.format(analog_val, ph_from_ain))
	else:
		tests[n](pH500)


