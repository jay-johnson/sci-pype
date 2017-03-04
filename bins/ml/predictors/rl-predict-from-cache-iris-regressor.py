#!/usr/bin/env python

# Load common imports and system envs to build the core object
import sys, os

# For running inside the docker container use:
#import matplotlib
#matplotlib.use('Agg')

# Load the Environment:
os.environ["ENV_DEPLOYMENT_TYPE"] = "RedisLabs"

from src.common.inits_for_python import *


#####################################################################
#
# Start Arg Processing:
#
action              = "ML Regressor"
parser              = argparse.ArgumentParser(description="Parser for Action: " + str(action))
parser.add_argument('-f', '--csvfile', help='CSV File', dest='csvfile')
parser.add_argument('-n', '--dsname', help='Dataset Name', dest='ds_name')
parser.add_argument('-b', '--s3bucket', help='S3 Bucket (Optional)', dest='s_bucket')
parser.add_argument('-k', '--s3key', help='S3 Key (Optional)', dest='s_key')
parser.add_argument('-u', '--usedate', help='Use Date', dest='usedate')
parser.add_argument("-d", "--debug", help="Debug Flag", dest='debug', action='store_true')
args                = parser.parse_args()

if args.debug:
    debug           = True
    core.enable_debug()

ds_name             = "iris_regressor"
if args.ds_name:
    ds_name         = str(args.ds_name).strip().lstrip()

now                 = datetime.datetime.now()
cur_date            = now
cur_date_str        = now.strftime("%Y-%m-%d")
if args.usedate:
    cur_date_str    = str(args.usedate)

send_email          = "1" # by default send email
s3_bucket           = "demodatasets"
s3_key              = "dataset_" + str(str(ds_name).upper().strip().lstrip()) + "_" + str(cur_date_str) + ".csv"
analysis_version    = 2

if args.s_bucket:
    s3_bucket       = str(args.s_bucket)

if args.s_key:
    s3_key          = str(args.s_key)

dataset_filename    = "iris.csv"
ml_csv              = str(os.getenv("ENV_DATA_SRC_DIR", "/opt/work/data/src")) + "/" + dataset_filename
if args.csvfile:
    ml_csv          = str(args.csvfile)
#
# End Arg Processing
#
#####################################################################


import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

if os.path.exists(ml_csv) == False:
    s3_loc              = str(s3_bucket) + ":" + str(s3_key)
    download_results    = core.s3_download_and_store_file(s3_loc, ml_csv, core.get_rds(), core.get_dbs(), debug)

    if download_results["Status"] != "SUCCESS":
        lg("ERROR: Stopping processing for errror: " + str(download_results["Error"]), 0)
        sys.exit(1)
    else:
        ml_csv          = download_results["Record"]["File"]
# end of downloading from s3 if it's not locally available

lg("Processing ML Predictions for CSV(" + str(ml_csv) + ")", 6)

max_features_to_display = 10
num_estimators          = 200
show_importance_plot    = True
show_confusion_plot     = True
random_state            = 0

# For forecasting:
units_ahead_set         = []
units_ahead             = 0
now                     = datetime.datetime.now()
title_prefix            = ds_name
confusion_plot_title    = ds_name + " - Random Forest Confusion Matrix\nThe darker the square on the diagonal the better the predictions\n\n"
featimp_plot_title      = ds_name + " - Feature Importance with Estimators(" + str(num_estimators) + ")"

row_names               = [ "Actual" ]      # CM - Y Axis
col_names               = [ "Predictions" ] # CM - X Axis
num_jobs                = 8

ranked_features         = []
org_ranked_features     = []
ml_type                 = "Predict with Filter"
ml_algo_name            = "xgb-regressor"
price_min               = 0.10
train_test_ratio        = 0.1


# What column has the labeled targets as integers? (added-manually to the dataset)
target_column_name      = "ResultLabel"                 
# possible values in the Target Column
target_column_values    = [ "Iris-setosa", "Iris-versicolor", "Iris-virginica" ] 

# What columns can the algorithms use for training and learning?
feature_column_names    = [ "SepalLength", "SepalWidth", "PetalLength", "PetalWidth", "ResultTargetValue" ] 

# What column holds string labels for the Target Column?
label_column_name       = "ResultLabel"

ignore_features         = [ # Prune non-int/float columns as needed: 
                            target_column_name,
                            label_column_name
                        ]

algo_nodes              = []
forcast_df              = None
ml_request              = {
                            "MLType"    : ml_type,
                            "MLAlgo"    : {
                                "Name"      : ml_algo_name,
                                "Version"   : 1,
                                "Meta"      : {
                                    "UnitsAhead"    : units_ahead,
                                    "DatasetName"   : ds_name,
                                    "FilterMask"    : None,
                                    "Source"        : {
                                        "CSVFile"       : ml_csv,
                                        "S3File"        : "",        # <Bucket Name>:<Key>
                                        "RedisKey"      : ""         # <App Name>:<Key>
                                    },
                                },
                                "Steps"     : {
                                    "Train"     :{
                                        "LearningRate"          : 0.1,
                                        "NumEstimators"         : 1000,
                                        "Objective"             : "reg:linear",
                                        "MaxDepth"              : 6,
                                        "MaxDeltaStep"          : 0,
                                        "MinChildWeight"        : 1,
                                        "Gamma"                 : 0,
                                        "SubSample"             : 0.8,
                                        "ColSampleByTree"       : 0.8,
                                        "ColSampleByLevel"      : 1.0,
                                        "RegAlpha"              : 0,
                                        "RegLambda"             : 1,
                                        "BaseScore"             : 0.5,
                                        "NumThreads"            : -1, # infinite = -1
                                        "ScaledPositionWeight"  : 1,
                                        "Seed"                  : 27,
                                        "Debug"                 : True
                                    }
                                },
                                "Cache" : {
                                    "RLoc"      : "CACHE:_MODELS_" + str(ds_name) + "_LATEST",
                                    "UseCaches" : True
                                }
                            },
                            "FeatureColumnNames": feature_column_names,
                            "TargetColumnName"  : target_column_name,
                            "TargetColumnValues": target_column_values,
                            "IgnoreFeatures"    : ignore_features,
                            "UnitsAheadSet"     : units_ahead_set,
                            "UnitsAheadType"    : "",
                            "PredictionType"    : "Predict",
                            "MaxFeatures"       : 10,
                            "Version"           : 1,
                            "TrackingType"      : "UseTargetColAndUnits",
                            "TrackingName"      : core.to_upper(ds_name),
                            "TrackingID"        : "ML_" + ds_name + "_" + str(core.build_unique_key()), 
                            "Debug"             : False
                        }

# Load dataset to build
csv_res                 = core.ml_load_csv_dataset(ml_request, core.get_rds(), core.get_dbs(), debug)
if csv_res["Status"] != "SUCCESS":
    lg("ERROR: Failed to Load CSV(" + str(ml_request["MLAlgo"]["Meta"]["Source"]["CSVFile"]) + ")", 0)
    sys.exit(1)

ds_df                   = csv_res["Record"]["SourceDF"]

# Build a Filter for pruning bad records out before creating the train/test sets
samples_filter_mask     =     (ds_df["SepalLength"] > 0.0) \
                            & (ds_df["PetalWidth"]  > 0.0)

# For patching on the fly you can use the encoder method to replace labels with target dictionary values:
#ready_df                = core.ml_encode_target_column(ds_df, "ResultLabel", "Target")

show_pair_plot          = False
if show_pair_plot:
    lg("Samples(" + str(len(ds_df.index)) + ") in CSV(" + str(ml_request["MLAlgo"]["Meta"]["Source"]["CSVFile"]) + ")", 6)
    lg("")
    print ds_df.describe()
    lg("")
    num_per_class       = ds_df.groupby("ResultLabel").size()
    print num_per_class
    lg("")

    pair_plot_req       = {
                            "Title"         : "Iris Dataset PairPlot",
                            "SourceDF"      : ds_df[samples_filter_mask],
                            "Style"         : "default",
                            "DiagKind"      : "hist", # "kde" or "hist"
                            "HueColumnName" : ml_request["TargetColumnName"],
                            "XLabel"        : "",
                            "YLabel"        : "",
                            "CompareColumns": ml_request["FeatureColumnNames"],
                            "Size"          : 3.0,
                            "ImgFile"       : str(os.getenv("ENV_DATA_SRC_DIR", "/opt/work/data/src")) + "/" + "validate_jupyter_iris_classification_pairplot.png",
                            "ShowPlot"      : True
                        }
    core.sb_pair_plot(pair_plot_req)
    if os.path.exists(pair_plot_req["ImgFile"]):
        lg("Done Plotting Valiation Pair Plot - Saved(" + str(pair_plot_req["ImgFile"]) + ")", 5)
    else:
        lg("Failed to save Validation Pair Plot(" + str(pair_plot_req["ImgFile"]) + "). Please check the ENV_DATA_SRC_DIR is writeable by this user and exposed to the docker container correctly.", 0)
# end of showing a pairplot for validation

# Create a Prediction Column
ml_request["MLAlgo"]["Meta"]["SamplesFilterMask"]  = samples_filter_mask

# Create a Result Column

core.enable_debug()
ml_images               = []
train_results           = core.ml_train_models_for_predictions(ml_request, core.get_rds(), core.get_dbs(), debug)
if train_results["Status"] != "SUCCESS":
    lg("ERROR: Failed to Train Models for Predictions with Error(" + str(train_results["Error"]) + ") StoppedEarly(" + str(train_results["Record"]["StoppedEarly"]) + ")", 0)
    sys.exit(1)

algo_nodes              = train_results["Record"]["AlgoNodes"]
predict_row             = {
                            "SepalLength"       : 5.4,
                            "SepalWidth"        : 3.4,
                            "PetalLength"       : 1.7, 
                            "PetalWidth"        : 0.2,
                            "ResultTargetValue" : 0
                        }
predict_row_df          = pd.DataFrame(predict_row, index=[0])
predict_req             = {
                            "AlgoNodes"     : algo_nodes,
                            "PredictionMask": samples_filter_mask,
                            "PredictionRow" : predict_row_df
                        }
predict_results         = core.ml_compile_predictions_from_models(predict_req, core.get_rds(), core.get_dbs(), debug)
if predict_results["Status"] != "SUCCESS":
    lg("ERROR: Failed to Compile Predictions from Models with Error(" + str(predict_results["Error"]) + ")", 0)
    sys.exit(1)

lg("Done with Predictions", 6)

if predict_results["Status"] == "SUCCESS":

    al_req                      = train_results["Record"]

    al_req["DSName"]            = ml_request["TrackingName"]
    al_req["Version"]           = 1
    al_req["FeatureColumnNames"]= ml_request["FeatureColumnNames"]
    al_req["TargetColumnName"]  = ml_request["TargetColumnName"]
    al_req["TargetColumnValues"]= ml_request["TargetColumnValues"]
    al_req["IgnoreFeatures"]    = ml_request["IgnoreFeatures"]
    al_req["PredictionType"]    = ml_request["PredictionType"]
    al_req["ConfMatrices"]      = predict_results["Record"]["ConfMatrices"]
    al_req["PredictionMarkers"] = predict_results["Record"]["PredictionMarkers"]

    analysis_dataset    = core.ml_compile_analysis_dataset(al_req, core.get_rds(), core.get_dbs(), debug)

    lg("Analyzed Models(" + str(len(analysis_dataset["Models"])) + ")", 6)
    
    lg("-----------------------------------------------------", 6)

    lg("Caching Models", 6)

    cache_req           = {
                            "Name"      : "CACHE",
                            "Key"       : "_MODELS_" + str(al_req["Tracking"]["TrackingName"]) + "_LATEST",
                            "TrackingID": "_MD_" + str(al_req["Tracking"]["TrackingName"]),
                            "Analysis"  : analysis_dataset
                        }

    cache_results       = core.ml_cache_analysis_and_models(cache_req, core.get_rds(), core.get_dbs(), debug)
    
    lg("Done Caching Models", 6)

    lg("-----------------------------------------------------", 6)

    lg("Creating Analysis Visualizations", 6)

    # Turn this on to show the images:
    analysis_dataset["ShowPlot"]    = True
    analysis_dataset["SourceDF"]    = al_req["SourceDF"]
    
    lg("Plotting Feature Importance", 6)
    
    for midx,model_node in enumerate(analysis_dataset["Models"]):
        predict_col     = model_node["Target"]
        if predict_col == "ResultTargetValue": 
            plot_req    = {
                            "ImgFile"   : analysis_dataset["FeatImpImgFile"],
                            "Model"     : model_node["Model"],
                            "XLabel"    : str(predict_col),
                            "YLabel"    : "Importance Amount",
                            "Title"     : str(predict_col) + " Importance Analysis",
                            "ShowPlot"  : analysis_dataset["ShowPlot"]
                        }
            image_list  = core.sb_model_feature_importance(plot_req, debug)
            for img in image_list:
                ml_images.append(img)
    # end of for all models
    
    lg("Plotting PairPlots", 6)

    plot_req        = {
                        "DSName"        : str(analysis_dataset["DSName"]),
                        "Title"         : str(analysis_dataset["DSName"]) + " - Pair Plot",
                        "ImgFile"       : str(analysis_dataset["PairPlotImgFile"]),
                        "SourceDF"      : al_req["SourceDF"],
                        "HueColumnName" : target_column_name,
                        "CompareColumns": feature_column_names,
                        "Markers"       : ["o", "s", "D"],
                        "Width"         : 15.0,
                        "Height"        : 15.0,
                        "ShowPlot"      : analysis_dataset["ShowPlot"]
                    }

    image_list      = core.sb_pairplot(plot_req, debug)
    for img in image_list:
        ml_images.append(img)
    
    lg("Plotting Confusion Matrices", 6)

    plot_req        = {
                        "DSName"        : str(analysis_dataset["DSName"]),
                        "Title"         : str(analysis_dataset["DSName"]) + " - Confusion Matrix",
                        "ImgFile"       : str(analysis_dataset["CMatrixImgFile"]),
                        "SourceDF"      : al_req["SourceDF"],
                        "ConfMatrices"  : al_req["ConfMatrices"],
                        "Width"         : 15.0,
                        "Height"        : 15.0,
                        "XLabel"        : "Dates",
                        "YLabel"        : "Values",
                        "ShowPlot"      : analysis_dataset["ShowPlot"]
                    }

    image_list      = core.sb_confusion_matrix(plot_req, debug)

    for img in image_list:
        ml_images.append(img)

    lg("Plotting Scatters", 6)

    plot_req        = {
                        "DSName"            : str(analysis_dataset["DSName"]),
                        "Title"             : str(analysis_dataset["DSName"]) + " - Scatter Plot",
                        "ImgFile"           : str(analysis_dataset["ScatterImgFile"]),
                        "SourceDF"          : analysis_dataset["SourceDF"],
                        "UnitsAheadType"    : analysis_dataset["UnitsAheadType"],
                        "FeatureColumnNames": analysis_dataset["FeatureColumnNames"],
                        "Hue"               : label_column_name,
                        "Width"             : 7.0,
                        "Height"            : 7.0,
                        "XLabel"            : "Dates",
                        "YLabel"            : "Values",
                        "ShowPlot"          : analysis_dataset["ShowPlot"]
                    }

    image_list      = core.sb_all_scatterplots(plot_req, debug)
    for img in image_list:
        ml_images.append(img)
    
    lg("Plotting JointPlots", 6)

    plot_req        = {
                        "DSName"            : str(analysis_dataset["DSName"]),
                        "Title"             : str(analysis_dataset["DSName"]) + " - Joint Plot",
                        "ImgFile"           : str(analysis_dataset["JointPlotImgFile"]),
                        "SourceDF"          : analysis_dataset["SourceDF"],
                        "UnitsAheadType"    : analysis_dataset["UnitsAheadType"],
                        "FeatureColumnNames": analysis_dataset["FeatureColumnNames"],
                        "Hue"               : label_column_name,
                        "Width"             : 15.0,
                        "Height"            : 15.0,
                        "XLabel"            : "Dates",
                        "YLabel"            : "Values",
                        "ShowPlot"          : analysis_dataset["ShowPlot"]
                    }

    image_list      = core.sb_all_jointplots(plot_req, debug)
    for img in image_list:
        ml_images.append(img)

    lg("Done Creating Analysis Visualizations", 6)

    lg("-----------------------------------------------------", 6)

else:
    lg("", 6)
    lg("ERROR: Failed Processing Predictions for Dataset(" + str(ds_name) + ") with Error:", 6)
    lg(ml_results["Error"], 6)
    lg("", 6)
    sys.exit(2)
# end of if success

lg("", 6)
lg("Analysis Complete Saved Images(" + str(len(ml_images)) + ")", 5)
lg("", 6)

sys.exit(0)
