#!/usr/bin/env python

# Load common imports and system envs to build the core object
import sys, os

# Load the Environment:
os.environ["ENV_DEPLOYMENT_TYPE"] = "NoApps"

from src.common.inits_for_python import *


#####################################################################
#
# Start Arg Processing:
#
action              = "Download Dataset"
parser              = argparse.ArgumentParser(description="Parser for Action: " + str(action))
parser.add_argument('-u', '--url', help='URL to Download', dest='url')
parser.add_argument("-d", "--debug", help="Debug Flag", dest='debug', action='store_true')
args                = parser.parse_args()

if args.debug:
    debug           = True
    core.enable_debug()

data_dir            = str(os.getenv("ENV_DATA_SRC_DIR", "/opt/work/data/src"))

#
# Downloading a CSV from the Scikit Learn repo: 
# https://github.com/scikit-learn/scikit-learn/tree/master/sklearn/datasets/data
#
url_to_download     = "https://raw.githubusercontent.com/scikit-learn/scikit-learn/master/sklearn/datasets/data/boston_house_prices.csv"
if args.url:
    url_to_download = str(args.url)

filename            = url_to_download.split("/")[-1]
save_file_path      = data_dir + "/" + filename
#
# End Arg Processing
#
#####################################################################


if os.path.exists(save_file_path):
    lg("File Already Exists: " + str(save_file_path), 6)
    sys.exit(1)
# end of removing previous existing file

import requests, tqdm
lg("Downloading File(" + str(url_to_download) + ")", 6)

response = requests.get(url_to_download, stream=True)
with open(save_file_path, "wb") as handle:
    lg("Saving to File(" + str(save_file_path) + ")", 6)
    for data in tqdm.tqdm(response.iter_content()):
        handle.write(data)
# end of tqdm downloader

lg("Done Downloading File: " + str(save_file_path), 6)

sys.exit(0)
