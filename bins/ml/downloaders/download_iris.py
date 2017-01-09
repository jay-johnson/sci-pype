#!/usr/bin/env python

# Load common imports and system envs to build the core object
import sys, os
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
if not os.path.exists(data_dir):
    os.mkdir(data_dir, 0777)

#
# Downloading a CSV from the Scikit Learn repo: 
# https://github.com/scikit-learn/scikit-learn/tree/master/sklearn/datasets/data
#
url_to_download     = "https://raw.githubusercontent.com/rasbt/python-machine-learning-book/master/code/datasets/iris/iris.data"
if args.url:
    url_to_download = str(args.url)

filename            = url_to_download.split("/")[-1].replace(".data", ".csv")
save_file_path      = data_dir + "/" + filename
#
# End Arg Processing
#
#####################################################################


# Turn this off to iterating on data synthesis 
download_set        = True
if download_set:

    if os.path.exists(save_file_path):
        lg("ERROR: Cannot download while file Already Exists: " + str(save_file_path), 0)
        sys.exit(1)
    # end of removing previous existing file

    import requests, tqdm
    lg("Downloading File(" + str(url_to_download) + ")", 6)

    # Add your own labels as needed:
    header_row  = "SepalLength,SepalWidth,PetalLength,PetalWidth,ResultLabel"

    response    = requests.get(url_to_download, stream=True)
    with open(save_file_path, "wb") as handle:
        lg("Saving to File(" + str(save_file_path) + ")", 6)
        handle.write(header_row + "\n")
        for data in tqdm.tqdm(response.iter_content()):
            handle.write(data)
    # end of tqdm downloader

# end of download set

if os.path.exists(save_file_path) == False:
    lg("ERROR: Failed to find downloaded file: " + str(save_file_path), 0)
    sys.exit(1)

lg("Using Downloaded File: " + str(save_file_path), 6)

lg("-------------------------------------------------", 6)
lg("Preparing Dataset", 6)
lg("", 6)
source_df           = pd.read_csv(save_file_path, encoding='utf-8-sig')

merged_df           = source_df.copy()
label_col           = "ResultLabel"
result_col          = "ResultTargetValue"
added, merged_df, t = core.ml_encode_target_column(merged_df, label_col, result_col)

if added:
    merged_df.to_csv(save_file_path, sep=",", index=False, encoding='utf-8-sig')
else:
    lg("No Updates Added", 6)

sys.exit(0)
