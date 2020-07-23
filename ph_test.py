from watershed import PHSensor
from time import sleep
from datetime import datetime as dt

if __name__ == "__main__":
	pH500 = PHSensor()
	while True:
		try:
			pH = pH500.pH
			voltage = pH500.voltage
			value = pH500._value
			ts = dt.now().strftime("%m/%d/%Y,%I:%M:%S %p")
			print("[{}]    pH = {:.2f}  |  voltage = {:.2f} V  |  ain = {:.2f}".format(ts, pH, voltage, value))
			sleep(1)
		except KeyboardInterrupt:
			break
