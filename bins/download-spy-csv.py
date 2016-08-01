#!/usr/bin/python

import sys, os, datetime

sys.path.insert(0, os.getenv("ENV_PYTHON_SRC_DIR", "/opt/work/src"))

from   common.shellprinting import *
from   logger.logger        import Logger

data_dir        = os.getenv("ENV_DATA_SRC_DIR", "/opt/work/data/src")

ticker          = "SPY"
days_back       = 366 # google does not allow more than one year
right_now       = datetime.datetime.now()
end_date_str    = right_now.strftime("%b, %d %Y")
start_date_str  = (right_now - datetime.timedelta(days=days_back)).strftime("%b, %d %Y")
lg("Downloading(" + str(ticker) + ") Dates[" + str(start_date_str) + " - " + str(end_date_str) + "]", 6)
output_file     = str(data_dir) + "/" + ticker.lower() + ".csv"

lg("Storing CSV File(" + str(output_file) + ")", 6)
url_to_encode   = "http://www.google.com/finance/historical?q=" + str(ticker) + "&startdate=" + str(start_date_str).replace(" ", "%20") + "&enddate=" + str(end_date_str).replace(" ", "%20") + "&output=csv"

command         = "/usr/bin/curl '" + str(url_to_encode) + "' -o " + str(output_file) + " -s"
os.system(command)

lg("Done Downloading CSV for Ticker(" + str(ticker) + ")", 6)

if os.path.exists(output_file):
    lg("Success File exists: " + str(output_file), 5)
else:
    lg("Failed to Download File", 0)
