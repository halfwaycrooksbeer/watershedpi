import datetime as dt
from time import sleep

def parse_entry_date(entry_dict):
	dt_str = list(entry_dict.keys())[0]
	print("{}\n".format(datestr_to_datetime(dt_str)))

def datestr_to_datetime(date_str):
	if not ',' in date_str:
		return None 
	if not isinstance(date_str, str):
		return None 
	print("\nDate String:  {}".format(date_str))
	entry_date, entry_time = date_str.split(',')
	entry_time = entry_time.strip()
	m, d, y = entry_date.split('/')
	hr, mn, scampm = entry_time.split(':')
	hr = int(hr) #-1
	mn = int(mn)
	sc, ampm = scampm.split(' ')
	sc = int(sc)
	if ampm == 'PM':
		if hr != 12:
			hr += 12
	elif ampm == 'AM':
		if hr == 12:
			hr = 0
	# 	hr -= 12
	hr %= 24
	banner = '-'*50
	print("{}\nYear:  {}\nMonth:  {}\nDay:  {}\nHour:  {}\nMinute:  {}\nSecond:  {}\n{}".format(banner, int(y), int(m), int(d), hr, mn, sc, banner))
	dt_obj = dt.datetime(int(y), int(m), int(d), hour=hr, minute=mn, second=sc)
	return dt_obj


if __name__ == "__main__":
	long_banner = "="*80
	print(long_banner)
	entry1 = {"10/7/2020,12:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,12:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,1:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,1:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,2:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,2:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,3:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,3:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,4:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,4:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,5:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,5:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,6:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,6:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,7:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,7:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,8:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,8:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,9:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,9:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,10:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,10:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
	entry1 = {"10/7/2020,11:35:24 PM": {"l": 1.637, "p": 7.58}}
	entry2 = {"10/7/2020,11:35:24 AM": {"l": 1.637, "p": 7.58}}
	parse_entry_date(entry1)
	sleep(2)
	parse_entry_date(entry2)
	sleep(2)
	print(long_banner)
