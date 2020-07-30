#!/bin/bash

## Check network
netfails=0
while [ $netfails -lt 5 ]; do
	if ! ping -c 1 pypi.org; then
		echo "[setup.sh] net fail!"
		((netfails++))
		sudo service networking restart
		sleep 8s
	else
		break
	fi
done
if [ $netfails -lt 5 ]; then
	echo -e "\n[setup.sh] network connected!\n"
else
	echo -e "\n[setup.sh] CRITICAL ERROR: No network connectivity, rebooting device!\n"
	sleep 4s
	sudo reboot
fi

## Check apt dependencies
declare -a ReqPackages=("git" "make" "build-essential" "i2c-tools" "libi2c-dev")
for REQ_PKG in "${ReqPackages[@]}"; do
	PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $REQUIRED_PKG|grep "install ok installed")
	printf "$(ansi --yellow Checking for package) $(ansi --cyan $REQ_PKG):\t-->\t"
	if [ "" = "$PKG_OK" ]; then
		printf "$(ansi --red --bold not yet installed) -- installing now...\n\n"
		sudo apt-get install -qq $REQ_PKG 
	else
		printf "$(ansi --green --bold $PKG_OK)\n"
	fi
done
echo -e "\n\n"

## Check pip3 dependencies
PIP="python3 -m pip"
PIP_REQS_FILE="${HOME}/watershedpi/requirements.txt"
PIP_LIST_FILE="${HOME}/pip_list.txt"

$PIP list --format=columns > $PIP_LIST_FILE

if [ -f "$PIP_REQS_FILE" ]; then
	# ALL_INSTALLED=true
	while IFS="" read -r p || [ -n "$p" ]
	do
		PKG_OK=$(grep "$p" $PIP_LIST_FILE)
		printf "$(ansi --yellow Checking for package) $(ansi --cyan $p):\t-->\t"
		if [ "" = "$PKG_OK" ]; then
			printf "$(ansi --red --bold not yet installed) -- installing now...\n"
			# ALL_INSTALLED=false
			$PIP install --user $p 
		else
			printf "$(ansi --green --bold $PKG_OK)\n"
		fi
	done < $PIP_REQS_FILE

	# if [ $ALL_INSTALLED = false ]; then
	# 	$PIP install --user -r $PIP_REQS_FILE
	# fi
else
	declare -a PipPackages=("gspread" "oauth2client" "google-api-python-client" "google-auth-httplib2" "google-auth-oauthlib" "adafruit-blinka" "adafruit-circuitpython-ads1x15")
	for p in "${PipPackages[@]}"; do
		PKG_OK=$(grep "$p" $PIP_LIST_FILE)
		printf "$(ansi --yellow Checking for package) $(ansi --cyan $p):\t-->\t"
		if [ "" = "$PKG_OK" ]; then
			printf "$(ansi --red --bold not yet installed) -- installing now...\n\n"
			$PIP install --user $p
		else
			printf "$(ansi --green --bold $PKG_OK)\n"
		fi
	done
	# $PIP install --user gspread oauth2client google-api-python-client google-auth-httplib2 google-auth-oauthlib adafruit-blinka adafruit-circuitpython-ads1x15
fi

rm $PIP_LIST_FILE

## Configure watchdog settings
echo -e "\n\n~~~~~~~ W4TCH_D0G ~~~~~~~~\n"

test_with_forkbomb=false  #true

if [ $(watchdog) ]; then
	first_wtd_install=false
else
	first_wtd_install=true
fi
echo -e "${first_wtd_install}\n"

sudo apt-get install -y watchdog chkconfig

if grep -q "bcm2835_wdt" /etc/modules; then
	echo "==>  bcm2835_wdt Watchdog Kernel Module Loaded"
else
	echo "==>  Now Adding Missing bcm2835_wdt Watchdog Kernel Module to /etc/modules ..."
	echo "bcm2835_wdt" | sudo tee -a /etc/modules
fi

## Load the module w/ modprobe
sudo modprobe bcm2835_wdt

## Set the watchdog daemon to run on every boot
sudo update-rc.d watchdog defaults

if grep -q "watchdog-timeout" /etc/watchdog.conf; then
	echo "==>  /etc/watchdog.conf Appears to be Correctly Configured"
else
	echo "==>  Loading Custom watchdog.conf File to /etc/"
	if [ -f "${HOME}/watershedpi/watchdog.conf" ]; then
		sudo mv "${HOME}/watershedpi/watchdog.conf" /etc/
	else
		sudo sed -i "s|#watchdog-device|watchdog-device|g" /etc/watchdog.conf
		sudo sed -i "s|#max-load-1 |max-load-1 |g" /etc/watchdog.conf
		sudo sed -i "s|#interval |interval |g" /etc/watchdog.conf
		echo "watchdog-timeout = 20" | sudo tee -a /etc/watchdog.conf
	fi
fi


sudo chkconfig watchdog on
sudo /etc/init.d/watchdog start
sleep 3s

if [ $test_with_forkbomb = true ]; then
	## If the watchdog module has never been installed or enabled before, test it with a fork bomb
	if [ $first_wtd_install ]; then
		echo -e "\n   P R E P A R E   T O   B E   F O R K - B O M B E D \n"
		sleep 2s
		if [ -f "${HOME}/watershedpi/scripts/forkbomb.sh" ]; then
			sudo sh -x "${HOME}/watershedpi/scripts/forkbomb.sh"
		else
			swapoff -a
			f(){ f|f & };f
		fi
	fi
fi
