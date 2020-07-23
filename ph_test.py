from watershed import PHSensor
from time import sleep
from datetime import datetime as dt
from statistics import mean

N_CALIB_SAMPLES = 32
S_CALIB_DELAY = 1
DATA_STRF = "pH: {:.3f}  |  voltage: {:.3f} V  |  aIn: {:.3f}"

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
			# print("[{}]    pH = {:.2f}  |  voltage = {:.2f} V  |  ain = {:.2f}".format(ts, p, v, a))
			print(poll_str)
			# return pH, voltage
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

tests = {
	1 : poll_sensor,
	2 : calibrate_pH_4,
	3 : calibrate_pH_7,
	4 : calibrate_pH_10
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
	tests[n](pH500)
