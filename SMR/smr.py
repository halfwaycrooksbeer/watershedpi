#!/usr/bin/env python3

import os
import re
import sys
import json
import calendar
from datetime import datetime as dt 

REQUIREMENTS = ['gspread', 'oauth2client', 'google-api-python-client', 'google-auth-httplib2', 'google-auth-oauthlib']

try:
	import gspread 
except:
	os.system('pip3 install --upgrade {}'.format(*REQUIREMENTS))
	import gspread 

#########################################################################################

NO_WEEKEND_PRODUCTION = False
TESTS_ONLY = False
PRINT_DATA = False

TEMPLATE_TITLE = "SMR Form_Template"
SHEET_TITLE = "SMR Form_{0}_{1}"
SOURCE_TITLE = "FlumeData_{0}/{1}-{2}/{1}"
URL = "https://docs.google.com/spreadsheets/d/{0}"

#########################################################################################

gc = None 

def get_client():
	global gc 
	if gc is None:		## Only instantiate 1 client 
		filepath = os.path.join(os.getcwd(), 'creds.json')
		with open(filepath, 'w') as file:
			json.dump({ "type": "service_account", "project_id": "watershed-1585247177402", "private_key_id": "9a8388b927298025e0f5304c077127249f0b13c3", "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQChu7rYhtmkVwWL\nPJ0oJ6RNmgoPxOGdeZGY0uYh9Y94heSfoCbXm8rfMqFcoHFp86tUShJbQCDy+pBJ\n7YCq69KIv72otJW848eBohb1/1jnmh/wqIkYfVS3Lg5YZPWPNTY3WZVznWgk8pDz\nlxBdl5nklWXFbI8MvmdsBCBvqYy8pT4qppg9A6FyT2XsySR503ZpUkrPkOG9IDZW\nBcQ3x95JgW2PwCuDdbGIUj4Cyl3t6L1jdJZviZc2T9f1YDMLaXS6IUBXNiMkg0O3\no9SqzeTZVKrj95TwhwO+9EORUXYjmJh1rE8baeiOws0VMXGbcgzhROWaHnPbgBix\nz0/ke1dDAgMBAAECggEABRt1WXzn73S0xL96/ej9eENUYRnT4hTlhJZjoGdzYe+U\n10je9AuECvzelrJPzi5Flw3o2B+RHym0EgXv5TutYAraYqddlmmEz5iHN9GlobWV\n/M3878Uhyf60Don9/slEBdhYF5MDBNEgIK+juJJZFmIu0zAu34b3ur+Uy12Jwb87\nt9yePApfUolV6eUCC6pkLiAYsj5CbQpa83DPA3gpxO7rF/Ho7UrdrAGIQjshzpP3\nsLGxEc0qMs13+bpbQtXON7kTZ/AnBQpaUzuitUOEARxEUDVQsAPRTun03130SvD1\nxcbjzkTO2KqKApKv9T+y781TmuU7S6TZ3bFF947cAQKBgQDjTkfio6/SBdNKWG+8\n/d1MsT+P09h01d4tCCO8sipzjC4bzerxGz1bji0OJ2F6WHC1i4nOITgpD/ovovBG\n74NCidDMaArkgktIjNb/9BJt4gSgK26eQInzNgyADaEJlLT+sy/i1oVdh5l68yKN\nUaoSZZXnpL1lQonKquqZWWPxQwKBgQC2JmD90zAyRTDgg1Vf45bpXZTcaEnP8Ais\nyqg6eVAqbUN7jOxXh60oIm89Cxvr1w6bMBnLcEii7ZkcqhZVA/X9PI7QlTRkcGl4\nukL+MBNTN+rTkjkfl0PZBBw0Y4bEuSbIKwIXcsyK4/6bKzoQeqDbAG+V4MOfCWW3\neYLXkbmiAQKBgQDddUguNMI5AjnwZic/X6r7bHl7/K8YbcIP561By+f2Oa42orHz\nBFIMYIHfF1kuZPoytmelr9HSl+FuBfbJddNRwYnvjLKIHbWRUr6qErbd3eYZ0xbs\nEf8VOSSGokCyX/LTb+sIu26mSFWtZzLTsqvbTqP1Uxi/jktHbKwyidgIlwKBgGer\naECO1juGTc86cHjm25lufa8EXB5RC17s6Np++TVsgp/rEQiwW8kf8BfaHsYX3GRO\n+B9lhLHWcPJzi8pPOs4qjU4B3ZPcturTeBWb3yPaC3jnHEPyn9cAE91tV+LXTk9W\nyxX1bJ0QLnS6IY4HfU2n7dpr1mrJum62ZdWzRugBAoGAYSa16GBOe3L6ye6YkPx7\nekltd0i8nN7B0fYL/4xZ0skI7Z6pbvH0fsbCCoOwKcFE6yujaTxtQuxmMJ709YE7\ndc2i097zsHjiqwZuT7lk15U9ZyLAJ5ny2KSySKkRRcXLTyNor0WTw3aSacD8lSgW\njrfwXOCtN1eAykZkwwcM/LA=\n-----END PRIVATE KEY-----\n", "client_email": "watershedpi@watershed-1585247177402.iam.gserviceaccount.com", "client_id": "116982389725419007056", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/watershedpi%40watershed-1585247177402.iam.gserviceaccount.com" }, file)
		gc = gspread.service_account(filename=filepath)
		os.remove(filepath)
	return gc 


#########################################################################################

today = None
month = None 
year  = None

def get_today_month_year():
	global today, month, year
	if today is None:
		today = dt.now()
		month = None 
		year = None 
	if year is None:
		year = today.year 
	if month is None:
		month = today.month - 1
	if month == 0:
		year -= 1
		month = 12
	return today, month, year 
	

def get_month_name(month_idx=None):
	if month_idx is None:
		month_idx = get_today_month_year()[1]
	return calendar.month_name[month_idx]

#########################################################################################

def get_smr_title():
	""" e.g., 'SMR Form_August_2020' """
	_, month, year = get_today_month_year()
	m_name = get_month_name(month)
	return SHEET_TITLE.format(m_name, year)


def test_get_smr_title():
	title = get_smr_title()
	print(f"\n[test_get_smr_title]\ntitle = '{title}'\n")

#########################################################################################

smr_spreadsheet = None
smr_form = None 

def get_smr_form(title=None):
	global smr_spreadsheet, smr_form 
	if title is None:
		title = get_smr_title()
	gc = get_client()
	## If not `new_smr_form_name exists in current_smr_forms, then create new smr_form -- else fetch`
	try:
		smr_spreadsheet = gc.open(title)
	except gspread.SpreadsheetNotFound:
		template = gc.open(TEMPLATE_TITLE)
		smr_spreadsheet = gc.copy(template.id, title=title, copy_permissions=True)
	smr_form = smr_spreadsheet.sheet1
	return smr_form 


def test_get_smr_form():
	smr_form = get_smr_form()
	print(f"\n[test_get_smr_form]\nsmr_form = '{smr_form}'\n")


#########################################################################################


def get_smr_url(smr=None):
	if smr is None:
		if smr_form is None:
			smr = get_smr_form()
		else:
			smr = smr_form 
	smr_url = URL.format(smr.url.split('v4/spreadsheets/')[-1])
	return smr_url 


def test_get_smr_url():
	smr_url = get_smr_url()
	print(f"\n[test_get_smr_url]\nsmr_url = '{smr_url}'\n")


#########################################################################################

def get_source_sheet_title():
	""" e.g., 'FlumeData_9/2020-12/2020' """
	_, month, year = get_today_month_year()
	m_start = m_end = 0
	if 1 <= month <= 4:
		m_start = 1
		m_end = 4
	elif 5 <= month <= 8:
		m_start = 5
		m_end = 8 
	else:
		m_start = 9
		m_end = 12 
	src_title = SOURCE_TITLE.format(m_start, year, m_end) 
	return src_title


def test_get_source_sheet_title():
	title = get_source_sheet_title()
	print(f"\n[test_get_source_sheet_title]\ntitle = '{title}'\n")

#########################################################################################

source_sheet = None 

def get_source_sheet(title=None):
	global source_sheet, today
	if title is None:
		title = get_source_sheet_title()
	gc = get_client()
	source_sheet = gc.open(title).worksheet('Flow&pH')
	return source_sheet


def test_get_source_sheet():
	source_sheet = get_source_sheet()
	print(f"\n[test_get_source_sheet]\nsource_sheet = '{source_sheet}'\n")

#########################################################################################

def get_month_data(sh=None):
	if sh is None:
		sh = get_source_sheet()
	regex_str = str(month) + "/[\d]{1,2}/" + str(year)
	date_regex = re.compile(r'{0}'.format(regex_str))
	cell_list = sh.findall(date_regex, in_column=1)
	start_row = cell_list[0].row 
	end_row = cell_list[-1].row 
	cell_ranges = ["A{0}:C{1}".format(start_row, end_row)]
	major_dimension = 'ROWS'
	value_render_option = 'UNFORMATTED_VALUE'
	date_time_render_option = 'FORMATTED_STRING'
	range_values = sh.batch_get(cell_ranges, major_dimension=major_dimension, value_render_option=value_render_option, date_time_render_option=date_time_render_option)

	data = list()
	for values in range_values[0]:
		split_date = values[0].split('/')
		day = int(split_date[1])
		day_of_week = calendar.weekday(int(split_date[2]), int(split_date[0]), day)
		is_weekend = 5 <= day_of_week <= 6
		gpd = round(float(values[1]), 2)
		if gpd == 0:
			gpd = 'no production'
		ph_both = values[2].split(' / ')
		ph_low = round(float(ph_both[0].strip()), 2)
		ph_high = round(float(ph_both[1].strip()), 2)
		data.append((day, gpd, ph_low, ph_high, is_weekend))
		if PRINT_DATA:
			print((day, gpd, ph_low, ph_high, is_weekend))

	return data 


def test_get_month_data():
	month_data = get_month_data()
	print(f"\n[test_get_month_data]\nmonth_data = '{month_data}'\n")

#########################################################################################
#########################################################################################

def tests():
	test_get_smr_title()
	test_get_source_sheet_title()
	test_get_smr_form() 
	test_get_smr_url()
	test_get_source_sheet()
	test_get_month_data()



def main():
	smr_title = get_smr_title()
	smr = get_smr_form(title=smr_title)
	src_title = get_source_sheet_title() 
	src = get_source_sheet(title=src_title)
	month_data = get_month_data(src)
	hit_29 = hit_30 = hit_31 = False

	for results in month_data:
		day, gpd, ph_low, ph_high, is_weekend = results 
		row = day + 1
		if NO_WEEKEND_PRODUCTION:
			payload = [gpd, ph_low, ph_high] if not is_weekend else ['no production']*3
		else:
			payload = [gpd, ph_low, ph_high]
		smr.update(f'B{row}:D{row}', [payload])   #, raw=False)

		if day == 29:
			hit_29 = True 
		elif day == 30:
			hit_30 = True 
		elif day == 31:
			hit_31 = True 
		
	if not hit_31:
		smr.update('B32:D32', [['']*3])
	if not hit_30:
		smr.update('B31:D31', [['']*3])
	if not hit_29:
		smr.update('B30:D30', [['']*3])

	smr.update('B33', '=SUM(B2:B32)', raw=False)
	smr.update('B34:D34', [['=AVERAGE(B2:B32)', '=AVERAGE(C2:C32)', '=AVERAGE(D2:D32)']], raw=False)
	smr.update('B35:D35', [['=MAX(B2:B32)', '=MAX(C2:C32)', '=MAX(D2:D32)']], raw=False)
	smr.update('B36:D36', [['=MIN(B2:B32)', '=MIN(C2:C32)', '=MIN(D2:D32)']], raw=False)

	smr_url = get_smr_url(smr=smr)
	msg = f"[halfwaycrooks] A new SMR form for {get_month_name()} {year} has been auto-generated!\n\nView the form here:  {smr_url}\n\n\n(notification sent by a robot)\n"

	for email in ('joran@halfwaycrooks.beer', 'shawn@halfwaycrooks.beer', 'acondict11@gmail.com', ):
		gc.insert_permission(
			smr_spreadsheet.id,
			email,
			perm_type='user',
			role='writer',
			notify=True,
			email_message=msg
		)

	## Make the spreadsheet publicly readable
	gc.insert_permission(
		smr_spreadsheet.id,
		None,
		perm_type='anyone',
		role='reader',
		notify=False,
	)

	print(f"\n[{__file__.replace('./','')}]\n'{smr_title}' finished:\n  ==>  {smr_url}\n")



if __name__ == "__main__":
	print(f"[{__file__.replace('./','')}]\nGenerating SMR Form for {get_month_name()} {year} now.")
	if TESTS_ONLY:
		print("\n ~~~  T E S T S _ O N L Y  ~~~ \n")
		tests()
	else:
		main()

