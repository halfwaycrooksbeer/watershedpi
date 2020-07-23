from watershed import LevelSensor
import time
from datetime import datetime as dt

def get_ts():
	return dt.now().strftime('%I:%M:%S %p')

fstr = "({})   L: {:.4f} in.  |  V: {:.4f} V  |  A: {}"
loop_delay = 1  ## Seconds
dl10 = LevelSensor()

while True:
	try:
		data = [get_ts(), dl10.level, dl10.voltage, dl10._value]
		print(fstr.format(*data))
		time.sleep(loop_delay)
	except KeyboardInterrupt:
		break

