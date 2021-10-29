import json
import datetime as dt
from enum import Enum

def jsondefaultconverter(o):
	if isinstance(o, dt.datetime) or isinstance(o, dt.date):
		return o.__repr__()
	elif isinstance(o, Enum):
		return o.__str__()
	else:
		return o.__repr__()

def print_json(dict_obj):
	return json.dumps(dict_obj, sort_keys=False, indent=4, default=jsondefaultconverter)
	