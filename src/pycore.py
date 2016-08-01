import os, inspect, datetime, uuid, json, glob, random, logging, sys
from   sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, MetaData, Date, DateTime, Float, Boolean, and_, or_, asc, desc
from   sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker, relation
from   sqlalchemy.ext.declarative import declarative_base

sys.path.insert(0, os.getenv("ENV_PYTHON_SRC_DIR", "/opt/work/src"))

from   common.shellprinting import *
from   logger.logger        import Logger

class PyCore:

    def __init__(self, core_manifest="/opt/work/configs/jupyter.json"):
        
        # the json config for this core:
        self.m_core_file            = core_manifest
        self.m_db_json              = {}
        self.m_debug                = False

        # needs to be in the /opt/work/configs/jupyter.json => Core.Envs JSON Dict
        self.m_env                  = str(os.getenv("ENV_DEPLOYMENT_TYPE", "Local")) 

        self.m_log                  = None # Eventually this will have syslog with: Logger(self.m_name, "/dev/log", logging.DEBUG)

        self.m_core_json            = {}
        self.m_dbs                  = {} # dictionary where the keys are logical names for the underlying db session (applications)
        self.m_db_apps_json         = {}
        self.m_db_app_system        = None
        self.m_rds                  = {} # dictionary where the keys are logical names for the underlying redis connections (applications)
        self.m_rd_apps_json         = {}
        self.m_rd_app_system        = None
    
        self.m_slack_node_name      = "jupyter"
        self.m_slack_node           = {
                                        "BotName"     : str(os.getenv("ENV_SLACK_BOTNAME", "bugbot")),
                                        "ChannelName" : str(os.getenv("ENV_SLACK_CHANNEL", "debugging")),
                                        "NotifyUser"  : str(os.getenv("ENV_SLACK_NOTIFY_USER", "channel")),
                                        "Token"       : str(os.getenv("ENV_SLACK_TOKEN", "xoxb-51351043345-Lzwmto5IMVb8UK36MghZYMEi")),
                                        "EnvName"     : str(os.getenv("ENV_SLACK_ENVNAME", "dev-jupyter"))
                                    }
        self.m_slack_bot            = str(self.m_slack_node["BotName"])
        self.m_slack_enabled        = os.getenv("ENV_SLACK_ENABLED", "1") == "1"

        # load the core
        self.load_core_json()

        # Assign the name out of the json config
        self.m_name                 = str(self.m_core_json["Core"]["Name"])

        self.load_core_db_apps()
        
        self.load_core_redis_apps()

    # end of __init__

     
    def lg(self, msg, level=6):

        # log it to syslog
        if self.m_log:
            # concat them
            full_msg = self.m_name + ": " + msg

            self.m_log.log(full_msg, level)

        else:
            lg(msg, level)

        return None
    # end of lg

    
    #####################################################################################################
    #
    # Initialize Resources
    #
    #####################################################################################################


    def init_core_resources(self):
        self.load_core_json()
        self.load_core_db_apps()
        self.load_core_redis_apps()
    # end of init_core_resources


    def load_core_json(self):

        if len(self.m_core_json) == 0:
            self.m_core_json     = json.loads(open(self.m_core_file).read())
            self.m_db_apps_json     = json.loads(open(self.m_core_json["Core"]["Envs"][self.m_env]["Database"]).read())
            self.m_rd_apps_json     = json.loads(open(self.m_core_json["Core"]["Envs"][self.m_env]["Redis"]).read())

    # end of load_core_json


    def load_core_db_apps(self):

        self.load_core_json()

        if self.m_debug:
            self.lg("Looking up DB Connectivity File", 6)
        # end of if debug

        # Load them if there are apps
        if len(self.m_db_apps_json["Database Applications"]) > 0:

            # Add the source base path
            self.load_src_path("ENV_PYTHON_SRC_DIR", "/opt/work/src")
            from connectors.database.database_application_system import DatabaseApplicationSystem

            self.m_db_app_system    = DatabaseApplicationSystem(None, False)
            self.m_dbs              = self.m_db_app_system.return_connectors(self.m_db_apps_json["Database Applications"])
            self.m_db_app_system.connect_all()

        # end of if there are Database apps to load

    # end of load_core_db_apps

   
    def load_core_redis_apps(self):
        
        self.load_core_json()

        if self.m_debug:
            self.lg("Looking up RA Connectivity File", 6)
        # end of if debug

        # Load them if there are apps
        if len(self.m_rd_apps_json["Redis Applications"]) > 0:

            # Add the source base path
            self.load_src_path("ENV_PYTHON_SRC_DIR", "/opt/work/src")
            from connectors.redis.redis_application_system import RedisApplicationSystem

            self.m_ra_app_system    = RedisApplicationSystem(self.m_log, False)
            self.m_rds              = self.m_ra_app_system.return_connectors(self.m_rd_apps_json["Redis Applications"])
            self.m_ra_app_system.connect_all()
        # end of if there are Redis apps to load

    # end of load_core_redis_apps



    def load_src_path(self, env_key, default_path):

        import sys
        add_path    = os.getenv(env_key, default_path)
        found_path  = False
        for path in sys.path:
            if path == add_path:
                found_path = True
                break
        # end of iterating through path

        if not found_path:
            sys.path.insert(0, add_path)
        # end of need to add path

    # end of load_src_path


    #####################################################################################################
    #
    # General Util Methods
    #
    #####################################################################################################


    def convert_utc_date_to_str(self, cur_date, optional_format="%m/%d/%Y %H:%M:%S"):
        return_str  = ""
        if cur_date != None:
            convert_date    = cur_date - datetime.timedelta(hours=4)
            return_str      = str(convert_date.strftime('%m/%d/%Y %H:%M:%S'))
        return return_str
    # end of convert_utc_date_to_str


    def convert_date_string_to_date(self, date_str, optional_format="%Y-%m-%dT%H:%M:%S.%fZ"):

        date_to_return          = None
        try:
            import datetime
            date_to_return      = datetime.datetime.strptime(str(date_str), optional_format)
        except Exception,f:
            self.lg("ERROR: Failed Converting Date(" + str(date_str) + ") with Format(" + str(optional_format) + ")", 0)
        # end of tries to read this string as a valid date...

        return date_to_return
    # end of convert_date_string_to_date


    def core_build_unique_key(self, length=-1):
        return str(str(uuid.uuid4()).replace("-", "")[0:length])
    # end of core_build_unique_key


    def ppj(self, json_data):
        return str(json.dumps(json_data, sort_keys=True, indent=4, separators=(',', ': ')))
    # end of ppj


    def convert_utc_date_string_to_est_datetime(self, utc_date_str, optional_format="%Y-%m-%dT%H:%M:%S.%fZ"):
        utc_time                = datetime.datetime.strptime(utc_date_str, optional_format)
        utc_adjusted            = utc_time.replace(tzinfo=self.m_utc_tz_zone)
        offset_est_local_time   = utc_adjusted.astimezone(self.m_est_tz_zone)
        est_local_time          = datetime.datetime(
                                        year    = offset_est_local_time.year,
                                        month   = offset_est_local_time.month,
                                        day     = offset_est_local_time.day,
                                        hour    = offset_est_local_time.hour,
                                        minute  = offset_est_local_time.minute,
                                        second  = offset_est_local_time.second)

        return est_local_time
    # end of convert_utc_date_string_to_est_datetime


    def create_random_float(self, original, min_value, max_value):
        new_random_float= float(original) + float(random.uniform(min_value, max_value))
        return new_random_float
    # end of create_random_float


    def create_random_int(self, original, min_value, max_value):
        new_random_int  = random.uniform(min_value, max_value)
        return original + int(int(original) * float(new_random_int))
    # end of create_random_int


    def get_percent_done(self, progress, total):
        return "%0.2f" % float(float(progress)/float(total)*100.00)
    # end of get_percent_done

      
    def write_json_to_file(self, output_file, record_json):

        try:
            temp_output     = "/tmp/tmpfile_" + datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S") + "_"
            temp_file       = self.log_msg_to_unique_file(self.pretty_print_json(record_json), temp_output)
            os.system("mv " + str(temp_file) + " " + str(output_file))

            if os.path.exists(output_file):
                return output_file
            else:
                return "FAILED_TO_CREATE_FILE"

        except Exception,k:
            print "ERROR: Failed to write file with pretty print json with Ex(" + str(k) + ")"
            return "FILE_DOES_NOT_EXIST"
        # end of try/ex

        return output_file 
    # end of write_json_to_file


    def core_build_def_hash(self, start_status="FAILED", start_error="", record={}):
        return  { "Status" : str(start_status), "Error" : str(start_error), "Record" : record }
    # end of core_build_def_hash
    
    
    def handle_core_display_error(self, err_msg, def_rec={}, debug=False):

        results                 = {}
        results["Status"]       = "Display Error"
        results["Error"]        = str(err_msg)
        results["Record"]       = def_rec

        return results
    # end of handle_core_display_error


    def handle_core_general_error(self, status, err_msg, def_rec={}, debug=False):

        results                 = {}
        results["Status"]       = str(status)
        results["Error"]        = str(err_msg)
        results["Record"]       = def_rec

        if debug:
            self.lg("ERROR: " + str(err_msg), 0)

        return results
    # end of handle_core_general_error

    
    def handle_core_exception(self, status, err_msg, ex, debug=False):
        
        results                 = self.core_build_def_hash(status, err_msg, {
                                                "Exception" : "Failed to Process"
                                            })

        try:

            if self.m_slack_enabled:
                self.handle_send_slack_internal_ex(ex, debug)
                results             = self.core_build_def_hash("SUCCESS", "", {
                                                    "Exception" : ""
                                            })
            else:
                import traceback, sys
                exc_type, exc_obj, exc_tb = sys.exc_info()
                ex_error            = self.get_exception_error_message(ex, exc_type, exc_obj, exc_tb, False, debug)
                results             = self.core_build_def_hash("SUCCESS", "", {
                                                    "Exception" : str(ex_error)
                                            })
            # end of branching if slack supported or not

        except Exception, e:
            err_msg             = "Failed to post message to slack with Ex(" + str(e) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results             = self.core_build_def_hash("Display Error", str(err_msg), {
                                                "Exception" : "Failed Processing with Exception"
                                            })
            results["Status"]   = "FAILED"
        # end of try/ex

        return results
    # end of handle_core_exception

    
    def get_exception_error_message(self, ex, exc_type, exc_obj, exc_tb, slack_formatted=False, debug=False):

        error_log_msg           = "FAILED to process exception"
        try:
            path_to_file        = str(exc_tb.tb_frame.f_code.co_filename)
            last_line           = int(exc_tb.tb_lineno)
            gh_line_number      = int(last_line) - 1

            file_name           = str(os.path.split(exc_tb.tb_frame.f_code.co_filename)[1])
            path_to_file        = str(exc_tb.tb_frame.f_code.co_filename)
            
            ex_details_msg      = str(ex)

            if ex_details_msg != "":
                error_log_msg = "Error on Line: \x1b[31m" + str(last_line) + "\x1b[0m Code: \n\t\x1b[31m" + str(ex_details_msg) + "\x1b[0m\n"
                if slack_formatted:
                    self.lg("" + str(error_log_msg), 0)
                    error_log_msg = " Error on Line: *" + str(last_line) + "* Code: \n```" + str(ex_details_msg) + "``` \n"
            else:
                error_log_msg   = "Error on Line Number: " + str(last_line)

        except Exception,k:
            error_log_msg       = "Failed to process exception with(" + str(k) + ")"
            self.lg("ERROR: " + str(error_log_msg), 0)
        # end of trying to process the exception

        return error_log_msg
    # end of get_exception_error_message


    #####################################################################################################
    #
    # Redis Application Methods
    #
    #####################################################################################################


    def get_message_no_block(self, redis_app, input_key):

        results                         = {}
        results["Status"]               = "FAILED"
        results["Error"]                = ""
        results["Record"]               = None

        try:
            results["Record"]           = redis_app.get_message(False, input_key)
            results["Status"]           = "SUCCESS"
            results["Error"]            = ""

        except ValueError, e:
            err_msg                     = "RA - ValueError to Address(" + redis_app.get_address() + ") ValueEx(" + str(e) +")"
            self.lg("ERROR: " + str(err_msg), 0)
            results["Record"]           = None
            results["Status"]           = "FAILED"
            results["Error"]            = str(err_msg)

        except Exception, e:
            test_for_redis_connectivity = str(e)
            if "Connection refused." in test_for_redis_connectivity:
                err_msg                 = "RA - Connection REFUSED to Address(" + redis_app.get_address() + ") Key(" + input_key + ") ConEx(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Record"]       = None
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)

            else:
                err_msg                 = "RA - EX Address(" + redis_app.get_address() + ") Key(" + input_key + ") General Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Record"]       = None
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
        # end of try/ex

        return results
    # end of get_message_no_block


    def get_message_with_block(self, redis_app, input_key):

        results                         = {}
        results["Status"]               = "FAILED"
        results["Error"]                = ""
        results["Record"]               = None

        try:
            results["Record"]           = redis_app.get_message(True, input_key)
            results["Status"]           = "SUCCESS"
            results["Error"]            = ""

        except ValueError, e:
            err_msg                     = "RA - ValueError to Address(" + redis_app.get_address() + ") ValueEx(" + str(e) +")"
            self.lg("ERROR: " + str(err_msg), 0)
            results["Record"]           = None
            results["Status"]           = "FAILED"
            results["Error"]            = str(err_msg)

        except Exception, e:
            test_for_redis_connectivity = str(e)
            if "Connection refused." in test_for_redis_connectivity:
                err_msg                 = "RA - Connection REFUSED to Address(" + redis_app.get_address() + ") Key(" + input_key + ") ConEx(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Record"]       = None
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)

            else:
                err_msg                 = "RA - EX Address(" + redis_app.get_address() + ") Key(" + input_key + ") General Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Record"]       = None
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
        # end of try/ex

        return results
    # end of get_message_with_block


    def publish_message_to_key(self, message, dest_key, redis_app, debug=False):

        results                         = {}
        results["Status"]               = "FAILED"
        results["Error"]                = ""
        results["Record"]               = {}

        try:
            if debug:
                self.lg("Publish(" + str(dest_key) + ") RA(" + str(redis_app.get_address()) + ")", 6)
            
            if redis_app.m_rw == None:
                redis_app.connect()

            redis_app.put_into_key(dest_key, message)
            results["Record"]           = {
                                            "Address"   : str(redis_app.get_address()),
                                            "Key"       : dest_key
                                        }
            results["Status"]           = "SUCCESS"
            results["Error"]            = ""
            if debug:
                self.lg("Publish Done", 6)

        except ValueError, e:
            err_msg                     = "Connection to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Non-Pickle Formatted Message Ex(" + str(e) +")"
            self.lg("ERROR: " + str(err_msg), 0)
            results["Status"]           = "FAILED"
            results["Error"]            = str(err_msg)
            results["Record"]           = {}
        except Exception, e:
            test_for_redis_connectivity = str(e)
            if "Connection refused." in test_for_redis_connectivity:
                err_msg                 = "Connection REFUSED to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
                results["Record"]       = {}

            else:
                err_msg                 = "Publish Failed to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
                results["Record"]       = {}
        # end of try/ex

        if debug:
            self.lg("Base Done Publish Result Key", 6)

        return results
    # end of publish_message_to_key


    def add_records_to_cache_in_redis(self, json_record, dest_key, redis_app, debug=False):

        results                         = {}
        results["Status"]               = "FAILED"
        results["Error"]                = ""
        results["Record"]               = {}

        try:
            if debug:
                self.lg("Add Records to Cache(" + str(dest_key) + ") RA(" + str(redis_app.get_address()) + ")", 6)

            if redis_app.m_rw == None:
                redis_app.connect()

            redis_app.put_into_key(dest_key, json_record)

            results["Record"]           = {
                                            "Address"   : str(redis_app.get_address()),
                                            "Key"       : dest_key
                                        }
            results["Status"]           = "SUCCESS"
            results["Error"]            = ""
            if debug:
                self.lg("Add Records to Cache Done", 6)

        except ValueError, e:
            err_msg                     = "Connection to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Non-Pickle Formatted Message Ex(" + str(e) +")"
            self.lg("ERROR: " + str(err_msg), 0)
            results["Status"]           = "FAILED"
            results["Error"]            = str(err_msg)
            results["Record"]           = {}
        except Exception, k:

            test_for_redis_connectivity = str(k)

            if "Connection refused." in test_for_redis_connectivity:
                err_msg                 = "Add Records - Connection REFUSED to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(k) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
                results["Record"]       = {}

            else:
                err_msg                 = "Add Records - Cache Failed to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(k) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                cache_results           = self.handle_core_exception("FAILED", err_msg, k)
        # end of try/ex

        if debug:
            self.lg("Add to Cache Done", 6)

        return results
    # end of add_records_to_cache_in_redis

    
    def purge_and_cache_records_in_redis(self, redis_app, dest_key, message, debug=False):

        results                         = {}
        results["Status"]               = "FAILED"
        results["Error"]                = ""
        results["Record"]               = {}

        try:
            if debug:
                self.lg("Purge and Cache(" + str(dest_key) + ") RA(" + str(redis_app.get_address()) + ")", 6)

            if redis_app.m_rw == None:
                redis_app.connect()

            found_msg = True
            while found_msg != None:
                found_msg = redis_app.m_rw.get(False, 0.01, dest_key)
            # end of purging this cache

            redis_app.put_into_key(dest_key, message)

            results["Record"]           = {
                                            "Address"   : str(redis_app.get_address()),
                                            "Key"       : dest_key
                                        }
            results["Status"]           = "SUCCESS"
            results["Error"]            = ""
            if debug:
                self.lg("Purge and Cache Done", 6)

        except ValueError, e:
            err_msg                     = "Connection to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Non-Pickle Formatted Message Ex(" + str(e) +")"
            self.lg("ERROR: " + str(err_msg), 0)
            results["Status"]           = "FAILED"
            results["Error"]            = str(err_msg)
            results["Record"]           = {}
        except Exception, e:
            test_for_redis_connectivity = str(e)
            if "Connection refused." in test_for_redis_connectivity:
                err_msg                 = "Connection REFUSED to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
                results["Record"]       = {}

            else:
                err_msg                 = "Purge and Cache Failed to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
                results["Record"]       = {}
        # end of try/ex

        if debug:
            self.lg("Purge and Cache Done", 6)

        return results
    # end of purge_and_cache_records_in_redis

    
    def get_all_records_from_cache_in_redis(self, redis_app, dest_key, debug=False):

        results                         = {}
        results["Status"]               = "FAILED"
        results["Error"]                = ""
        results["Record"]               = {
                                            "Cache" : []
                                        }

        try:
            if debug:
                self.lg("Get All From Cache(" + str(dest_key) + ") RA(" + str(redis_app.get_address()) + ")", 6)

            if redis_app.m_rw == None:
                redis_app.connect()

            found_msg = True
            while found_msg != None:
                found_msg           = redis_app.m_rw.get(False, 0.01, dest_key)

                if found_msg:
                    results["Record"]["Cache"].append(found_msg)

            # end of purging this cache

            results["Status"]           = "SUCCESS"
            results["Error"]            = ""
            if debug:
                self.lg("Get All(" + str(len(results["Record"]["Cache"])) + ") From Cache Done", 6)

        except ValueError, e:
            err_msg                     = "Get All From Cache - Connection to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Non-Pickle Formatted Message Ex(" + str(e) +")"
            self.lg("ERROR: " + str(err_msg), 0)
            results["Status"]           = "FAILED"
            results["Error"]            = str(err_msg)
            results["Record"]           = {}
        except Exception, e:
            test_for_redis_connectivity = str(e)
            if "Connection refused." in test_for_redis_connectivity:
                err_msg                 = "Get All From Cache - Connection REFUSED to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
                results["Record"]       = {}

            else:
                err_msg                 = "Get All From Cache - Failed to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
                results["Record"]       = {}
        # end of try/ex

        if debug:
            self.lg("Get All From Cache Done", 6)

        return results
    # end of get_all_records_from_cache_in_redis

    
    def get_a_message_from_redis(self, redis_app, dest_key, debug=False):

        results                         = {}
        results["Status"]               = "FAILED"
        results["Error"]                = ""
        results["Record"]               = {}

        try:
            if debug:
                self.lg("Get A Msg(" + str(dest_key) + ") RA(" + str(redis_app.get_address()) + ")", 6)

            if redis_app.m_rw == None:
                redis_app.connect()

            found_msg = True
            while found_msg != None:
                found_msg           = redis_app.m_rw.get(False, 0.01, dest_key)

                if found_msg:
                    results["Record"]       = found_msg
                    results["Status"]       = "SUCCESS"
                    results["Error"]        = ""
                    return results
                else:
                    results["Record"]       = {}
                    results["Status"]       = "No Record"
                    results["Error"]        = ""
                    return results

            # end of purging this cache

            if debug:
                self.lg("Get Msg(" + str(len(results["Record"])) + ") Done", 6)

        except ValueError, e:
            err_msg                     = "Get A Msg - Connection to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Non-Pickle Formatted Message Ex(" + str(e) +")"
            self.lg("ERROR: " + str(err_msg), 0)
            results["Status"]           = "FAILED"
            results["Error"]            = str(err_msg)
            results["Record"]           = {}
        except Exception, e:
            test_for_redis_connectivity = str(e)
            if "Connection refused." in test_for_redis_connectivity:
                err_msg                 = "Get A Msg - Connection REFUSED to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
                results["Record"]       = {}

            else:
                err_msg                 = "Get A Msg - Failed to Address(" + str(redis_app.get_address()) + ") Results Key(" + str(dest_key) + ") Received a Ex(" + str(e) +")"
                self.lg("ERROR: " + str(err_msg), 0)
                results["Status"]       = "FAILED"
                results["Error"]        = str(err_msg)
                results["Record"]       = {}
        # end of try/ex

        if debug:
            self.lg("Get a Msg Done", 6)

        return results
    # end of get_a_message_from_redis

    
    def blocking_get_cache_from_redis(self, redis_app, cache_key, timeout_in_seconds=0, debug=False):

        cache_results       = self.core_build_def_hash("No Results", "No Results", {})

        try:

            if debug:
                self.lg("Blocking Getting Cache(" + str(cache_key) + ")", 6)

            if redis_app.m_rw == None:
                redis_app.connect()

            test_cache              = {}
            # timeout_in_seconds    = 0 means it will be forever
            test_cache              = redis_app.m_rw.get(True, timeout_in_seconds, cache_key)

            if test_cache != None:

                if len(test_cache) > 0:
                    cache_results   = self.core_build_def_hash("SUCCESS",    "", test_cache)
                else:
                    cache_results   = self.core_build_def_hash("SUCCESS",    "", {})

            else:
                cache_results       = self.core_build_def_hash("No Results", "No Results", {})

            if debug:
                self.lg("Cache(" + str(cache_key) + ") Results(" + str(cache_results) + ")", 6)

        except Exception,k:

            err_msg                 = "Failed to Blocking Get Cache(" + str(cache_key) + ") Results with Error(" + str(cache_results["Error"]) + ") Exception(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            cache_results           = self.handle_core_exception("FAILED", err_msg, k)
        # end of try/ex

        return cache_results
    # end of blocking_get_cache_from_redis


    def get_cache_from_redis(self, redis_app, cache_key, ra_blocking=True, debug=False):

        cache_results       = self.core_build_def_hash("No Results", "No Results", {})

        try:

            if debug:
                self.lg("Getting Cache(" + str(cache_key) + ")", 6)

            if redis_app.m_rw == None:
                redis_app.connect()

            test_cache              = {}

            if ra_blocking:
                test_cache          = redis_app.get_cached_data_for_key(cache_key)

            # for now there's no block call...and that's to prevent deadlock-ed jobs
            else:
                test_cache          = redis_app.get_cached_data_for_key(cache_key)

            if test_cache["Status"] == "SUCCESS":

                if test_cache["Value"]:
                    cache_results   = self.core_build_def_hash("SUCCESS",    "", test_cache["Value"])
                else:
                    cache_results   = self.core_build_def_hash("SUCCESS",    "", {})

            else:

                if "Error" in test_cache:
                    cache_results   = self.core_build_def_hash("No Results", str(test_cache["Error"]), {})
                else:
                    cache_results   = self.core_build_def_hash("No Results", "No Data in Cache Key(" + str(cache_key) + ")", {})

            if debug:
                self.lg("Cache(" + str(cache_key) + ") Results(" + str(cache_results) + ")", 6)

        except Exception,k:

            err_msg                 = "Failed to get Cache(" + str(cache_key) + ") Results with Error(" + str(cache_results["Error"]) + ") Exception(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            cache_results           = self.handle_core_exception("FAILED", err_msg, k)
        # end of try/ex

        return cache_results
    # end of get_cache_from_redis


    def safe_get_cache_from_redis(self, rd_app, cache_key, num_retries=1000, blocking=False, debug=False):
        
        cache_results       = self.core_build_def_hash("No Results", "No Results", {})
        
        try:

            if rd_app != None and cache_key != "":

                if rd_app.m_rw == None:
                    rd_app.connect()

                if debug:
                    self.lg("SC(" + str(rd_app.get_address()) + ") Cache(" + str(cache_key) + ") Retries(" + str(num_retries) + ")", 5)

                import datetime
                from time   import time, sleep
                waiting                 = True
                while waiting:
                    cache_records       = self.get_cache_from_redis(rd_app, cache_key, blocking, debug)

                    if debug:
                        self.lg("Cache(" + str(cache_key) + ") Records(" + str(cache_records) + ")", 6)

                    if len(cache_records) > 0:

                        if debug:
                            self.lg("Found Hits", 6)

                        cache_results           = {}
                        cache_results["Status"] = "SUCCESS"
                        cache_results["Error"]  = ""
                        cache_results["Record"] = cache_records["Record"]

                        if debug:
                            self.lg("Returning(" + str(cache_results["Record"]).replace("\n", "")[0:128] + ")", 5)

                        return cache_results

                    elif "Status" in cache_records and cache_records["Status"] == "SUCCESS":
                        if debug:
                            self.lg("Success Cache Record", 6)
                            self.lg("Cache(" + str(cache_key) + ") Records(" + str(len(cache_records)) + ")", 6)

                        cache_results       = self.core_build_def_hash("SUCCESS", "", cache_records)
                        return cache_results

                    else:
                        if debug:
                            self.lg("Counting Down", 6)
                        num_retries         -= 1
                        if num_retries < 0:
                            self.lg("ERROR: SAFE - Max retry for Cache(" + str(cache_key) + ")", 0)
                            waiting         = False
                        else:
                            self.lg("Sleeping", 6)
                            sleep(0.001)
                # end of while waiting for a cache restore

                if num_retries < 0 and cache_results["Status"] != "SUCCESS":
                    err_msg                 = "Safe - Failed to find Cache in Key(" + str(cache_key) + ") Records"
                    self.lg("ERROR: " + str(err_msg), 0)
                    cache_results           = self.core_build_def_hash("Display Error", err_msg, {})
                    return cache_results
            # end of valid safe cache reader            
            else:
                err_msg                     = "Safe - Invalid Attempt to read cache RA(" + str(rd_app) + ") Key(" + str(cache_key) + ")"
                self.lg("ERROR: " + str(err_msg), 0)
                cache_results               = self.core_build_def_hash("Display Error", err_msg, {})
                return cache_results

            # end of 

        except Exception,k:

            err_msg                 = "Failed to Safe Get from Cache(" + str(cache_key) + ") Results with Error(" + str(cache_results["Error"]) + ") Exception(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            cache_results           = self.handle_core_exception("FAILED", err_msg, k)
        # end of try/ex

        return cache_results
    # end of safe_get_cache_from_redis


    #####################################################################################################
    #
    # Core Slack Integration
    #
    #####################################################################################################


    def post_message_to_slack(self, channel, message, username="algobot", debug=False):
        
        results                 = self.core_build_def_hash("Display Error", "Not Run", {
                                            })

        try:
            import slackclient

            if debug:
                self.lg("Posting to Slack(" + str(channel) + ") Message(" + str(message)[0:10] + ")", 6)

            slack               = slackclient.SlackClient(self.m_slack_node["Token"])

            slack.api_call("chat.postMessage", channel=channel, text=message, username=username, as_user=True)
            
            if debug:
                self.lg("Done Posting to Slack(" + str(channel) + ")", 6)

        except Exception, e:
            err_msg             = "Failed to post message to slack with Ex(" + str(e) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results             = self.core_build_def_hash("Display Error", str(err_msg), {
                                            })
            results["Status"]   = "FAILED"
        # end of try/ex

        return results
    # end of post_message_to_slack


    def handle_send_slack_internal_ex(self, ex, debug=False):

        try:

            if self.m_slack_enabled:
                import traceback, sys
                exc_type, exc_obj, exc_tb = sys.exc_info()
                header_str          = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S") + " @" + str(self.m_slack_node["NotifyUser"]) + " `" + str(self.m_slack_node["EnvName"]) + "` *" + str(ex) + "*\n"
                ex_error            = self.get_exception_error_message(ex, exc_type, exc_obj, exc_tb, True, debug)
                send_slack_msg      = header_str + str(ex_error) + "\n"
                self.post_message_to_slack("#" + str(self.m_slack_node["ChannelName"]), send_slack_msg, self.m_slack_bot, debug)

        except Exception,k:
            if debug:
                self.lg("ERROR: Failed to Send Slack Error with Ex(" + str(k) + ")", 0)
        return None
    # end of handle_send_slack_internal_ex

    
# end of PyCore
