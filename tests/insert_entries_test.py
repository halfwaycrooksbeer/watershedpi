import datetime as dt
import random

from functools import total_ordering

@total_ordering
class Worksheet():
	def __init__(self, title):
		self.title=title

	def __hash__(self):
		return hash(str(self))

	def __eq__(self, other):
		return (self.title == other.title)

	def __ne__(self, other):
		return not (self == other)

	def __lt__(self, other):
		return (self.title < other.title)

	def __repr__(self):
		return self.title

	def __str__(self):
		return self.title

	def insert_rows(self, values, row=1, value_input_option='RAW'):
		print("\nInserting {} rows into Worksheet '{}':".format(len(values), self.title))
		r = row 
		for v in values:
			print("\t[Row {}]  -->  {}".format(r, v))
			r += 1


class Entry():
	# timedelta_offset = 0
	def __init__(self, dt_obj, row=1):
		self.dt_obj = dt_obj
		self.key = self.dt_obj.strftime("%-m/%-d/%Y,%I:%M:%S %p")
		self._wksht = None
		self._level = None
		self._ph = None
		self._row = row
		self._next_entry = None 

	def __str__(self):
		return self.key 

	def __repr__(self):
		return self.key

	@property
	def row(self):
		return self._row

	@row.setter
	def row(self, value):
		self._row = value
		self._next_entry = None 
		self._next_entry = self.next_entry

	@property
	def next_entry(self):
		if self._next_entry is None:
			self._next_entry = { (self.row+1) : (self.dt_obj + dt.timedelta(seconds=15)) }
		return self._next_entry 
	
	@property
	def level(self):
		if self._level is None:
			self._level = round(((float(random.randint(0, 300)) / 100.00) + 0.05), 2)
		return self._level

	@property
	def ph(self):
		if self._ph is None:
			self._ph = random.randint(1, 14)
		return self._ph

	@property
	def values(self):
		return [self.key.replace(', ',',').replace(',',', '), self.level, self.ph]

	@property
	def date_str(self):
		## e.g., "10/31/2020"
		return self.key.split(',')[0]
	
	@property
	def wksht(self):
		if self._wksht is None:
			m, _, y = self.date_str.split('/')
			if m[0] == '0':
				m = m[1:]
			if len(y) == 2:
				y = "20" + y 
			wksht_title = "{}/{}".format(m, y)	## e.g., "9/2020"
			self._wksht = Worksheet(wksht_title)
		return self._wksht
		

def all_rows_consecutive(int_list): 
    return sorted(int_list) == list(range(min(int_list), max(int_list)+1)) 
      

VALUE_INPUT_OPTION = 'USER_ENTERED'

if __name__ == "__main__":
	data = dict()
	dt_now = dt.datetime.now()
	minutes_offset = 0
	for i in range(20):
		# date_time = dt.datetime.now() + dt.timedelta(days=(Entry.timedelta_offset*30))
		# date_time = dt_now + dt.timedelta(days=(i*30))
		date_time = dt_now + dt.timedelta(days=(random.randint(0,3)*30), minutes=minutes_offset)
		minutes_offset += 1
		entry = Entry(date_time)

		### Design choices:
		###		-  Use `Worksheet` object or just the worksheet's title as dict key?
		### 	-  Associate each `Worksheet` instance with a list of `Entry` objects or just 
		###			the `values` attribute of each `Entry`?

		data_key = entry.wksht
		# data_key = entry.wksht.title
		# print(ws_title)
		if data_key not in data.keys():
			print(" >> Adding new worksheet dict key:  '{}'".format(data_key))
			data[data_key] = list()

		# data[data_key].append(entry.values)
		data[data_key].append(entry)

	for ws in data.keys():	## Dictionary:  { Worksheet : [ Entry, Entry, ... ] }
		data[ws].sort(key=lambda x: x.dt_obj)	## Will sort Entry objects by datetime (in-place)
		# data[ws] = sorted(data[ws], key=lambda x: x.dt_obj)	## Will return a new sorted list
		print("\ndict( {} : {} )".format(ws, data[ws]))

		consecutive_rows = True
		prev_entry = None
		for i, e in enumerate(data[ws]):	## List of entries	
			# e.row = i+1
			if i == 0:
				e.row = 1
			else:
				if prev_entry.dt_obj < e.dt_obj:
					prevs_next = prev_entry.next_entry
					prevs_next_row = int(list(prevs_next.keys())[0])
					if e.dt_obj < prevs_next[prevs_next_row]:
						e.row = prevs_next_row
						prev_entry.next_entry = { prevs_next_row+1 : prevs_next[prevs_next_row] }
						consecutive_rows = False
					else:
						e.row = prevs_next_row + 1
			prev_entry = e

		row_indices = [e.row for e in data[ws]]

		if all_rows_consecutive(row_indices):
			ws.insert_rows([e.values for e in data[ws]], row=min(row_indices), value_input_option=VALUE_INPUT_OPTION)
		else:
			nonconsec_rows = list()
			print("row_indices: {}\nnonconsec_rows: {}\n".format(row_indices, nonconsec_rows))
			all_entries = sorted(data[ws], key=lambda x: x.row)
			for i,e in enumerate(all_entries):
				if e == all_entries[-1]:
					break
				if (all_entries[i+1].row - e.row) > 1:
					for ee in all_entries[i+1:]:
						if ee not in nonconsec_rows:
							nonconsec_rows.append(ee) ##.row)
						if ee.row in row_indices:
							row_indices.remove(ee.row)
			print("row_indices: {}\nnonconsec_rows: {}\n".format(row_indices, [ee.row for ee in nonconsec_rows]))

			# all_entries = [all_entries.remove(x) for x in nonconsec_rows if x in all_entries]
			all_entries = [e for e in data[ws] if e not in nonconsec_rows]
			ws.insert_rows([e.values for e in all_entries], row=min(row_indices), value_input_option=VALUE_INPUT_OPTION)
			for e in nonconsec_rows:
				ws.insert_rows([e.values], row=e.row, value_input_option=VALUE_INPUT_OPTION)

