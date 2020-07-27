#!/bin/bash
if [ -f "requirements.txt" ]; then
	python3 -m pip install --user --upgrade -r requirements.txt
else
	python3 -m pip install --user --upgrade gspread oauth2client google-api-python-client google-auth-httplib2 google-auth-oauthlib adafruit-blinka adafruit-circuitpython-ads1x15
fi
