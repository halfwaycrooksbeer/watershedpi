
import time
from datetime import datetime as dt


def get_ts():
	return dt.now().strftime('%I:%M:%S %p')

fstr = "({})   L: {:.4f} in.  |  V: {:.4f} V  |  A: {}"
loop_delay = 1  ## Seconds


MA4 = 0.98   ## Voltage corresponding to 4mA
MA20 = 5.01  ## Voltage corresponding to 20mA
MAX_LEVEL = 3.01
MIN_LEVEL = 0.00

def map(x, in_min, in_max, out_min, out_max):
	return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def voltage_to_mA(v):
	m = 3.9702233250620353
	b = -0.10918114143920521
	return float((m * v) + b)

def mA_to_level(ma):
	m = 0.1875
	b = 0.75
	return float((m * ma) + b)

def voltage_to_level(v):
	# m = 0.7444168734491317
	# b = 0.7295285359801493
	# return float((m * v) + b)
	return map(v, MA4, MA20, MIN_LEVEL, MAX_LEVEL)


USE_LEVELSENSOR_CLASS = False

if USE_LEVELSENSOR_CLASS:
	from watershed import LevelSensor
	dl10 = LevelSensor()

	while True:
		try:
			data = [get_ts(), dl10.level, dl10.voltage, dl10._value]
			print(fstr.format(*data))
			time.sleep(loop_delay)
		except KeyboardInterrupt:
			break

else:
	from adafruit_ads1x15 import ads1015, analog_in
	import board

	adc = ads1015.ADS1015(board.I2C(), gain=(2/3), address=0x48)
	dl10 = analog_in.AnalogIn(adc, 0)

	ready = input("Press enter to begin test...")

	while True:
		try:
			volts = dl10.voltage
			mA = voltage_to_mA(volts)
			# level = mA_to_level(mA)
			level = voltage_to_level(volts)
			data = [get_ts(), level, volts, dl10.value]
			print(fstr.format(*data))
			time.sleep(loop_delay/2)
		except KeyboardInterrupt:
			break



