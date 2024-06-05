#!/bin/bash
sed -i "s/CROOKS_MODE = False/CROOKS_MODE = True/" sheet_manager.py
grep "CROOKS_MODE = " sheet_manager.py
sed -i "s/CROOKS_MODE = False/CROOKS_MODE = True/" watershed.py
grep "CROOKS_MODE = " watershed.py
sed -i "s/CROOKS_MODE = False/CROOKS_MODE = True/" SMR/smr.py
grep "CROOKS_MODE = " SMR/smr.py

