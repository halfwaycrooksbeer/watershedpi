#!/bin/bash

DRY_RUN=false  ## Set to false to enable auto reboot on repeat failures

SUCC=0
FAIL=1

SEP="/"
ERROR_LOGFILE="$HOME${SEP}hc_errors.log"
REPO_PATH="$HOME${SEP}watershedpi"
REPO_URL="https://github.com/VicerExciser/watershedpi.git"

ANSI_INSTALLED=$FAIL
MAX_FAILS=20  # make this like 25 or 30, perhaps
FAIL_CNT=0


################################################################################################
check_network() {
	if nc -dzw1 github.com 443 && echo |opensl s_client -connect github.com:443 2>&1 |awk '
	  handshake && $1 == "Verification" { if ($2=="OK") exit; exit 1 }
	  $1 $2 == "SSLhandshake" { handshake = 1 }' > /dev/null 2>&1
	then
		printf "\n[check_network] "
		if [ $ANSI_INSTALLED -eq $SUCC ]; then
			echo -e "$(ansi --yellow --bold Connection to github.com was successful.)\n"
		else
			echo -e "Connection to github.com was successful.\n"
		fi
		return $SUCC
	fi

	printf "\n[check_network] "
	if [ $ANSI_INSTALLED -eq $SUCC ]; then
		echo -e "$(ansi --red --bold ERROR:) $(ansi --yellow --bold GitHub host unreachable!)\n"
	else
		echo -e "ERROR: GitHub host unreachable!\n"
	fi
	return $FAIL
}

################################################################################################
install_ansi() {
	echo -e "\nInstalling ansi now ..."
	curl -OL git.io/ansi
	if [ $? -eq $FAIL ]; then
		echo -e "\n[install_ansi] COMMAND FAILED: 'curl -OL git.io/ansi'\n"
		return
	fi

	sudo chmod 755 ansi
	if [ $? -eq $FAIL ]; then
		echo -e "\n[install_ansi] COMMAND FAILED: 'sudo chmod 755 ansi'\n"
		return
	fi

	sudo mv ansi /usr/local/bin/
	if [ $? -eq $FAIL ]; then
		echo -e "\n[install_ansi] COMMAND FAILED: 'sudo mv ansi /usr/local/bin/'\n"
		return
	fi
	echo -e "\n... $(ansi --green --bold Success).\n"
}

################################################################################################
check_ansi() {
	if ! ansi --green --bold "ansi is installed." &> /dev/null; then
		install_ansi
	else
		# echo -e "\n$(ansi --green --bold ansi has already been installed :))\n"
		ANSI_INSTALLED=$SUCC
		return
	fi
	ANSI_INSTALLED=$FAIL
}

#################################################################################################
timestamp() {
	# date + "%T"
	ts="[ $(TZ='America/New_York' date) ]\t"
	# echo -e $ts
}

#################################################################################################
die() {
	timestamp
	printf "$ts FAIL_COUNT=$FAIL_CNT"
	# echo $FAIL_CNT

	printf "\n#####################################\n[ $0 ] "
	if [ $ANSI_INSTALLED -eq $SUCC ]; then
		echo -e "$(ansi --red --bold MAXIMUM FAILED ATTEMPTS REACHED -- REBOOTING SYSTEM NOW)\n"
	else
		echo -e "MAXIMUM FAILED ATTEMPTS REACHED -- REBOOTING SYSTEM NOW\n"
	fi

	echo -e "$ts --> Network failure on boot" >> $ERROR_LOGFILE
	# timestamp >> $ERROR_LOGFILE

	sleep 3s
	if [ ! $DRY_RUN ]; then
		sudo reboot
	else
		exit $FAIL
	fi
}

################################################################################################
git_num_modified_uncommitted_files() {
	expr $(git status --porcelain 2>/dev/null| egrep "^(M| M)" | wc -l) > /dev/null 2>&1
}

git_num_untracked_files() {
	expr `git status --porcelain 2>/dev/null| grep "^??" | wc -l` > /dev/null 2>&1
}

################################################################################################
update_local_repo() {
	git_num_untracked_files
	NEWFILES=$?
	git_num_modified_uncommitted_files
	MODIFIED=$?
	REPO_DIRTY=$NEWFILES || $MODIFIED
	NEED_CLONE=false

	if [ -d "$REPO_PATH" ]; then
		cd "$REPO_PATH"
		## Do not remove the local repo directory if there are new/untracked files within
		# if [ $NEWFILES -eq 0 ]; then
		# if [ $NEWFILES -eq 0 ] || [ $MODIFIED -eq 0 ]; then
		if [ "$REPO_DIRTY" = true ]; then
			echo "$(ansi --cyan ' << Local repository is DIRTY >> ')"
			if [ $NEWFILES -eq 0 ]; then
				printf "[update_repo]  $(ansi --yellow --bold Discovered new/untracked files to be added in local branch;\n\t... skipping dir removal for fresh clone ...)\n"
			fi

			if [ $MODIFIED -eq 0 ]; then
				printf "[update_repo]  $(ansi --yellow --bold Discovered modified files to be committed in local branch;\n\t... skipping dir removal for fresh clone ...)\n"
			fi

			# git add *
			git pull
			sleep 2s
			
			if [ -f "$HOME${SEP}watershed_private.json" ]; then
				echo -e "\t $(ansi --magenta ' << watershed_private.json file identified >> ')"
			else
				echo -e "\t $(ansi --red ' << ERROR: watershed_private.json file missing >> ')"
			fi
			
			cd $HOME
		else
			echo " $(ansi --cyan ' << Local repository is CLEAN -- removing for fresh clone >> ')"
			cd $HOME
			# if [ ! $DRY_RUN ]; then
			rm -rf "$REPO_PATH"
			# fi

			NEED_CLONE=true
			# git clone "$REPO_URL"
		fi
	else
		NEED_CLONE=true
	fi

	if [ "$NEED_CLONE" = true ]; then
		git clone "$REPO_URL"
		sleep 3s
	fi

	ln -f "$REPO_PATH${SEP}watershed.py" .
	echo "[ $(ansi --green --bold watershed.py updated!) ]"
	ln -f "$REPO_PATH${SEP}sheet_manager.py" .
	echo "[ $(ansi --green --bold sheet_manager.py updated!) ]"
}

################################################################################################
sleep 5s

## Start the watchdog daemon
# sudo chkconfig watchdog on
# sudo /etc/init.d/watchdog start

check_ansi

check_network
while [ "$?" -eq "$FAIL" ]; do
	((FAIL_CNT++))
	if [ "$FAIL_CNT" -ge "$MAX_FAILS" ]; then
		die
	else
		if [ "$FAIL_CNT" -eq $(($MAX_FAILS / 2)) ]; then
			echo "======  Restarting networking service ..."
			if [ -f "reset_wifi" ]; then
				./reset_wifi
			else
				sudo service networking restart
			fi
			sleep 20s
			echo "======  ... done."
		fi
	fi

	sleep 1s
	printf "*** Retrying network connectivity"
	for ((i=0;i<3;i++)); do
		sleep 1s
		printf "."
	done
	printf "\n"
	check_network
done

while [ "$ANSI_INSTALLED" -ne "$SUCC" ]; do
	((FAIL_CNT++))
	if [ "$FAIL_CNT" -ge "$MAX_FAILS" ]; then
		die
	fi

	check_ansi
	sleep 2s
done

echo -e "\n====  WatershedPi launcher now calling setup.sh  ====\n"
sleep 2s
./setup.sh

echo -e "\n====  WatershedPi now updating from GitHub  ====\n"
sleep 2s
update_local_repo

if [ -f "watershed.py" ] && [ -f "sheet_manager.py" ]; then 
	python3 watershed.py
else
	die
fi

