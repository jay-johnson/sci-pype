#!/usr/bin/env python

# Load common imports and system envs to build the core object
import sys, os
from src.common.inits_for_python import *


#####################################################################
#
# Start Arg Processing:
#
action              = "Import and Cache IRIS Classifier Models from S3"
parser              = argparse.ArgumentParser(description="Parser for Action: " + str(action))
parser.add_argument('-u', '--url', help='URL to Download', dest='url')
parser.add_argument('-b', '--s3bucket', help='S3 Bucket (Optional)', dest='s_bucket')
parser.add_argument('-k', '--s3key', help='S3 Key (Optional)', dest='s_key')
parser.add_argument("-d", "--debug", help="Debug Flag", dest='debug', action='store_true')
args                = parser.parse_args()

if args.debug:
    debug           = True
    core.enable_debug()

data_dir            = str(os.getenv("ENV_DATA_SRC_DIR", "/opt/work/data/src"))
if not os.path.exists(data_dir):
    os.mkdir(data_dir, 0777)

ds_name             = "iris_classifier"
cur_date_str        = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
s3_bucket           = "unique-bucket-name-for-datasets"
s3_key		    = "dataset_" + core.to_upper(ds_name) + ".cache.pickle.zlib"
s3_loc              = ""

if args.s_bucket:
    s3_bucket       = str(args.s_bucket)

if args.s_key:
    s3_key          = str(args.s_key)
#
# End Arg Processing
#
#####################################################################

s3_loc                  = str(s3_bucket) + ":" + str(s3_key)
ml_file                 = data_dir + "/" + str(s3_key)

lg("-------------------------------------------------", 6)
lg("Importing Models and Analysis from S3 into Caching Models from CACHE - S3Loc(" + str(s3_loc) + ") File(" + str(ml_file) + ")", 6)
lg("", 6)
    

if os.path.exists(ml_file) == False:

    s3_loc              = str(s3_bucket) + ":" + str(s3_key)
    lg("Downloading ModelFile S3Loc(" + str(s3_loc) + ")", 6)
    download_results    = core.s3_download_and_store_file(s3_loc, ml_file, core.get_rds(), core.get_dbs(), debug)

    if download_results["Status"] != "SUCCESS":
        lg("ERROR: Stopping processing for errror: " + str(download_results["Error"]), 0)
        sys.exit(1)
    else:
        lg("Done Downloading ModelFile S3Loc(" + str(s3_loc) + ") File(" + str(download_results["Record"]["File"]) + ")", 6)
        ml_file         = download_results["Record"]["File"]
else:
    lg("ERROR: Existing Model File Found(" + str(ml_file) + ") Remove this file and retry. (It costs money to download from S3)... Continuing using the existing file.", 6)
# end of downloading from s3 if it's not locally available

ra_name                 = "CACHE"

lg("Importing(" + str(ml_file) + ") Models and Analysis into Redis(" + str(ra_name) + ")", 6)

cache_req               = {
                            "RAName"    : ra_name,
                            "DSName"    : str(ds_name),
                            "TrackingID": "",
                            "ModelFile" : ml_file,
                            "S3Loc"     : s3_loc
                        }

upload_results          = core.ml_load_model_file_into_cache(cache_req, core.get_rds(), core.get_dbs(), debug)
if upload_results["Status"] == "SUCCESS":
    lg("Done Loading Model File for DSName(" + str(ds_name) + ") S3Loc(" + str(cache_req["S3Loc"]) + ")", 6)
else:
    lg("", 6)
    lg("ERROR: Failed Loading Model File(" + str(cache_req["ModelFile"]) + ") into Cache for DSName(" + str(ds_name) + ")", 6)
    lg(upload_results["Error"], 6)
    lg("", 6)
    sys.exit(2)
# end of if success


lg("", 6)
lg("Importing and Caching Completed", 5)
lg("", 6)

sys.exit(0)
