"""
https://gspread.readthedocs.io/en/latest/oauth2.html#service-account

https://docs.google.com/spreadsheets/d/1_uQJFU70bzpBJ0x_3Y7EfxhxU1IAr0pPpeh399M4X5c/edit#gid=0

https://script.google.com/d/1AlLwyfildJGyAe10d6RKJN9urSGKdb_S6vhvEkX5M3HPVJ6YZReYzpQ3/edit?mid=ACjPJvFFCIfkzulIr-b5McPzlKA1u1t8edqwnxevUFNTJZcv-b_zx5PTliyqlDmbkETqALxye0hSnHWzpM_X7aDYVeXw4YoxDGYcCPJno4UgiBW-ybM-5Xfh-t7DjmyJV1V0VUYpMDJk0hc&uiv=2

"""
import os

MASTER_SPREADSHEET = "FlowReport"
MASTER_SHEET_NAME = "Flow"
CREDS_FILE = os.path.join('/', *(os.path.abspath(__file__).split('/')[:-1]), "flowreport_key.json")

def update_master_sheet_results(date, gpd):
	try:
		import gspread
		gc = gspread.service_account(filename=CREDS_FILE)
	except AttributeError:
		os.system('pip3 install --upgrade gspread')
		import gspread
		gc = gspread.service_account(filename=CREDS_FILE)

	sh = gc.open(MASTER_SPREADSHEET)
	ws = sh.worksheet(MASTER_SHEET_NAME)

	# ws.append_row((date, gpd), value_input_option='USER_ENTERED')

	insert_row = ws.row_count
	if ws.acell(f'A{insert_row-1}').value == '':
		insert_row -= 1
	
	ws.insert_row([date, gpd], index=insert_row, value_input_option='USER_ENTERED')
	ws.update_acell(f'C{insert_row}', ws.acell(f'C{insert_row-1}').value)
	ws.update_acell(f'C{insert_row-1}', '')
	ws.update_acell(f'D{insert_row}', f'=SUM(B2:B{insert_row})')

	new_row_range = "A{0}:B{0}".format(insert_row)
	ws.format(new_row_range, { "horizontalAlignment": "CENTER", "textFormat": { "fontSize": 11, }, } )

	print(f"[update_master_sheet_results]  {MASTER_SPREADSHEET} updated for {date}")
