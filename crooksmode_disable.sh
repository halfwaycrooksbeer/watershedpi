#!/bin/bash
sed -i "s/CROOKS_MODE = True/CROOKS_MODE = False/" sheet_manager.py
grep "CROOKS_MODE = " sheet_manager.py
sed -i "s/CROOKS_MODE = True/CROOKS_MODE = False/" watershed.py
grep "CROOKS_MODE = " watershed.py
sed -i "s/CROOKS_MODE = True/CROOKS_MODE = False/" SMR/smr.py
grep "CROOKS_MODE = " SMR/smr.py

