#!/usr/bin/python

import os, inspect, sys, json, argparse, uuid, csv, glob
        
# Endpoint Database Schema Files:
import imp, datetime 
from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, MetaData, Date, DateTime, Float, Boolean
from sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker, relation
from sqlalchemy.ext.declarative import declarative_base

sys.path.append("/opt/src")

from databases.schema.db_schema_stocks  import *
from common                             import *


#####################################################################
#
# Start Arg Processing:
#
action          = "Building DB Initial Records"
parser          = argparse.ArgumentParser(description="Parser for Action: " + str(action))
parser.add_argument('-e', help='Environment <Local|Debug|Test|Live>', required=True, dest='env')
parser.add_argument('-d', '--debug', help='Debug Flag')
args            = parser.parse_args()

db_config       = "/opt/configs/db.json"
env_name        = "Local"
debug           = False

if args.env:
    env_name = str(args.env)

    if env_name == "Local":
        db_config       = "/opt/configs/db.json"

if args.debug:
    debug = True
#
# End Arg Processing
#
#####################################################################


def handle_build_initial_records(db, path_to_csv_files, env_name):

    results             = {}
    results["Status"]   = "FAILED"
    results["Error"]    = ""
    results["Record"]   = {}

    lg("Adding Stock Records", 5)

    try:
        import os, inspect
        src_dir         = str(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))

        Base            = declarative_base()
        schema_to_use   = str(db["Schema"])
        schema_file_imp = str(str(schema_to_use).replace(".py", "").split("/")[-1])
        database_name   = str(db["Database Name"])
        db_user         = str(db["User"])
        db_password     = str(db["Password"])
        db_host_list    = str(db["Address List"])
        db_host         = db_host_list.split(" ")[0]
        sql_conn_str    = "mysql://" + str(db_user) + ":" + str(db_password) + "@" + str(db_host) + "/" + str(database_name)

        lg("Building Engine", 6)
        engine          = create_engine(sql_conn_str,
                                        echo=False)


        lg("Connecting Engine with SQLAddr(" + str(sql_conn_str) + ")", 5)
        connection      = engine.connect()
        session         = scoped_session(sessionmaker(autocommit=False,
                                                        autoflush=False,
                                                        bind=engine))

        error_msg       = "Walking through Schema File(" + str(schema_file_imp) + ")"
        Base            = declarative_base()
        new_module      = __import__(str(schema_file_imp))
        the_job_module  = None
        classes_to_add  = []
        lg("Loading all Schema Modules", 6)
        for name, job_module_obj in inspect.getmembers(new_module):
            if inspect.isclass(job_module_obj) and (str(job_module_obj.__class__.__name__) == "DeclarativeMeta") and name != "Base":
                last_class_name = str(job_module_obj.__class__.__name__)
                classes_to_add.append(last_class_name)
                lg("Adding Class DB Name(" + str(name) + ") if not created", 6)
                job_module_obj.__table__.create(engine, checkfirst=True)
        # End of building tables

        files_to_process= glob.glob(str(path_to_csv_files) + "*.csv")
        errors          = []
        total_records   = len(files_to_process)
        percent_done    = 0.0
        progress_done   = 0.0
        cur_record      = 0

        date_idx        = 0
        open_idx        = 1
        high_idx        = 2
        low_idx         = 3
        close_idx       = 4
        volume_idx      = 5

        lg("Total Stock CSV Files to Import(" + str(len(files_to_process)) + ")", 6)

        for idx, target_file in enumerate(files_to_process):
            if debug:
                lg("Processing CSV File(" + str(target_file) + ")", 6)

            csv_file_handle   = open(target_file, "r")
            ticker_name       = target_file.split("/")[-1].replace(".csv", "").strip().lstrip().upper()
            try:
                reader        = csv.reader(csv_file_handle)
                cur_row       = 0
                for row in reader:

                    if debug:
                        lg("Ticker(" + str(ticker_name) + ") Row(" + str(cur_row) + ") Data(" + str(row) + ")", 6)

                    # skip the header row
                    if cur_row > 0:
                        date_value      = None
                        open_value      = None
                        high_value      = None
                        low_value       = None
                        close_value     = None
                        volume_value    = None

                        if str(row[date_idx]) != "" and str(row[date_idx]).lower() != "none":
                          split_date_arr  = str(row[date_idx]).split("-")
                          day             = str(split_date_arr[0])
                          if len(day) < 2:
                            day           = "0" + str(split_date_arr[0])

                          formatted_date  = day + "-" + str(split_date_arr[1]) + "-20" + str(split_date_arr[2]) 
                          date_value      = datetime.datetime.strptime(formatted_date, "%d-%b-%Y")
                        # end of scrubbing the date value for a clean strptime

                        if str(row[open_idx])   != "" and str(row[open_idx]).lower() != "none":
                          open_value      = float(row[open_idx])

                        if str(row[high_idx])   != "" and str(row[high_idx]).lower() != "none":
                          high_value      = float(row[high_idx])

                        if str(row[low_idx])    != "" and str(row[low_idx]).lower() != "none":
                          low_value       = float(row[low_idx])

                        if str(row[close_idx])  != "" and str(row[close_idx]).lower() != "none":
                          close_value     = float(row[close_idx])

                        if str(row[volume_idx]) != "" and str(row[volume_idx]).lower() != "none":
                          volume_value    = int(row[volume_idx])


                        new_stock_point = BT_Stocks(
                                          Symbol                      = ticker_name,
                                          Date                        = date_value,
                                          Open                        = open_value,
                                          High                        = high_value,
                                          Low                         = low_value,
                                          Close                       = close_value,
                                          Volume                      = volume_value,
                                          creation_date               = datetime.datetime.now(),
                                          last_update                 = None
                                        )
                        session.add(new_stock_point)
                    # end of the adds

                    cur_row   += 1
                # end of all rows in the csv
                
                lg("Ticker(" + str(ticker_name) + ") - Adding Stock Points DB Records(" + str(cur_row) + ")", 6)     
                session.commit()
                lg("Ticker(" + str(ticker_name) + ") - Done Adding Stock Points DB Records(" + str(cur_row) + ")", 6)     
            except Exception,k:
                lg("Failed to read CSV(" + str(target_file) + ") with Ex(" + str(k) + ")", 0)

            finally:     
                if debug:
                    lg("Closing", 6)
                csv_file_handle.close()
        # end of building the initial db records
        
        results["Status"]        = "SUCCESS"
        results["Error"]         = ""

    except Exception,f:
        err_msg                         = "Unable to Build Initial Stock Records Ex(" + str(f) + ")"
        lg("ERROR: " + str(err_msg), 0)
        results["Status"]        = "FAILED"
        results["Error"]         = err_msg
        results["Record"]        = {}
    # end of try/ex

    lg("Done Building Stock DB", 5)

    return results
# end of handle_build_initial_records


#####################################################################################

all_db_json     = json.loads(open(db_config).read())

db_json         = {}

for db in all_db_json["Database Applications"]:
    if db["Name"] == "STOCKS":
        db_json = db
# end of finding db json

lg("", 6)
lg("Performing Action(" + str(action) + ")", 4)
lg("DB(" + str(json.dumps(db_json)) + ")", 6)
lg("", 6)

sys.exit(0)

