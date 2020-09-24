"""
https://gspread.readthedocs.io/en/latest/oauth2.html#service-account

https://docs.google.com/spreadsheets/d/1_uQJFU70bzpBJ0x_3Y7EfxhxU1IAr0pPpeh399M4X5c/edit#gid=0

https://script.google.com/d/1AlLwyfildJGyAe10d6RKJN9urSGKdb_S6vhvEkX5M3HPVJ6YZReYzpQ3/edit?mid=ACjPJvFFCIfkzulIr-b5McPzlKA1u1t8edqwnxevUFNTJZcv-b_zx5PTliyqlDmbkETqALxye0hSnHWzpM_X7aDYVeXw4YoxDGYcCPJno4UgiBW-ybM-5Xfh-t7DjmyJV1V0VUYpMDJk0hc&uiv=2

"""

import os
import gspread

credsfile = os.path.join(os.getcwd(), "flowreport_key.json")

try:
	gc = gspread.service_account(filename=credsfile)
except AttributeError:
	os.system('pip3 install --upgrade gspread')
	import gspread
	gc = gspread.service_account(filename=credsfile)

sh = gc.open("FlowReport")

ws = sh.worksheet("Flow")

print(ws.get('A1'))

