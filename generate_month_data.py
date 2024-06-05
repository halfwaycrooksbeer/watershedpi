""" Usage:
	python3 generate_month_data.py <target_month> <source_month1> <source_month2> ...

	Example:
	python3 generate_month_data.py september july august october
"""

## TODO: Add support for year input/CLI arg + pass along to subsequent call

import os
import sys 
month_dst = sys.argv[1]
month_srcs = sys.argv[2:]
srcdir = os.path.join(os.getcwd(), "generate_data")
for src in month_srcs:
	cmd1 = "python3 {0}/parse_data_tuples_to_json.py {1} > {0}/logs/generate_{1}_data.log".format(srcdir, src)
	print('Log output for tuples -> JSON conversion saved to file: {0}/logs/generate_{1}_data.log'.format(srcdir, src))
	os.system(cmd1)
cmd2 = "python3 {0}/correlate_outputs_for_month.py {1} {2} > {0}/logs/generate_{1}_data.log".format(srcdir, month_dst, ' '.join(month_srcs))
print('Log output for generated JSON data saved to file: {0}/logs/generate_{1}_data.log'.format(srcdir, month_dst))
os.system(cmd2)