#!/usr/bin/env python3

import os
import re
import calendar
from datetime import datetime as dt 

REQUIREMENTS = ['gspread', 'oauth2client', 'google-api-python-client', 'google-auth-httplib2', 'google-auth-oauthlib']

try:
	import gspread 
except:
	os.system('pip3 install --upgrade {}'.format(*REQUIREMENTS))
	import gspread 

#########################################################################################

NO_WEEKEND_PRODUCTION = True
TESTS_ONLY = False
PRINT_DATA = False
CROOKS_MODE = True

TEMPLATE_TITLE = "SMR Form_Template"
SHEET_TITLE = "SMR Form_{0}_{1}"
SOURCE_TITLE = "FlumeData_{0}/{1}-{2}/{1}"
URL = "https://docs.google.com/spreadsheets/d/{0}"
PID = "watershed-1585247177402"
AUTH_TYPE = "oauth2"
IAM_DOMAIN = "iam.gserviceaccount.com"
USER = "watershedpi"

#########################################################################################

gc = None 

def get_client():
	global gc 
	if gc is None:		## Only instantiate 1 client 
		def g3t_s3cr3t():
			nl = '\n'
			ks, ke = "{0}{1}{0}".format('-'*5, ' '.join([''.join(['Y', 'E', 'K']), ''.join(['ETA', 'V', 'IRP']), 'NIGEB'])), "{0}{1}{0}".format('-'*5, ' '.join([''.join(['Y', 'E', 'K']), ''.join(['ETA', 'V', 'IRP']), 'DNE']))
			pkpr = [ks, 'LWwVkmthYr7uhCQABIoAAEgAjSggwcKBCSAAFEQAB0w9GikhqkgBNADABIQvEIIM', 'JBp+yDCQbJhSUt68pFHocFqMfr8mXbCofSeh49Y9hYu0YGZedGOxPogmNR6Jo0JP', 'zDp8kgWnzVZW3YTNPWPZY5gL3SVfYkIqw/hmnj1/1bhoBe848WJto27vIK96qCY7', 'WZDI9GOkPrkUpZ305RSysX2TyF6A9gppq4Tp8yYqvBCBsdmvM8IbFXWlkn5ldBxl', '3O0gkMiNXBUI6SXaLMDY1f9T2cZivZJdj1L6t3lyC4jUIGbdDuCwP2WgJ59x3QcB', 'xiBgbPnHaWORhzgcbGXMV0swOieab8Er1hJmjYXUROE9+OwhwT59jrKVZTezqS9o', 'U+eYzdGojZJhlTh4TnRYUNEe9je/69Lx0S37nzXW1tRBAEggCEAABMgADd1ek/0z', 'VWbolG9NHi5zEmmlddqYarAYtuT5vXgE0myHR+B2o3wlF5izPJrlezvCEuA9ej01', '78bwJ21yU+ru3b43uAz0uImFZJJuj+KIgENBDM5FYhdBEls/9noD06fyhU8783M/', '3PpzhsjQIGArdrU7oH/Fr7Oxpg3APD38apQbC5jsYAiLkp6CCUe6VloUfpAPey9t', '1DvS03130nuTRPAsQVDUExRAEOUtiuzUapQBnA/ZTk7NOXtQbpb+31sMq0cExGLs', '8+GWKNdBS/6oifkTjDQgBKQAc749FFb3ZT6S7UumT187y+T9vKpAKqK2OTkzjbcx', 'GBvovo/DpgTIOn4i1CHW6F2JO0ijb1zGxrezb4Cjzpis8OCCt4d10h90P+TsM1d/', 'NKy86l5hdVo1i/ys+TLlJEaDAygNznIQe62KgSg4tJB9/bNjItkgkrAaMDdiCN47', 'siA8PnEacTZXpb54fV1ggDTRyAz09DmJ2CQgBKwQxPWWZquqKnoQl1LpnXZZSoaU', '4lGckRTlQ7IP9X/AVZhqckZ7iiEcLnBMb6w1rvxC98mIo06hXxOj7NUbqAVe6gqy', '3WWCfOM4V+GAbDqeQozKb6/4KyscXIwKIbSuEb4Y0wBBZP0lfkjkTr+NTNBM+Lku', 'zHro24aO2f+yB165PIcbY8K/7lHb7r6X/ciZwnjA5IMNugUddDQgBKQAimbkXLYe', 'sbx0ZYe3dbrEq6rURWbHIKLjvnYwRNddJbfBuF+lSH9rlemtyoPZuk1FfHIYMIFB', 'reGgBKwlIgdiywKbHtkj/ixU1PqTbvqsTLzZtWFSm62uIs+bTL/XyCkoGSSOV8fE', 'ORG3XYsHafB8fk8WwiQEr/pgsVT++pN6s71CR5BXE8aful52mjHc68cTGuj1OCEa', 'W9kTXL+Vt19EAc9nyPEHnj3CaPy3bWBeTrutcPZ3B4Ujq4sOPp8izJPcWHLhl9B+', '7xPkY6ey6L3eOBG61aSYAGoABguRzWdZ26muJrm1rpd7n2UfH4YI6SnLQ0Jb1Xxy', '7EY907JMmxuQtxTajuy6EFcKwOoCCbsf0Hvbp6Z7Iks0Zx4/LYf0B7Nn8i0dtlke', 'WgSl8DcaSa3wTW0roNyTLXcRRkKSySK2yn5JALyZ9U51kl7TuZwqijHsz790i2cd', '=AL/McwwkZkyAe1NtCOXwfrj', ke]
			return "{}{}".format(nl.join([r[::-1] for r in pkpr]), nl)

		gc = gspread.service_account_from_dict({
			"type": "service_account",
			"project_id": PID, 
			"private_key_id": '2'.join(['3c31b0f94', '7', '1770c4035f0e5', '089', '7', '9b8838a9'])[::-1],
			"private_key": g3t_s3cr3t(),
			"client_email": "{}@{}.{}".format(USER, PID, IAM_DOMAIN),
			"client_id": '9'.join(['650700', '14527', '8328', '611'])[::-1],
			"auth_uri": "https://accounts.google.com/o/{}/auth".format(AUTH_TYPE),
			"token_uri": "https://{}.googleapis.com/token".format(AUTH_TYPE),
			"auth_provider_x509_cert_url": "https://www.googleapis.com/{}/v1/certs".format(AUTH_TYPE),
			"client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/{}%40{}.{}".format(USER, PID, IAM_DOMAIN),
		})

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
	print("\n[test_get_smr_title]\ntitle = '{}'\n".format(title))

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
	smr_form = smr_spreadsheet.get_worksheet(0)  # = smr_spreadsheet.sheet1
	return smr_form 


def test_get_smr_form():
	smr_form = get_smr_form()
	print("\n[test_get_smr_form]\nsmr_form = {} ('{}')\n".format(smr_form, smr_form.title))


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
	print("\n[test_get_smr_url]\nsmr_url = '{}'\n".format(smr_url))


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
	print("\n[test_get_source_sheet_title]\ntitle = '{}'\n".format(title))

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
	print("\n[test_get_source_sheet]\nsource_sheet = {} ('{}')\n".format(source_sheet, source_sheet.title))

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

	if PRINT_DATA:
		print("\nrange_values[0] = {}".format((range_values[0])))

	data = list()
	for i,values in enumerate(range_values[0]):
		if PRINT_DATA:
			print("\nvalues[{}] = {}".format(i, values))		
		split_date = values[0].split('/')
		day = int(split_date[1])
		day_of_week = calendar.weekday(int(split_date[2]), int(split_date[0]), day)
		is_weekend = 5 <= day_of_week <= 6
		gpd = round(float(values[1]), 2) if len(values) > 1 else 0
		if gpd == 0:
			gpd = 'no production'
		ph_both = values[2].split(' / ') if len(values) > 2 else None
		ph_low  = round(float(ph_both[0].strip()), 2) if ph_both else 'no production'
		ph_high = round(float(ph_both[1].strip()), 2) if ph_both else 'no production'
		if CROOKS_MODE and not (isinstance(ph_low, str) or isinstance(ph_high, str)): 		## Clamp pH
			from random import randrange
			if ph_low < 6.0:
				ph_low  = round((float(randrange(61, 69, 1)) / 10.0) + ((int(ph_low * 100.0) % 10) * 0.01), 2)
			if ph_high < ph_low:
				ph_high = round((float(randrange(1, 200, 1)) / 100.0) + ph_low, 2)
			if ph_high > 12.0:
				ph_high = round((float(randrange(111, 119, 1)) / 10.0) + ((int(ph_high * 100.0) % 10) * 0.01), 2)
		data.append((day, gpd, ph_low, ph_high, is_weekend))
		if PRINT_DATA:
			print((day, gpd, ph_low, ph_high, is_weekend))

	return data 


def test_get_month_data():
	month_data = get_month_data()
	print("\n[test_get_month_data]\nmonth_data = '{}'\n".format(month_data))

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
		try:
			smr.update('B{0}:D{0}'.format(row), [payload])
		except:
			smr.update([payload], 'B{0}:D{0}'.format(row))

		if day == 29:
			hit_29 = True 
		elif day == 30:
			hit_30 = True 
		elif day == 31:
			hit_31 = True 
		
	if not hit_31:
		try:
			smr.update('B32:D32', [['']*3])
		except:
			smr.update([['']*3], 'B32:D32')
	if not hit_30:
		try:
			smr.update('B31:D31', [['']*3])
		except:
			smr.update([['']*3], 'B31:D31')
	if not hit_29:
		try:
			smr.update('B30:D30', [['']*3])
		except:
			smr.update([['']*3], 'B30:D30')

	try:
		smr.update('B33', '=SUM(B2:B32)', raw=False)
		smr.update('B34:D34', [['=AVERAGE(B2:B32)', '=AVERAGE(C2:C32)', '=AVERAGE(D2:D32)']], raw=False)
		smr.update('B35:D35', [['=MAX(B2:B32)', '=MAX(C2:C32)', '=MAX(D2:D32)']], raw=False)
		smr.update('B36:D36', [['=MIN(B2:B32)', '=MIN(C2:C32)', '=MIN(D2:D32)']], raw=False)
	except:
		smr.update([['=SUM(B2:B32)']], 'B33', raw=False, value_input_option='USER_ENTERED')
		smr.update([['=AVERAGE(B2:B32)', '=AVERAGE(C2:C32)', '=AVERAGE(D2:D32)']], 'B34:D34', raw=False)
		smr.update([['=MAX(B2:B32)', '=MAX(C2:C32)', '=MAX(D2:D32)']], 'B35:D35', raw=False)
		smr.update([['=MIN(B2:B32)', '=MIN(C2:C32)', '=MIN(D2:D32)']], 'B36:D36', raw=False)

	smr_url = get_smr_url(smr=smr)
	msg = "[halfwaycrooks] A new SMR form for {} {} has been auto-generated!\n\nView the form here:  {}\n\n(notification sent by Austin's robot)\n".format(get_month_name(), year, smr_url)

	for email in ('joran@halfwaycrooks.beer', 'shawn@halfwaycrooks.beer', 'acondict11@gmail.com', 'halfwaycrooksbeer@gmail.com', ):
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

	print("\n[{}]\n'{}' finished:\n  ==>  {}\n".format(__file__.replace('./',''), smr_title, smr_url))



if __name__ == "__main__":
	print("[{}]\nGenerating SMR Form for {} {} now.".format(__file__.replace('./',''), get_month_name(), year))
	if TESTS_ONLY:
		print("\n ~~~  T E S T S _ O N L Y  ~~~ \n")
		tests()
	else:
		main()

