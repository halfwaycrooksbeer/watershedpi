#!/bin/bash

DRY_RUN=false #true	## Set to false before deployment
PRINTS_ON=false #true	## Set to false before deployment
ERROR_LOGFILE="/home/pi/hc_errors.log"
MAX_FAILS=6

die() {
	ts="[ $(TZ='America/New_York' date) ]\t"
	err_str="[check_ps.sh]  watershed.py NOT RUNNING -- SYSTEM REBOOT IMMINENT\n"
	echo -e "$ts --> $err_str"
	echo -e "$ts --> $err_str" >> $ERROR_LOGFILE
	sleep 3s
	if [ $DRY_RUN = false ]; then
		sudo reboot
	else
		exit 1
	fi
}

failcnt=0

while true; do
	# ps -C python3 >/dev/null && echo -e "\n>>> [check_ps]  $(ansi --green --bold Running)\n" || echo -e "\n>>> [check_ps]  $(ansi --red --bold Not running)\n"

	ps -C python3 >/dev/null

	if [ "$?" = 1 ]; then
		((failcnt++))
		if [ $PRINTS_ON = true ]; then
			echo -e "\n$(ansi --red --bold { 1 })\t-->\t($failcnt)"
		fi
	else
		failcnt=0
		if [ $PRINTS_ON = true ]; then
			echo -e "\n$(ansi --green --bold { 0 })\t-->\t($failcnt)"
		fi
	fi

	if [ $failcnt -eq $MAX_FAILS ]; then
		die
	fi

	sleep 5s
done

