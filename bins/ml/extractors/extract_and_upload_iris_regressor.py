#!/usr/bin/env python

# Load common imports and system envs to build the core object
import sys, os
from src.common.inits_for_python import *


#####################################################################
#
# Start Arg Processing:
#
action              = "Extract and Upload IRIS Models to S3"
parser              = argparse.ArgumentParser(description="Parser for Action: " + str(action))
parser.add_argument('-u', '--url', help='URL to Download', dest='url')
parser.add_argument('-b', '--s3bucket', help='S3 Bucket (Optional)', dest='s_bucket')
parser.add_argument('-k', '--s3key', help='S3 Key (Optional)', dest='s_key')
parser.add_argument("-d", "--debug", help="Debug Flag", dest='debug', action='store_true')
args                = parser.parse_args()

if args.debug:
    debug           = True
    core.enable_debug()

data_dir            = str(os.getenv("ENV_DATA_DST_DIR", "/opt/work/data/dst"))
if not os.path.exists(data_dir):
    os.mkdir(data_dir, 0777)

ds_name             = "iris_regressor"
cur_date_str        = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
s3_bucket           = "unique-bucket-name-for-datasets"
s3_key              = "dataset_" + core.to_upper(ds_name) + ".cache.pickle.zlib"
s3_loc              = ""

if args.s_bucket:
    s3_bucket       = str(args.s_bucket)

if args.s_key:
    s3_key          = str(args.s_key)
#
# End Arg Processing
#
#####################################################################

s3_loc              = str(s3_bucket) + ":" + str(s3_key)

lg("-------------------------------------------------", 6)
lg("Extracting and Uploading Models from CACHE to S3Loc(" + str(s3_loc) + ")", 6)
lg("", 6)

cache_req           = {
                        "RAName"        : "CACHE",      # Redis instance name holding the models
                        "DSName"        : str(ds_name), # Dataset name for pulling out of the cache
                        "S3Loc"         : str(s3_loc),  # S3 location to store the model file
                        "DeleteAfter"   : False,        # Optional delete after upload
                        "SaveDir"       : data_dir,     # Optional dir to save the model file - default is ENV_DATA_DST_DIR
                        "TrackingID"    : ""            # Future support for using the tracking id
                    }

upload_results      = core.ml_upload_cached_dataset_to_s3(cache_req, core.get_rds(), core.get_dbs(), debug)
if upload_results["Status"] == "SUCCESS":
    lg("Done Uploading Model and Analysis DSName(" + str(ds_name) + ") S3Loc(" + str(cache_req["S3Loc"]) + ")", 6)
else:
    lg("", 6)
    lg("ERROR: Failed Upload Model and Analysis Caches as file for DSName(" + str(ds_name) + ")", 6)
    lg(upload_results["Error"], 6)
    lg("", 6)
    sys.exit(1)
# end of if extract + upload worked

lg("", 6)
lg("Extract and Upload Completed", 5)
lg("", 6)

sys.exit(0)
