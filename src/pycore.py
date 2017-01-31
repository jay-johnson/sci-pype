import os, inspect, datetime, uuid, json, glob, random, logging, sys, copy, time
from   sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, MetaData, Date, DateTime, Float, Boolean, and_, or_, asc, desc
from   sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker, relation
from   sqlalchemy.ext.declarative import declarative_base

from   src.common.shellprinting import *
from   src.logger.logger        import Logger


class PyCore:

    def __init__(self, core_manifest=str(os.getenv("ENV_CONFIGS_DIR", "/opt/work/configs") + "/jupyter.json")):

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
        self.load_json()

        # Assign the name out of the json config
        self.m_name                 = str(self.m_core_json["Core"]["Name"])
        self.m_locale_dict          = {}
        self.m_locale_abb_dict      = {}

        self.load_db_apps()
        
        self.load_redis_apps()

        self.m_last_start_time          = None
        self.m_last_end_time            = None
        self.m_last_check_time          = None

        self.m_colors           = {
                                    "red"           : "#E74C3C",
                                    "feldspar"      : "#D19275",
                                    "orange"        : "#FF7D40",
                                    "pink"          : "#FFCCCC",
                                    "green"         : "#2ECC71",
                                    "blue"          : "#3498db",
                                    "black"         : "#111111",
                                    "copper"        : "#EDC393",
                                    "brown"         : "#6B4226",
                                    "lightgreen"    : "#C0FF3E",
                                    "darkgreen"     : "#385E0F",
                                    "maroon"        : "#800000",
                                    "gray"          : "#8B8989",
                                    "gold"          : "#FFCC11",
                                    "yellow"        : "#FFE600",
                                    "volumetop"     : "#385E0F",
                                    "volume"        : "#ADFF2F",
                                    "high"          : "#CC1100",
                                    "low"           : "#164E71",
                                    "open"          : "#608DC0",
                                    "close"         : "#99CC32",
                                    "white"         : "#FFFFFF"
                                }

        self.m_last_color_idx   = -1
        self.m_color_rotation   = []

        self.m_is_notebook      = False
    # end of __init__

     
    def lg(self, msg, level=6):

        # log it to syslog
        if self.m_log:
            # concat them
            full_msg = self.m_name + ": " + msg

            self.m_log.log(full_msg, level)

        else:
            if not self.m_is_notebook:
                lg(str(self.m_name) + ": " + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + " " + str(msg), level)

        if self.m_debug:
            lg(str(self.m_name) + ": " + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + " " + str(msg), level)

        return None
    # end of lg

    
    #####################################################################################################
    #
    # Initialize Resources
    #
    #####################################################################################################


    def init_resources(self):
        self.load_json()
        self.load_db_apps()
        self.load_redis_apps()
    # end of init_resources


    def load_json(self):

        if len(self.m_core_json) == 0:
            self.m_core_json        = json.loads(open(self.m_core_file).read())
            self.m_db_apps_json     = json.loads(open(self.m_core_json["Core"]["Envs"][self.m_env]["Database"]).read())
            self.m_rd_apps_json     = json.loads(open(self.m_core_json["Core"]["Envs"][self.m_env]["Redis"]).read())

    # end of load_json


    def load_db_apps(self):

        self.load_json()

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

    # end of load_db_apps

   
    def load_redis_apps(self):
        
        self.load_json()

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

    # end of load_redis_apps


    def load_thirdparty_dir(self, dir_name, debug=False):
        load_dir    = "/opt/work/src/thirdparty/" + str(dir_name)
        if debug:
            print load_dir
        self.load_src_path("ENV_THIRD_PARTY_SOURCE_DIR", load_dir)
    # end of load_thirdparty_dir


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


    def enable_debug(self):
        self.m_debug    = True
    # end of enable_debug


    def disable_debug(self):
        self.m_debug    = False
    # end of disable_debug


    def is_notebook(self):
        self.m_is_notebook  = True
    # end of is_notebook


    #####################################################################################################
    #
    # AWS Methods
    #
    #####################################################################################################


    def running_on_aws(self, debug=False):
        return os.path.exists("/opt/aws/bin/ec2-metadata")
    # end of running_on_aws


    def aws_get_keys(self, debug=False):
        record  = {
                    "Key"       : os.getenv("ENV_AWS_KEY"),
                    "Secret"    : os.getenv("ENV_AWS_SECRET")
                }
        return record
    # end of aws_get_keys


    def aws_get_instance_from_metadata(self, debug=False):

        results                     = self.build_def_hash("Display Error", "Failed to Get EC2 Instance from MetaData", {
                                            "Name"          : "",
                                            "InstanceID"    : "",
                                            "InstanceType"  : "",
                                            "ImageID"       : "",
                                            "Running"       : "",
                                            "ImageName"     : "",
                                            "ExternalIP"    : "",
                                            "InternalIP"    : ""
                                    })

        try:

            import os, boto

            if os.path.exists("/tmp/publicip"):
                os.system("rm -f /tmp/publicip >> /dev/null")

            
            cur_ip                  = ""
            if self.running_on_aws():
                os.system("/opt/aws/bin/ec2-metadata | grep public-ipv4 | awk '{print $NF}' > /tmp/publicip")
                cur_ip                  = open("/tmp/publicip").read().strip().lstrip()
            else:
                cur_ip       = "54.188.188.188"

            if cur_ip == "":
                self.lg("ERROR: Invalid IP(" + str(cur_ip) + ")", 0)
            else:

                self.lg("Looking for IP(" + str(cur_ip) + ")", 6)
                aws_creds               = self.aws_get_keys()
                ec2                     = boto.connect_ec2(aws_creds["Key"], aws_creds["Secret"])
                filters                 = {"ip-address": cur_ip}
                inst_list               = ec2.get_only_instances(filters=filters)

                if len(inst_list) > 0:
                    instance            = inst_list[0]
                    if str(instance.ip_address) == str(cur_ip):
                        #self.lg("Res(" + str(reservation.id) + ") Instance(" + str(iidx) + ") ID(" + str(instance) + ")", 6)
                        tag_name        = ""
                        if "Name" in instance.tags:
                            tag_name    = str(instance.tags["Name"])
                        
                        ami_results     = ec2.get_all_images(image_ids=[str(instance.image_id)])
                        ami_name        = ""

                        if len(ami_results) > 0:
                            if str(ami_results[0].name) != "":
                                ami_name= str(ami_results[0].name)

                        results["Record"]   = {
                                                                "Name"          : str(tag_name),
                                                                "InstanceID"    : str(instance.id),
                                                                "InstanceType"  : str(instance.instance_type),
                                                                "ImageID"       : str(instance.image_id),
                                                                "Running"       : str(instance.state),
                                                                "ImageName"     : str(ami_name),
                                                                "ExternalIP"    : str(instance.ip_address),
                                                                "InternalIP"    : str(instance.private_ip_address)
                                            }
            
                        if not self.running_on_aws():
                            results["Record"]["Name"]   = "DSWorker-1"
                    # end if the ip matches
                # end of get all instances

            # end of if there's an ip or not
             
            os.system("rm -f /tmp/publicip >> /dev/null")

            results["Status"]       = "SUCCESS"
            results["Error"]        = ""

        except Exception,e:

            err_msg                 = "Failed to Get Instance from MetaData with Ex(" + str(e) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results                 = self.build_def_hash("Display Error", "Failed to Get Instance From MetaData", {
                                            "Name"          : "",
                                            "InstanceID"    : "",
                                            "InstanceType"  : "",
                                            "ImageID"       : "",
                                            "Running"       : "",
                                            "ImageName"     : "",
                                            "ExternalIP"    : "",
                                            "InternalIP"    : ""
                                    })
            results["Status"]       = "FAILED"
            results["Error"]        = ""

        # end of try/ex

        return results
    # end of aws_get_instance_from_metadata


    def aws_get_instance_from_name(self, cur_name, debug=False):

        results                     = self.build_def_hash("Display Error", "Failed to Get EC2 Instance by Name", {
                                            "Name"          : "",
                                            "InstanceID"    : "",
                                            "InstanceType"  : "",
                                            "ImageID"       : "",
                                            "Running"       : "",
                                            "ImageName"     : "",
                                            "ExternalIP"    : "",
                                            "InternalIP"    : ""
                                    })

        try:

            import os, boto

            if cur_name == "":
                self.lg("ERROR: Invalid Name(" + str(cur_name) + ")", 0)
            else:

                self.lg("Looking for Name(" + str(cur_name) + ")", 6)
                aws_creds               = self.aws_get_keys()
                ec2                     = boto.connect_ec2(aws_creds["Key"], aws_creds["Secret"])
                filters                 = {"tag:Name" : cur_name}
                inst_list               = ec2.get_only_instances(filters=filters)

                if len(inst_list) > 0:
                    instance            = inst_list[0]
                    if str(instance.ip_address) != "":
                        tag_name        = ""
                        if "Name" in instance.tags:
                            tag_name    = str(instance.tags["Name"])

                            if str(tag_name).lower().strip().lstrip() == str(cur_name).lower().strip().lstrip():
                                
                                ami_results     = ec2.get_all_images(image_ids=[str(instance.image_id)])
                                ami_name        = ""

                                if len(ami_results) > 0:
                                    if str(ami_results[0].name) != "":
                                        ami_name= str(ami_results[0].name)

                                results["Record"]   = {
                                                                        "Name"          : str(tag_name),
                                                                        "InstanceID"    : str(instance.id),
                                                                        "InstanceType"  : str(instance.instance_type),
                                                                        "ImageID"       : str(instance.image_id),
                                                                        "Running"       : str(instance.state),
                                                                        "ImageName"     : str(ami_name),
                                                                        "ExternalIP"    : str(instance.ip_address),
                                                                        "InternalIP"    : str(instance.private_ip_address)
                                                    }
                
                    # end if the ip matches
                # end of get all instances

            # end of if there's an ip or not

            results["Status"]       = "SUCCESS"
            results["Error"]        = ""

        except Exception,e:

            err_msg                 = "Failed to Get Instance from Name with Ex(" + str(e) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results                 = self.build_def_hash("Display Error", "Failed to Get Instance From Name", {
                                            "Name"          : "",
                                            "InstanceID"    : "",
                                            "InstanceType"  : "",
                                            "ImageID"       : "",
                                            "Running"       : "",
                                            "ImageName"     : "",
                                            "ExternalIP"    : "",
                                            "InternalIP"    : ""
                                    })
            results["Status"]       = "FAILED"
            results["Error"]        = ""

        # end of try/ex

        return results
    # end of aws_get_instance_from_name


    def aws_get_instances(self, debug=False):

        results                     = self.build_def_hash("Display Error", "Failed to Get EC2 Instances", { "Instances" : [] })

        try:

            import os, boto

            aws_creds               = self.aws_get_keys()
            ec2                     = boto.connect_ec2(aws_creds["Key"], aws_creds["Secret"])

            reservations            = ec2.get_all_instances()
            for ridx, reservation in enumerate(reservations):
                for iidx, instance in enumerate(reservation.instances):
                    #self.lg("Res(" + str(reservation.id) + ") Instance(" + str(iidx) + ") ID(" + str(instance) + ")", 6)
                    tag_name        = ""
                    if "Name" in instance.tags:
                        tag_name    = str(instance.tags["Name"])
                    
                    ami_results     = ec2.get_all_images(image_ids=[str(instance.image_id)])
                    ami_name        = ""

                    if len(ami_results) > 0:
                        if str(ami_results[0].name) != "":
                            ami_name= str(ami_results[0].name)

                    results["Record"]["Instances"].append({
                                                            "Name"          : str(tag_name),
                                                            "InstanceID"    : str(instance.id),
                                                            "InstanceType"  : str(instance.instance_type),
                                                            "ImageID"       : str(instance.image_id),
                                                            "Running"       : str(instance.state),
                                                            "ImageName"     : str(ami_name),
                                                            "ExternalIP"    : str(instance.ip_address),
                                                            "InternalIP"    : str(instance.private_ip_address)
                                                    })

                # end of get all instances

            # end of get all reservations
             
            results["Status"]   = "SUCCESS"
            results["Error"]    = ""

        except Exception,e:

            err_msg                 = "Failed to Get All Instances with Ex(" + str(e) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results                 = self.build_def_hash("Display Error", "Failed to Get EC2 Instances", {})
            results["Status"]       = "FAILED"
            results["Error"]        = ""

        # end of try/ex

        return results
    # end of aws_get_instances


    #####################################################################################################
    #
    # General Util Methods
    #
    #####################################################################################################


    def get_dbs(self):
        return self.m_dbs
    # end of get_dbs
    

    def get_rds(self):
        return self.m_rds
    # end of get_rds


    def db_convert_utc_date_to_str(self, db_cur_date):
        return_str  = ""
        if db_cur_date != None:
            convert_date    = db_cur_date - datetime.timedelta(hours=4)
            return_str      = str(convert_date.strftime('%m/%d/%Y %H:%M:%S'))
        return return_str
    # end of db_convert_utc_date_to_str


    def db_convert_date_to_str(self, db_cur_date, optional_format="%m/%d/%Y %H:%M:%S"):
        return_str  = ""
        if db_cur_date != None:
            return_str  = str(db_cur_date.strftime(optional_format))
        return return_str
    # end of db_convert_date_to_str

    
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


    def build_unique_key(self, length=-1):
        return str(str(uuid.uuid4()).replace("-", "")[0:length])
    # end of build_unique_key


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


    def get_random_number_in_range(self, min_int, max_int):
        import random
        return random.randint(min_int, max_int)
    # end of get_random_number_in_range


    def get_percent_done(self, progress, total):
        return "%0.2f" % float(float(progress)/float(total)*100.00)
    # end of get_percent_done


    def to_float_str(self, cur_float):
        return str("%0.2f" % float(cur_float))
    # end of to_float_str
    
      
    def to_upper(self, cur_str):
        return str(cur_str).upper().strip().lstrip()
    # end of to_upper
    
    
    def width_percent_done(self, idx, total):
        percent_str     = "Percent(" + str(self.get_percent_done(idx, total)) + ")"
        if len(percent_str) < 14:
            percent_str += " "
        return percent_str
    # end of width_percent_done 
    

    def timer_start(self):
        self.m_last_start_time  = datetime.datetime.now()
    # end of timer_start


    def timer_end(self):
        self.m_last_end_time    = datetime.datetime.now()
    # end of timer_end


    def how_long(self):
        if self.m_last_start_time == None:
            self.lg("Forgot to start the timer with: self.timer_start()", 0)
            return "-1"

        # In case I forget to stop the timer just set it to whenever the how_long was invoked
        elif self.m_last_end_time == None:
            self.timer_end()

        return self.to_float_str(float((self.m_last_end_time - self.m_last_start_time).total_seconds()))
    # end of how_long

      
    def log_msg_to_unique_file(self, msg, path_to_file="/tmp/errors_to_look_at_"):
    
        log_file    = str(path_to_file) + str(uuid.uuid4()).replace("-", "") + ".log"
        with open(log_file, "w") as output_file:
            output_file.write(str(msg))

        return log_file
    # end of log_msg_to_unique_file


    def write_json_to_file(self, output_file, record_json):

        try:
            temp_output     = "/tmp/tmpfile_" + datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S") + "_"
            temp_file       = self.log_msg_to_unique_file(self.ppj(record_json), temp_output)
            os.system("mv " + str(temp_file) + " " + str(output_file))

            if os.path.exists(output_file):
                return output_file
            else:
                return "FAILED_TO_CREATE_FILE"

        except Exception,k:
            print "ERROR: Failed to write file with ppj with Ex(" + str(k) + ")"
            return "FILE_DOES_NOT_EXIST"
        # end of try/ex

        return output_file 
    # end of write_json_to_file


    def build_def_hash(self, start_status="FAILED", start_error="", record={}):
        return  { "Status" : str(start_status), "Error" : str(start_error), "Record" : record }
    # end of build_def_hash
    
    
    def handle_display_error(self, err_msg, def_rec={}, debug=False):

        results                 = {}
        results["Status"]       = "Display Error"
        results["Error"]        = str(err_msg)
        results["Record"]       = def_rec

        self.lg("ERROR: " + str(err_msg), 0)

        if debug:
            lg("ERROR: " + str(err_msg), 0)

        return results
    # end of handle_display_error


    def handle_general_error(self, status, err_msg, def_rec={}, debug=False):

        results                 = {}
        results["Status"]       = str(status)
        results["Error"]        = str(err_msg)
        results["Record"]       = def_rec

        if debug:
            self.lg("ERROR: " + str(err_msg), 0)

        return results
    # end of handle_general_error

    
    def handle_exception(self, status, err_msg, ex, debug=False):
        
        results                 = self.build_def_hash(status, err_msg, {
                                                "Exception" : "Failed to Process"
                                            })

        try:

            if self.m_slack_enabled:
                self.handle_send_slack_internal_ex(ex, debug)
                results             = self.build_def_hash("SUCCESS", "", {
                                                    "Exception" : ""
                                            })
            else:
                import traceback, sys
                exc_type, exc_obj, exc_tb = sys.exc_info()
                ex_error            = self.get_exception_error_message(ex, exc_type, exc_obj, exc_tb, False, debug)
                results             = self.build_def_hash("SUCCESS", "", {
                                                    "Exception" : str(ex_error)
                                            })
            # end of branching if slack supported or not

        except Exception, e:
            err_msg             = "Failed to post message to slack with Ex(" + str(e) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results             = self.build_def_hash("Display Error", str(err_msg), {
                                                "Exception" : "Failed Processing with Exception"
                                            })
            results["Status"]   = "FAILED"
        # end of try/ex

        return results
    # end of handle_exception

    
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
                cache_results           = self.handle_exception("FAILED", err_msg, k)
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

        cache_results       = self.build_def_hash("No Results", "No Results", {})

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
                    cache_results   = self.build_def_hash("SUCCESS",    "", test_cache)
                else:
                    cache_results   = self.build_def_hash("SUCCESS",    "", {})

            else:
                cache_results       = self.build_def_hash("No Results", "No Results", {})

            if debug:
                self.lg("Cache(" + str(cache_key) + ") Results(" + str(cache_results)[0:100] + ")", 6)

        except Exception,k:

            err_msg                 = "Failed to Blocking Get Cache(" + str(cache_key) + ") Results with Error(" + str(cache_results["Error"]) + ") Exception(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            cache_results           = self.handle_exception("FAILED", err_msg, k)
        # end of try/ex

        return cache_results
    # end of blocking_get_cache_from_redis


    def get_cache_from_redis(self, redis_app, cache_key, ra_blocking=True, debug=False):

        cache_results       = self.build_def_hash("No Results", "No Results", {})

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
                    cache_results   = self.build_def_hash("SUCCESS",    "", test_cache["Value"])
                else:
                    cache_results   = self.build_def_hash("SUCCESS",    "", {})

            else:

                if "Error" in test_cache:
                    cache_results   = self.build_def_hash("No Results", str(test_cache["Error"]), {})
                else:
                    cache_results   = self.build_def_hash("No Results", "No Data in Cache Key(" + str(cache_key) + ")", {})

            if debug:
                self.lg("Cache(" + str(cache_key) + ") Results(" + str(cache_results)[0:100] + ")", 6)

        except Exception,k:

            err_msg                 = "Failed to get Cache(" + str(cache_key) + ") Results with Error(" + str(cache_results["Error"]) + ") Exception(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            cache_results           = self.handle_exception("FAILED", err_msg, k)
        # end of try/ex

        return cache_results
    # end of get_cache_from_redis


    def ra_get_cache_from_redis(self, ra_loc, rds, ra_blocking=True, debug=False):

        cache_results       = self.build_def_hash("No Results", "No Results", {})

        try:

            split_arr               = ra_loc.split(":")
            ra_name                 = str(split_arr[0])
            cache_key               = str(split_arr[1])

            if ra_name not in rds:
                err_msg = "Missing RA App Name(" + str(ra_name) + ") from RDS"
                return self.handle_display_error(err_msg, record, True)

            redis_app               = rds[ra_name]
            
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
                    cache_results   = self.build_def_hash("SUCCESS",    "", test_cache["Value"])
                else:
                    cache_results   = self.build_def_hash("SUCCESS",    "", {})

            else:

                if "Error" in test_cache:
                    cache_results   = self.build_def_hash("No Results", str(test_cache["Error"]), {})
                else:
                    cache_results   = self.build_def_hash("No Results", "No Data in Cache Key(" + str(cache_key) + ")", {})

            if debug:
                self.lg("Cache(" + str(cache_key) + ") Results(" + str(cache_results)[0:100] + ")", 6)

        except Exception,k:

            err_msg                 = "Failed to get Cache(" + str(cache_key) + ") Results with Error(" + str(cache_results["Error"]) + ") Exception(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            cache_results           = self.handle_exception("FAILED", err_msg, k)
        # end of try/ex

        return cache_results
    # end of ra_get_cache_from_redis


    def safe_get_cache_from_redis(self, rd_app, cache_key, num_retries=1000, blocking=False, debug=False):
        
        cache_results       = self.build_def_hash("No Results", "No Results", {})
        
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

                        cache_results       = self.build_def_hash("SUCCESS", "", cache_records)
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
                    cache_results           = self.build_def_hash("Display Error", err_msg, {})
                    return cache_results
            # end of valid safe cache reader            
            else:
                err_msg                     = "Safe - Invalid Attempt to read cache RA(" + str(rd_app) + ") Key(" + str(cache_key) + ")"
                self.lg("ERROR: " + str(err_msg), 0)
                cache_results               = self.build_def_hash("Display Error", err_msg, {})
                return cache_results

            # end of 

        except Exception,k:

            err_msg                 = "Failed to Safe Get from Cache(" + str(cache_key) + ") Results with Error(" + str(cache_results["Error"]) + ") Exception(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            cache_results           = self.handle_exception("FAILED", err_msg, k)
        # end of try/ex

        return cache_results
    # end of safe_get_cache_from_redis


    #####################################################################################################
    #
    # Core Slack Integration
    #
    #####################################################################################################


    def post_message_to_slack(self, channel, message, username="algobot", debug=False):
        
        results                 = self.build_def_hash("Display Error", "Not Run", {
                                            })

        try:
            import slackclient

            if debug:
                self.lg("Posting to Slack(" + str(channel) + ") Message(" + str(message)[0:10] + ")", 6)
            else:
                slack               = slackclient.SlackClient(self.m_slack_node["Token"])
                slack.api_call("chat.postMessage", channel=channel, text=message, username=username, as_user=True)

            if debug:
                self.lg("Done Posting to Slack(" + str(channel) + ")", 6)

        except Exception, e:
            err_msg             = "Failed to post message to slack with Ex(" + str(e) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results             = self.build_def_hash("Display Error", str(err_msg), {
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

    
    #####################################################################################################
    #
    # Pandas and Matlab Helper Methods
    #
    #####################################################################################################


    def pd_convert_df_dates_to_list(self, df_list, date_format_str="%Y-%m-%d"):
        date_series         = df_list["Date"].apply(lambda x: x.strftime(date_format_str))
        return date_series.tolist()
    # end of pd_convert_df_dates_to_list


    def pd_json_to_df(self, data_json, sorted_by_key="Date", in_ascending=True):
        import pandas as pd
        new_df  = pd.read_json(data_json).sort_values(by=sorted_by_key, ascending=in_ascending)
        return new_df
    # end of pd_json_to_df


    def pd_empty_df(self, debug=False):
        import pandas as pd
        return pd.DataFrame({'Timestamp' : [ 0 ]})
    # end of pd_empty_df


    def pd_get_color(self, color_key="blue"):

        hex_plot_color  = self.m_colors["blue"]
        test_key        = str(color_key).lower().strip().lstrip()
        if test_key in self.m_colors:
            hex_plot_color  = str(self.m_colors[test_key])

        return hex_plot_color
    # end of pd_get_color


    def pd_add_footnote(self, fig):
        footnote_text   = str(os.getenv("ENV_PLOT_FOOTNOTE", "Your Footnote"))
        fig.text(0.99, 0.01, footnote_text, ha="right", va="bottom", fontsize=8, color="#888888")
    # end of pd_add_footnote


    def pd_print(self, df, mask=None):
        if mask:
            print df[mask]
        else:
            print df
    # end of pd_print


    def pd_change_xtick_freq(self, total_ticks, ax, debug=False):

        # Change the xaxis frequency
        if total_ticks > 30:
            n = 10
            ticks = ax.xaxis.get_ticklocs()
            ticklabels = [l.get_text() for l in ax.xaxis.get_ticklabels()]
            ax.xaxis.set_ticks(ticks[::n])
            ax.xaxis.set_ticklabels(ticklabels[::n])
        # end of changing the frequency

    # end of pd_change_xtick_freq


    def pd_set_date_ticks_by_number(self, total_ticks, ax, debug=False):

        ticks = ax.xaxis.get_ticklocs()
        ticklabels = [l.get_text() for l in ax.xaxis.get_ticklabels()]
        ax.xaxis.set_ticks(ticks[::total_ticks])
        ax.xaxis.set_ticklabels(ticklabels[::total_ticks])

    # end of pd_set_date_ticks_by_number


    def pd_show_with_entities(self, x_label, y_label, title_msg, ax, fig, plt, legend_list=[], show_plot=True, debug=False):

        plt.xlabel(x_label)
        plt.ylabel(y_label)

        ax.set_title(title_msg)

        if len(legend_list) == 0:
            ax.legend(loc="best", prop={"size":"medium"})
        else:
            ax.legend(legend_list, loc="best", prop={"size": "medium"})

        self.pd_add_footnote(fig)
        plt.tight_layout()

        if show_plot:
            plt.show()
        else:
            plt.plot()

    # end of pd_show_with_entities


    def get_colors(self):
        return self.m_colors
    # end of get_colors


    def pd_get_color_from_id(self, color_int):
            
        if len(self.m_color_rotation) == 0:
            add_in_order            = [
                                        "blue",
                                        "green",
                                        "red",
                                        "gold",
                                        "brown",
                                        "lightgreen",
                                        "black",
                                        "darkgreen",
                                        "copper",
                                        "maroon",
                                        "orange"
                                    ]
            self.m_color_rotation   = []
            for ck in add_in_order:
                self.m_color_rotation.append(self.m_colors[ck])
            # end of list
        # if color rotation

        hex_color       = self.m_color_rotation[0]

        if color_int == -1:
            if self.m_last_color_idx == -1:
                self.m_last_color_idx   = 0
            else:
                self.m_last_color_idx += 1
                if self.m_last_color_idx > len(self.m_color_rotation):
                    self.m_last_color_idx = 0
            return self.m_color_rotation[self.m_last_color_idx]
        else:
            target_idx      = 0 
            max_colors      = len(self.m_color_rotation)
            if color_int > 0 and color_int > max_colors:
                target_idx  = int(color_int % max_colors)
            else:
                target_idx  = color_int

            for idx,ck in enumerate(self.m_color_rotation):
                if idx == int(target_idx):
                    self.m_last_color_idx   = idx
                    return self.m_color_rotation[idx]
            # end of for loop

            self.m_last_color_idx   = 0
            return hex_color
    # end of pd_get_color_from_id


    def plt_feature_importance(self, record, plot_max_features, max_valid_features, plot_title):
            
        import pandas as pd
        width               = 15.0
        height              = 10.0
        fig, ax             = plt.subplots(figsize=(width, height))
        plt.title(plot_title)

        max_bars            = plot_max_features
        plt_display_names   = []
        max_range           = max_valid_features
        if max_range > max_bars:
            max_range       = max_bars

        plot_df             = pd.DataFrame(record["Rankings"][0:max_bars])
        bar_colors          = []
        for idx in range(max_range):
            hex_color       = self.pd_get_color_from_id(idx)
            bar_colors.append(hex_color)
        # end of trained features

        total_rows          = float(len(plot_df.index))
        bar_width           = 0.6
        bar_offset          = float(bar_width)/2.0
        largest_imp         = 0.0
        for ridx, pd_row in plot_df.iterrows():
            plt.bar(ridx-bar_offset, float(pd_row["Importance"]), bar_width, color=bar_colors[ridx])
            plt_display_names.append(pd_row["DisplayName"].replace(" ", "\n"))
            if float(pd_row["Importance"]) > largest_imp:
                largest_imp = float(pd_row["Importance"])
        # end of all rows


        plt.xticks(range(max_range), plt_display_names)
        plt.xlim([-1, max_range])

        if largest_imp < 20:
            plt.ylim([0, 20.0])

        self.pd_add_footnote(fig)

        self.pd_show_with_entities("Ranked Features", "Importance", plot_title, ax, fig, plt, x_labels, True, False)
        
        return None
    # end of plt_feature_importance


    #####################################################################################################
    #
    # S3 Helper Methods
    #
    #####################################################################################################


    def s3_create_id(self, dataset_name, date_str, debug=False):
        id_name = "DS_" + str(dataset_name) + "_" + str(date_str) + "_" + str(self.build_unique_key())
        return id_name
    # end of s3_create_id


    def s3_create_new_bucket(self, bucketname, bucket_location="sa-east-1", debug=False):

        record              = {
                            }

        results             = self.build_def_hash("Display Error", "Not Run", record)

        try:

            cur_keys        = self.aws_get_keys(debug)

            import boto 
            import boto.s3

            conn_s3         = boto.connect_s3(cur_keys["Key"], cur_keys["Secret"])
            bucket          = conn_s3.create_bucket(bucketname, location=bucket_location)

            if bucket:
                self.lg("Created Bucket(" + str(bucketname) + ")", 6)
                results     = self.build_def_hash("SUCCESS", "", {})
            else:
                results     = self.build_def_hash("Display Error", "Failed to Create Bucket(" + str(bucketname) + ")", {})

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to Create new S3 Bucket(" + str(bucketname) + ") with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of s3_create_new_s3_bucket


    def s3_upload_json_dataset(self, dataset_name, date_str, data_json, rds, dbs, bucketname="dataset-new", filename="", compress_json=True, delete_when_done=True, debug=False):

        record              = {
                                "File"  : "",
                                "Size"  : "0"
                            }

        results             = self.build_def_hash("Display Error", "Not Run", record)

        try:

            if filename == "":
                record["File"]  = self.ml_create_s3_id(dataset_name, date_str, debug) + ".json"
            else:
                record["File"]  = filename
                    
            cur_keys        = self.aws_get_keys(debug)
            cur_filename    = "/tmp/" + record["File"]

            file_path       = cur_filename
            if compress_json:
                temp_output = "/tmp/tmpfile_" + datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S") + "_"
                temp_file   = self.log_msg_to_unique_file(data_json, temp_output)
                os.system("mv " + str(temp_file) + " " + str(cur_filename))
            else:
                file_path   = self.write_json_to_file(cur_filename, data_json)

            import boto, math
            import boto.s3
    
            conn_s3         = boto.connect_s3(cur_keys["Key"], cur_keys["Secret"])
            bucket          = conn_s3.get_bucket(bucketname, validate=False)
            cur_filename    = os.path.basename(file_path)
            k               = bucket.new_key(cur_filename)
            mp              = bucket.initiate_multipart_upload(cur_filename)
            source_size     = os.stat(file_path).st_size
            bytes_per_chunk = 5000*1024*1024
            chunks_count    = int(math.ceil(source_size / float(bytes_per_chunk)))

            for i in range(chunks_count):
                offset      = i * bytes_per_chunk
                remaining_bytes = source_size - offset
                bytes       = min([bytes_per_chunk, remaining_bytes])
                part_num    = i + 1

                self.lg("S3 Uploading(" + str(cur_filename) + ") part " + str(part_num) + " of " + str(chunks_count), 6)

                with open(file_path, 'r') as fp:
                    fp.seek(offset)
                    mp.upload_part_from_file(fp=fp, part_num=part_num, size=bytes)
            # end of writing multipart files

            record["Size"]      = str(source_size)

            if len(mp.get_all_parts()) == chunks_count:
                mp.complete_upload()
                results         = self.build_def_hash("SUCCESS", "", record)
            else:
                mp.cancel_upload()
                results         = self.build_def_hash("Display Error", "Failed to Upload", record)

            if os.path.exists(cur_filename):
                os.system("rm -f " + str(cur_filename))

            if delete_when_done:
                if os.path.exists(file_path):
                    os.system("rm -f " + str(file_path))

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to Upload JSON Data to S3 with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of s3_upload_json_dataset


    def s3_upload_json_record(self, req, debug=False):

        record              = {
                                "Size"  : "0"
                            }

        results             = self.build_def_hash("Display Error", "Not Run", record)

        try:
                
            cur_filename    = "/tmp/uploadfile_" + datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S") + "_"
            s3_bucket       = req["S3Loc"].split(":")[0]
            s3_key          = req["S3Loc"].split(":")[1]

            cur_keys        = self.aws_get_keys(debug)

            file_path       = cur_filename
            if "Compress" in req:
                if bool(req["Compress"]):
                    temp_output = "/tmp/tmpfile_" + datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S") + "_"
                    temp_file   = self.log_msg_to_unique_file(req["JSON"], temp_output)
                    os.system("mv " + str(temp_file) + " " + str(cur_filename))
            else:
                file_path   = self.write_json_to_file(cur_filename, req["JSON"])

            import boto, math
            import boto.s3

            conn_s3         = boto.connect_s3(cur_keys["Key"], cur_keys["Secret"])
            bucket          = conn_s3.get_bucket(s3_bucket, validate=False)
            cur_filename    = os.path.basename(file_path)
            k               = bucket.new_key(s3_key)
            mp              = bucket.initiate_multipart_upload(s3_key.split("/")[-1])
            source_size     = os.stat(file_path).st_size
            bytes_per_chunk = 5000*1024*1024
            chunks_count    = int(math.ceil(source_size / float(bytes_per_chunk)))

            for i in range(chunks_count):
                offset      = i * bytes_per_chunk
                remaining_bytes = source_size - offset
                bytes       = min([bytes_per_chunk, remaining_bytes])
                part_num    = i + 1

                self.lg("S3 Uploading(" + str(cur_filename) + ") part " + str(part_num) + " of " + str(chunks_count), 6)

                with open(file_path, 'r') as fp:
                    fp.seek(offset)
                    mp.upload_part_from_file(fp=fp, part_num=part_num, size=bytes)
            # end of writing multipart files

            record["Size"]  = str(source_size)

            if len(mp.get_all_parts()) == chunks_count:
                mp.complete_upload()
                results     = self.build_def_hash("SUCCESS", "", record)
            else:
                mp.cancel_upload()
                results     = self.build_def_hash("Display Error", "Failed to Upload", record)

            if os.path.exists(cur_filename):
                os.system("rm -f " + str(cur_filename))

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to Upload JSON Record to S3 with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of s3_upload_json_record


    def s3_upload_csv_dataset(self, cur_csv_file, rds, dbs, bucketname="dataset-csv-new", filename="", delete_when_done=True, debug=False):

        record              = {
                                "File"  : "",
                                "Size"  : "0"
                            }

        results             = self.build_def_hash("Display Error", "Not Run", record)

        try:

            cur_keys        = self.aws_get_keys(debug)

            import boto, math
            import boto.s3

            conn_s3         = boto.connect_s3(cur_keys["Key"], cur_keys["Secret"])
            bucket          = conn_s3.get_bucket(bucketname, validate=False)
            cur_filename    = os.path.basename(cur_csv_file)
            k               = bucket.new_key(filename)
            mp              = bucket.initiate_multipart_upload(filename)
            source_size     = os.stat(cur_csv_file).st_size
            bytes_per_chunk = 5000*1024*1024
            chunks_count    = int(math.ceil(source_size / float(bytes_per_chunk)))

            for i in range(chunks_count):
                offset          = i * bytes_per_chunk
                remaining_bytes = source_size - offset
                bytes           = min([bytes_per_chunk, remaining_bytes])
                part_num        = i + 1

                self.lg("S3 Uploading(" + str(cur_filename) + ") part " + str(part_num) + " of " + str(chunks_count), 6)

                with open(cur_csv_file, 'r') as fp:
                    fp.seek(offset)
                    mp.upload_part_from_file(fp=fp, part_num=part_num, size=bytes)
            # end of writing multipart files
            
            record["Size"]      = str(source_size)

            if len(mp.get_all_parts()) == chunks_count:
                mp.complete_upload()
                results         = self.build_def_hash("SUCCESS", "", record)
            else:
                mp.cancel_upload()
                results         = self.build_def_hash("Display Error", "Failed to Upload", record)

            if delete_when_done:
                if os.path.exists(cur_filename):
                    os.system("rm -f " + str(cur_filename))

                if os.path.exists(cur_csv_file):
                    os.system("rm -f " + str(cur_csv_file))

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to Upload CSV Data to S3 with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of s3_upload_csv_dataset


    def s3_upload_file(self, req, debug=False):

        record              = {
                                "File"  : "",
                                "Size"  : "0"
                            }

        results             = self.build_def_hash("Display Error", "Not Run", record)

        try:

            cur_keys        = self.aws_get_keys(debug)

            import boto, math
            import boto.s3

            """
            req             = {
                                "SaveToFile"    : <path to file>,
                                "S3Loc"         : <bucket>:<key>,
                                "DeleteAfter"   : boolean
                            }
            """

            s3_split        = str(req["S3Loc"]).split(":")
            s3_bucket       = str(s3_split[0])
            s3_key          = str(s3_split[1])

            savepath        = str(req["SaveToFile"])
            delete_after    = False
            if "DeleteAfter" in req:
                delete_after= bool(req["DeleteAfter"])

            conn_s3         = boto.connect_s3(cur_keys["Key"], cur_keys["Secret"])
            bucket          = conn_s3.get_bucket(s3_bucket, validate=False)
            filename        = os.path.basename(savepath)
            k               = bucket.new_key(s3_key)
            mp              = bucket.initiate_multipart_upload(filename)
            source_size     = os.stat(savepath).st_size
            bytes_per_chunk = 5000*1024*1024
            chunks_count    = int(math.ceil(source_size / float(bytes_per_chunk)))

            for i in range(chunks_count):
                offset      = i * bytes_per_chunk
                remaining_bytes = source_size - offset
                bytes       = min([bytes_per_chunk, remaining_bytes])
                part_num    = i + 1

                self.lg("S3 Uploading(" + str(filename) + ") part " + str(part_num) + " of " + str(chunks_count), 6)

                with open(savepath, 'r') as fp:
                    fp.seek(offset)
                    mp.upload_part_from_file(fp=fp, part_num=part_num, size=bytes)
            # end of writing multipart files
            
            record["Size"]  = str(source_size)

            if len(mp.get_all_parts()) == chunks_count:
                mp.complete_upload()
                results     = self.build_def_hash("SUCCESS", "", record)
            else:
                mp.cancel_upload()
                results     = self.build_def_hash("Display Error", "Failed to Upload", record)

            if delete_after:
                if os.path.exists(savepath):
                    os.system("rm -f " + str(savepath))

                if os.path.exists(savepath):
                    os.system("rm -f " + str(savepath))

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to Upload File(" + str(json.dumps(req)) + ") to S3 with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of s3_upload_file


    def s3_calculate_bucket_size(self, bucket_name, debug=False):
        
        record          = {
                            "Size"     : 0,
                            "SizeMB"   : 0.0,
                            "SizeGB"   : 0.0,
                            "Files"    : 0 
                        }    

        results         = self.build_def_hash("Display Error", "Not Run", record)

        try:
            import boto, math
            import boto.s3

            cur_keys        = self.aws_get_keys(debug)
            conn_s3         = boto.connect_s3(cur_keys["Key"], cur_keys["Secret"])
            bucket          = conn_s3.get_bucket(bucket_name, validate=False)
            total_bytes     = 0
            for key in bucket:
                record["Size"]  += int(key.size)
                record["Files"] += 1
            # end for all keys

            record["SizeMB"]    = float(self.to_float_str(float(float(record["Size"]) / 1024.0 / 1024.0)))
            record["SizeGB"]    = float(self.to_float_str(float(float(record["SizeMB"]) / 1024.0)))
        
            results             = self.build_def_hash("SUCCESS", "", record)
        except Exception,w:
            self.lg("Failed to Process S3 Bucket(" + str(bucket_name) + ") Size Ex(" + str(w) + ")", 0)
            results         = self.build_def_hash("Display Error", "Not Run", record)

        return results
    # end of s3_calculate_bucket_size


    def s3_download_file(self, s3_bucket, s3_key, rds, dbs, debug=False):

        record      = {
                        "Contents"  : ""
                    }
                
        results     = self.build_def_hash("Display Error", "Not Run", record)

        try:

            if s3_bucket and s3_key:
                record["Contents"]  = s3_key.get_contents_as_string()
                results             = self.build_def_hash("SUCCESS", "", record)
            else:
                err_msg             = "Missing valid S3 Bucket and Key"
                self.lg("ERROR: " + str(err_msg), 0)
                results             = self.build_def_hash("Display Error", err_msg, record)
            # end of if/else

        except Exception,w:
            err_msg         = "Failed to Download File from S3 with Ex(" + str(w) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, record)

        return results
    # end of s3_download_file


    def s3_download_and_store_file(self, s3_loc, local_file, rds, dbs, debug):
        
        record      = {
                        "Contents"  : "",
                        "File"      : ""
                    }
                
        results     = self.build_def_hash("Display Error", "Not Run", record)

        try:

            import boto, math
            import boto.s3

            s3_split        = s3_loc.split(":")
            s3_bucket_name  = s3_split[0]
            s3_key_name     = s3_split[1]

            cur_keys        = self.aws_get_keys(debug)
            conn_s3         = boto.connect_s3(cur_keys["Key"], cur_keys["Secret"])

            s3_bucket       = conn_s3.get_bucket(s3_bucket_name, validate=False)
            s3_key          = s3_bucket.get_key(s3_key_name, validate=False)

            self.lg("Downloading S3Loc(" + str(s3_bucket_name) + ":" + str(s3_key_name) + ")", 6)
            key_results     = self.s3_download_file(s3_bucket, s3_key, rds, dbs, debug)

            self.lg("Done Downloading S3Loc(" + str(s3_bucket_name) + ":" + str(s3_key_name) + ") Writing to File(" + str(local_file) + ") Bytes(" + str(len(str(key_results["Record"]["Contents"]))) + ")", 6)

            if len(key_results["Record"]["Contents"]) > 0:
                with open(local_file, "w") as output_file:
                    output_file.write(str(key_results["Record"]["Contents"]))
                # end of writing the contents
            else:
                self.lg(" - No data in S3 file", 6)

            if os.path.exists(local_file) == False:
                err_msg = "Failed to Download S3Loc(" + str(s3_bucket_name) + ":" + str(s3_key_name) + ")"
                return self.handle_display_error(err_msg, record, True)
            else:
                self.lg("Created Local File(" + str(local_file) + ")", 6)

                record["Contents"]      = key_results["Record"]["Contents"]
                record["File"]          = local_file
                
                results                 = self.build_def_hash("SUCCESS", "", record)
            # end of if created local file from s3 location

        except Exception,k:
            err_msg = "Failed to download S3Loc(" + str(s3_loc) + ") with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of s3_download_and_store_file

    
    #####################################################################################################
    #
    # Machine Learning Helper Methods
    #
    #####################################################################################################


    def ml_get_adjusted_current_time_for_deployment(self, debug=False):
        cur_time        = datetime.datetime.now() - datetime.timedelta(hours=0)
        if self.m_env.lower().lstrip().strip() == "local":
            cur_time    = datetime.datetime.now()

        return cur_time
    # end of ml_get_adjusted_current_time_for_deployment


    def ml_convert_models_to_objects(self, req, rds, dbs, debug=False):

        record                  = {
                                    "Errors"    : [],
                                    "Models"    : []
                                }
            
        results                 = self.build_def_hash("Display Error", "Failed to Get Convert Models to Objects", record )

        try:
            
            models              = []
            errors              = []

            self.lg("Converting Models(" + str(len(req["Models"])) + ") to Objects", 6)

            for idx,node in enumerate(req["Models"]):

                model_class_name    = node["Type"]
                model_version       = node["Version"]
                model_target        = node["Target"]
                model_feature_names = node["FeatureNames"]
                model_obj           = node["Model"]
                model_id            = node["ID"]

                self.lg("Model(" + str(idx) + ") Type(" + str(model_class_name) + ") Target(" + str(model_target) + ") Version(" + str(model_version) + ") ID(" + str(model_id) + ")", 6)

                new_model_node      = {
                                        "Type"          : model_class_name,
                                        "Version"       : model_version,
                                        "Target"        : model_target,
                                        "FeatureNames"  : model_feature_names,
                                        "Model"         : model_obj,
                                        "ID"            : model_id
                                    }

                models.append(new_model_node)
            # end of for all modesl

            record["Errors"]    = errors
            record["Models"]    = models
        
            self.lg("Converted(" + str(len(record["Models"])) + ") Errors(" + str(len(record["Errors"])) + ")", 6)

            results             = self.build_def_hash("SUCCESS", "", record )

        except Exception,k:
            err_msg = "Failed to Convert Models into Objects with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of ml_convert_models_to_objects


    def ml_load_model_file_into_cache(self, req, rds, dbs, debug=False):

        record                  = {
                                }
            
        results                 = self.build_def_hash("Display Error", "Failed to Load Model file into Cache", record )

        try:

            import pickle, cPickle, zlib

            ra_name             = "CACHE"
            ra_key              = ""

            dataset_name        = ""
            dataset_name        = self.to_upper(str(req["DSName"]))
            s3_bucket           = str(req["S3Loc"].split(":")[0])
            s3_key              = str(req["S3Loc"].split(":")[1])
            model_file          = str(req["ModelFile"])
            tracking_type       = "UseTargetColAndUnits"
            if "TrackingType" in req:
                tracking_type   = str(req["TrackingType"])

            lg("Loading DSName(" + str(dataset_name) + ") ModelFile(" + str(model_file) + ")", 6)

            if os.path.exists(model_file) == False:
                err_msg = "Failed to Find ModelFile(" + str(model_file) + ")"
                return self.handle_display_error(err_msg, record, True)

            model_stream        = cPickle.loads(zlib.decompress(open(model_file).read()))

            if len(model_stream) == 0:
                err_msg = "Decompressed ModelFile(" + str(model_file) + ") is Empty"
                return self.handle_display_error(err_msg, record, True)

            self.lg("Model File Decompressed Records(" + str(len(model_stream)) + ")", 6)

            if debug:
                for k in model_stream:
                    print k
            # serialization debugging

            if len(model_stream) > 0:

                self.lg("Creating Analysis Dataset", 6)

                analysis_dataset    = {
                                        "DSName"            : str(dataset_name),
                                        "CreationDate"      : str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")),
                                        "PredictionsDF"     : None,
                                        "AccuracyResults"   : {},
                                        "Models"            : [],
                                        "Manifest"          : {},
                                        "MLAlgo"            : {},
                                        "Tracking"          : {},
                                        "TrackingType"      : str(tracking_type),
                                        "Version"           : 1
                                    }

                if "CreationDate" in model_stream:
                    analysis_dataset["CreationDate"]    = model_stream["CreationDate"]
                if "Models" in model_stream:
                    analysis_dataset["Models"]          = model_stream["Models"]
                if "CacheVersion" in model_stream:
                    analysis_dataset["Version"]         = model_stream["CacheVersion"]
                if "Manifest" in model_stream:
                    analysis_dataset["Manifest"]        = model_stream["Manifest"]
                if "PredictionsDF" in model_stream:
                    analysis_dataset["PredictionsDF"]   = model_stream["PredictionsDF"]
                if "Accuracy" in model_stream:
                    analysis_dataset["AccuracyResults"] = model_stream["Accuracy"]
                if "MLAlgo" in model_stream:
                    analysis_dataset["MLAlgo"]          = model_stream["MLAlgo"]
                if "Tracking" in model_stream:
                    analysis_dataset["Tracking"]        = model_stream["Tracking"]

                tracking_data       = self.ml_build_tracking_id(analysis_dataset, rds, dbs, debug)

                if "Tracking" in model_stream:
                    tracking_data.update(model_stream["Tracking"])

                tracking_id         = str(tracking_data["TrackingID"])
                ra_name             = tracking_data["RLoc"].split(":")[0]
                ra_key              = tracking_data["RLoc"].split(":")[1]

                analysis_dataset["Tracking"] = tracking_data
            
                cache_req           = {
                                        "Name"          : ra_name,
                                        "Key"           : ra_key,
                                        "TrackingID"    : tracking_id,
                                        "Analysis"      : analysis_dataset,
                                        "ValidateDates" : False
                                    }
                cache_results       = self.ml_cache_analysis_and_models(cache_req, rds, dbs, debug)
            # end of valid stream

            results             = self.build_def_hash("SUCCESS", "", record )

        except Exception,k:
            err_msg = "Failed to Load Model File into Cache with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of ml_load_model_file_into_cache


    def ml_build_tracking_id(self, req, rds, dbs, debug=False):

        tracking_node           = {
                                    "TrackingID"        : "",
                                    "Start"             : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "End"               : "",
                                    "TrackingVersion"   : 1,
                                    "TrackingType"      : "",
                                    "TrackingName"      : "",
                                    "RLoc"              : "",
                                    "Data"              : {}
                                }
        
        tracking_version        = 1
        tracking_type           = "UseTargetColAndUnits"
        tracking_id             = ""
        tracking_name           = tracking_id
        ra_name                 = "CACHE"
        ra_key                  = ""

        if "TrackingType" in req:
            tracking_type       = str(req["TrackingType"])

        if str(tracking_type) == "UseTargetColAndUnits":

            if "Tracking" in req:
                tracking_id         = "_MD_" + str(req["Tracking"]["TrackingName"])
                tracking_name       = "_MD_" + str(req["Tracking"]["TrackingName"])
                ra_key              = "_MODELS_" + str(req["Tracking"]["TrackingName"]) + "_LATEST"

            else:
                if "TrackingName" in req:
                    tracking_id         = "_MD_" + str(req["TrackingName"])
                    tracking_name       = "_MD_" + str(req["TrackingName"])
                    ra_key              = "_MODELS_" + str(req["TrackingName"]) + "_LATEST"
                
        if "MLAlgo" in req: # tracking nodes should support passing the parent ml json api through
            
            data_node                       = {}
            if len(req["MLAlgo"]) > 0:
                for key in req:
                    data_node[key]          = req[key]
                # allow for pruning here

            tracking_node["Data"]           = data_node
        # end of passing the org algo through

        if tracking_name == "":
            lg("", 6)
            lg("Debugging help:", 6)
            for k in req:
                lg("  Key(" + str(k) + ")", 0)
            lg("", 6)
            raise Exception("Failed ml_build_tracking_id - Please confirm the TrackingName is set correctly")

        if tracking_id == "":
            lg("", 6)
            lg("Debugging help:", 6)
            for k in req:
                lg("  Key(" + str(k) + ")", 0)
            lg("", 6)
            raise Exception("Failed ml_build_tracking_id - Please confirm the TrackingID is set correctly")

        tracking_node["TrackingID"]         = tracking_id
        tracking_node["TrackingVersion"]    = tracking_version
        tracking_node["TrackingType"]       = tracking_type
        tracking_node["TrackingName"]       = tracking_name
        tracking_node["RLoc"]               = str(ra_name) + ":" + str(ra_key)

        return tracking_node
    # end of ml_build_tracking_id


    def ml_upload_cached_dataset_to_s3(self, req, rds, dbs, debug=False):
        
        record                  = {
                                    "Errors"    : [],
                                    "Models"    : []
                                }
            
        results                 = self.build_def_hash("Display Error", "Failed to Upload Cached Dataset to S3", record )

        try:

            import pickle, cPickle, zlib

            compress_data       = True
            dataset_name        = self.to_upper(str(req["DSName"]))
            s3_bucket           = str(req["S3Loc"].split(":")[0])
            s3_key              = str(req["S3Loc"].split(":")[1])

            delete_after        = False
            if "DeleteAfter" in req:
                delete_after    = bool(req["DeleteAfter"])

            image_base_dir      = str(os.getenv("ENV_DATA_SRC_DIR", "/opt/work/data/dst"))
            if "SaveDir" in req:
                image_base_dir  = str(req["SaveDir"])

            if not os.path.exists(image_base_dir):
                err_msg = "Unable to export because the SaveDir(" + str(image_base_dir) + ") does not exist. Please create it and retry."
                return self.handle_display_error(err_msg, record, True)

            tmp_file            = image_base_dir + "/" + s3_key
            ra_name             = "CACHE"
            ra_key              = ""
            if "RLoc" in req:
                ra_name         = str(req["RLoc"]).split(":")[0]
                ra_key          = str(req["RLoc"]).split(":")[1]

            model_req           = {
                                    "DSName"        : dataset_name,
                                    "TrackingID"    : "",
                                    "RAName"        : ra_name,
                                    "ReturnPickle"  : True
                                }
            
            self.lg("Getting Latest Analysis and Models for DSName(" + str(dataset_name) + ")", 6)

            analysis_rec        = self.ml_get_models_for_request(model_req, rds, dbs, debug)
            if len(analysis_rec["Record"]) > 0:
                if "CreationDate" in analysis_rec["Record"]:

                    lg("Found DSName(" + str(dataset_name) + ") Analysis Created on Date(" + str(analysis_rec["Record"]["CreationDate"]) + ") Creating File(" + str(tmp_file) + ")", 6)

                    with open(tmp_file, "w") as output_file:
                        output_file.write(zlib.compress(cPickle.dumps(analysis_rec["Record"])))

                    lg("Validating Serialization", 6)
                    validate_bytes      = open(tmp_file).read()
                    decompressed_obj    = cPickle.loads(zlib.decompress(validate_bytes))

                    lg("Checking Model Counts", 6)
                    if len(decompressed_obj["Models"]) != len(analysis_rec["Record"]["Models"]):
                        err_msg = "Analysis Dataset found Incorrect Number of Models(" + str(len(decompressed_obj["Models"])) + ") != (" + str(len(analysis_rec["Record"]["Models"])) + ") Please confirm the cache is up to date"
                        return self.handle_display_error(err_msg, record, True)
                    else:
                        lg("Decompression Validation Passed - Models(" + str(len(decompressed_obj["Models"])) + ") == (" + str(len(analysis_rec["Record"]["Models"])) + ")", 5)

                    lg("Done Creating File(" + str(tmp_file) + ")", 6)

                    s3_loc          = str(s3_bucket) + ":" + str(s3_key)
                    lg("Uploading to DSName(" + str(dataset_name) + ") Analysis to S3(" + str(s3_loc) + ")", 6)

                    req             = {
                                        "SaveToFile"    : tmp_file,
                                        "S3Loc"         : s3_loc,
                                        "DeleteAfter"   : delete_after
                                    }

                    upload_results  = self.s3_upload_file(req, debug)

                    if upload_results["Status"] != "SUCCESS":
                        lg("ERROR: Failed to upload S3 DSName(" + str(dataset_name) + ") new S3 File(" + str(s3_key) + ") Bucket(" + str(s3_bucket) + ") Compressed(" + str(compress_data) + ") Error(" + str(upload_results["Error"]) + ")", 0)
                    else:
                        lg("Uploaded DSName(" + str(dataset_name) + ") S3(" + str(s3_bucket) + ":" + str(s3_key) + ")", 5)
                    # end of uploading Dataset Name snapshot
		    
                    lg("Done Uploading to S3(" + str(s3_bucket) + ":" + str(s3_key) + ")", 6)
                else:
                    err_msg = "Analysis Dataset is missing CreationDate"
                    return self.handle_display_error(err_msg, record, True)
            else:
                err_msg = "Failed to find Model Cache for DSName(" + str(dataset_name) + ")"
                return self.handle_display_error(err_msg, record, True)

            results             = self.build_def_hash("SUCCESS", "", record )

        except Exception,k:
            err_msg = "Failed to Upload Cached Analysis Dataset to S3 with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of ml_upload_cached_dataset_to_s3


    def ml_get_single_model_from_cache(self, cached_model_node, rds, dbs, debug=False):
            
        import zlib
        import pickle
        import cPickle

        model_node                  = {
                                        "Type"          : "",
                                        "Version"       : "",
                                        "Target"        : "",
                                        "FeatureNames"  : "",
                                        "Model"         : "",
                                        "ID"            : -1
                                    }
        
        lg("Getting Single Model", 6)

        model_ra_name               = cached_model_node["RAName"]
        model_cache_key             = cached_model_node["RAKey"]
        model_cache_suffix_key      = ""

        tracking_data               = {}
        algo_data                   = {}
        tracking_id                 = -1
        tracking_type               = ""
        tracking_version            = 1

        if "AlgoTracking" in cached_model_node:
            tracking_data           = cached_model_node["AlgoTracking"]
            tracking_id             = tracking_data["TrackingID"]
            tracking_type           = tracking_data["TrackingType"]
            tracking_version        = tracking_data["TrackingVersion"]
            tracking_rloc           = str(tracking_data["RLoc"]).split(":")
            algo_data               = tracking_data["Data"]

        if "ModelRAKeySuffix" in cached_model_node:
            model_cache_suffix_key  = str(cached_model_node["ModelRAKeySuffix"])

        if tracking_type == "UseTargetColAndUnits":
            model_ra_name           = str(tracking_rloc[0])
            model_cache_key         = str(tracking_id) + "_" + str(model_cache_suffix_key)
                    
        lg("Getting Model RLoc(" + str(model_ra_name) + ":" + str(model_cache_key) + ")", 6)

        compressed_model_rec        = self.get_cache_from_redis(rds[model_ra_name], model_cache_key, False, False)
        if debug:
            lg("Checking compressed records(" + str(len(compressed_model_rec["Record"])) + ")", 6)

        if len(compressed_model_rec["Record"]) > 0:
            model_class_name        = compressed_model_rec["Record"]["Type"]
            model_version           = compressed_model_rec["Record"]["Version"]
            model_id                = compressed_model_rec["Record"]["ID"]
            model_target            = compressed_model_rec["Record"]["Target"]
            model_feature_names     = compressed_model_rec["Record"]["FeatureNames"]
            model_obj               = cPickle.loads(zlib.decompress(compressed_model_rec["Record"]["CompressedModel"]))

            model_node              = {
                                            "Type"              : model_class_name,
                                            "Version"           : model_version,
                                            "Target"            : model_target,
                                            "FeatureNames"      : model_feature_names,
                                            "Model"             : model_obj,
                                            "MLAlgo"            : algo_data,
                                            "Tracking"          : tracking_data,
                                            "ModelRAKeySuffix"  : model_cache_suffix_key,
                                            "ID"                : model_id
                                    }
                
            lg("Found Model(" + str(model_node["ID"]) + ") Type(" + str(model_node["Type"]) + ") Target(" + str(model_target) + ") FeatureNames(" + str(len(model_feature_names)) + ")", 6)
        # end of found

        return model_node
    # end of ml_get_single_model_from_cache

    
    def ml_get_models_for_request(self, req, rds, dbs, debug=False):

        record                  = {
                                }
            
        results                 = self.build_def_hash("Display Error", "Failed to Get Models for Request", record )

        try:
            
            import zlib
            import pickle
            import cPickle

            dataset_name        = req["DSName"]
            track_id            = req["TrackingID"]
            ra_name             = req["RAName"]
            ret_pickle_obj      = False
            if "ReturnPickle" in req:
                ret_pickle_obj  = True

            cache_key           = "_MODELS_" + str(dataset_name) + "_LATEST"

            manifest_cache_rec  = self.get_cache_from_redis(rds[ra_name], cache_key, False, False)

            if len(manifest_cache_rec["Record"]) > 0:

                # Take out of cache with: cPickle.loads(zlib.decompress(cPickle.loads( cache_record )["Pickle"]))
                cache_records                       = {}

                cache_records["CompressedSize"]     = manifest_cache_rec["Record"]["CompressedSize"]
                cache_records["DecompressedSize"]   = manifest_cache_rec["Record"]["DecompressedSize"]
                cache_records["CreationDate"]       = manifest_cache_rec["Record"]["CreationDate"]
                cache_records["Compression"]        = manifest_cache_rec["Record"]["Compression"]
                cache_records["CacheVersion"]       = manifest_cache_rec["Record"]["CacheVersion"]
                cache_records["Manifest"]           = manifest_cache_rec["Record"]["Manifest"]
                cache_records["Tracking"]           = manifest_cache_rec["Record"]["Tracking"]
                cache_records["Analysis"]           = {}

                self.lg("Decompressing Cached Record Size(" + str(cache_records["CompressedSize"]) + ") DecompressedSize(" + str(cache_records["DecompressedSize"]) + ")", 6)
                cache_records["Models"]             = []

                lg("Decompressing Analysis Dataset", 6)
                for manifest_key in manifest_cache_rec["Record"]["Manifest"]:
                    if      str(manifest_key).lower() != "models" \
                        and str(manifest_key).lower() != "date":

                        ra_name                     = manifest_cache_rec["Record"]["Manifest"][manifest_key][0]["RAName"]
                        ra_cache_key                = manifest_cache_rec["Record"]["Manifest"][manifest_key][0]["RAKey"]

                        lg("Finding ManifestKey(" + str(manifest_key) + ") Records in RLoc(" + str(ra_name) + ":" + str(ra_cache_key) + ")", 6)
                        current_comp_cache          = self.get_cache_from_redis(rds[ra_name], ra_cache_key, False, False)
                        if len(current_comp_cache["Record"]) > 0:
                            lg("Decompressing Key(" + str(manifest_key) + ")", 6)
                            cache_records[manifest_key] = cPickle.loads(zlib.decompress(current_comp_cache["Record"]["Pickle"]))
                            lg("Done Decompressing Key(" + str(manifest_key) + ")", 6)
                        else:
                            lg("ERROR: Failing Finding ManifestKey(" + str(manifest_key) + ") Records in RLoc(" + str(ra_name) + ":" + str(ra_cache_key) + ")", 0)
                # end of for all manifest

                lg("Done Decompressing Analysis Dataset", 6)
                
                self.lg("Decompressing Models(" + str(len(manifest_cache_rec["Record"]["Manifest"]["Models"])) + ")", 6)
                for cached_model_node in manifest_cache_rec["Record"]["Manifest"]["Models"]:

                    model_node      = self.ml_get_single_model_from_cache(cached_model_node, rds, dbs, debug)

                    if model_node["ID"] != -1:
                        cache_records["Models"].append(model_node)
                    else:
                        lg("ERROR: Failed to find a Model in Cache RLoc(" + str(ra_name) + ":" + str(model_node) + ")", 0)

                # end of pruning model objs

                if len(cache_records["PredictionsDF"].index) > 0:
                    lg("Sorting Predictions", 6)
                    cache_records["PredictionsDF"].sort_values(by="Date", ascending=True, inplace=True)

                lg("Done Decompressing Models(" + str(len(cache_records["Models"])) + ")", 6)

                results                             = self.build_def_hash("SUCCESS", "", cache_records )

            else:
                err_msg = "Failed to Get Models in RLoc(" + str(ra_name) + ":" + str(cache_key) + ") Req(" + str(json.dumps(req)) + ")"
                return self.handle_display_error(err_msg, record, True)
 
        except Exception,k:
            err_msg = "Failed to Get Models for Req(" + str(json.dumps(req)) + ") with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of ml_get_models_for_request

    
    def ml_cache_analysis_and_models(self, req, rds, dbs, debug):

        record                      = {
                                        "Locs" : []
                                    }
        results                     = self.build_def_hash("Display Error", "Not Run", record)

        try:

            import zlib
            import pickle
            import cPickle

            self.lg("Caching Analysis and Models(" + str(len(req["Analysis"]["Models"])) + ")", 6)
            
            tracking_node                   = req["Analysis"]["Tracking"]
            tracking_type                   = tracking_node["TrackingType"]
            tracking_id                     = tracking_node["TrackingID"]
            tracking_version                = tracking_node["TrackingVersion"]
            tracking_data                   = tracking_node["Data"]
            tracking_rloc                   = str(tracking_node["RLoc"]).split(":")
            ra_name                         = str(tracking_rloc[0])
            cache_key                       = str(tracking_rloc[1])
            run_date_validation             = True
            if "ValidateDates" in req:
                run_date_validation         = bool(req["ValidateDates"])
            cache_record                    = {
                                                "Date"              : str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                                "Models"            : [],
                                                "Accuracy"          : [],
                                                "PredictionsDF"     : []
                                            }
            accuracy_cache_key              = tracking_id + "_" + "Accuracy"
            predictionsdf_cache_key         = tracking_id + "_" + "PredictionsDF"
            
            accuracy_manifest               = [
                                                {
                                                    "RAName"    : ra_name,
                                                    "RAKey"     : accuracy_cache_key
                                                }
                                            ]
            predictions_df_manifest         = [
                                                {
                                                    "RAName"    : ra_name,
                                                    "RAKey"     : predictionsdf_cache_key
                                                }
                                            ]

            if "Manifest" in req["Analysis"]:
                manifest_node               = req["Analysis"]["Manifest"]
                accuracy_manifest           = manifest_node["Accuracy"]
                predictions_df_manifest     = manifest_node["PredictionsDF"]
            # end of passing the manifests from a file or previous cache back in for a quick data refresh

            lg("Compressing Models(" + str(len(req["Analysis"]["Models"])) + ")", 6)
            compressed_models               = []
            num_done                        = 0
            num_left                        = len(req["Analysis"]["Models"])
            total_model_size                = 0
            compressed_model_size           = 0
            decompressed_model_size         = 0

            for m in req["Analysis"]["Models"]:
                model_class_name            = str(m["Model"].__class__.__name__)
                lg("Compressing Model(" + str(num_done) + "/" + str(num_left) + ") Type(" + str(model_class_name) + ")", 6)
                model_version               = "1"             # should use git commit hash for deserializing on correct code
                pickled_model               = cPickle.dumps(m["Model"])
                compress_model              = zlib.compress(pickled_model)
                compressed_model_size       += len(compress_model)       
                decompressed_model_size     += len(pickled_model)       
                model_cache_rec             = {
                                                "Name"              : ra_name,
                                                "Key"               : m["ID"],
                                                "ID"                : m["ID"],
                                                "Target"            : m["Target"],
                                                "FeatureNames"      : m["FeatureNames"],
                                                "AlgoTracking"      : tracking_node,
                                                "ModelRAKeySuffix"  : m["Target"],
                                                "Type"              : model_class_name,
                                                "Version"           : model_version,
                                                "CompressedModel"   : compress_model,
                                                "CompressedSize"    : len(compress_model),
                                                "DecompressedSize"  : len(pickled_model)
                                            }
                lg("Done Compressing(" + str(num_done) + "/" + str(num_left) + ") Type(" + str(model_class_name) + ") Size(" + str(model_cache_rec["CompressedSize"]) + ") Decompressed(" + str(model_cache_rec["DecompressedSize"]) + ")", 6)
                total_model_size            += int(model_cache_rec["CompressedSize"])
            
                model_cache_key             = str(m["ID"])
                model_cache_key             = str(req["TrackingID"]) + "_" + str(num_done) # Allow these to stomp to prevent overrunning the memory

                if tracking_type == "UseTargetColAndUnits":
                    model_cache_key         = tracking_id + "_" + str(model_cache_rec["ModelRAKeySuffix"])

                lg("Caching Model(" + str(num_done) + ") ID(" + str(m["ID"]) + ") RLoc(" + str(ra_name) + ":" + str(model_cache_key) + ")", 6)
                self.purge_and_cache_records_in_redis(rds[ra_name],
                                            model_cache_key,
                                            model_cache_rec,
                                            False)
                lg("Done Caching Model(" + str(num_done) + ") ID(" + str(m["ID"]) + ") RLoc(" + str(ra_name) + ":" + str(cache_key) + ")", 6)
                new_manifest_node           = {
                                                "Type"              : model_class_name,
                                                "Version"           : model_version,
                                                "RAName"            : ra_name,
                                                "RAKey"             : model_cache_key,
                                                "Target"            : m["Target"],
                                                "AlgoTracking"      : tracking_node,
                                                "ModelRAKeySuffix"  : str(model_cache_rec["ModelRAKeySuffix"]),
                                                "FeatureNames"      : m["FeatureNames"],
                                                "ID"                : str(m["ID"])
                                            }
                cache_record["Models"].append(new_manifest_node)

                num_done                    += 1
            # end for all models to compress

            self.lg("Preprocessing Accuracy Results", 6)

            no_models                       = {}

            for key_name in req["Analysis"]["AccuracyResults"]:
                cur_node                    = {}
                for acc_res_key in req["Analysis"]["AccuracyResults"][key_name]:

                    # Ignore these as they just increase the cache size 
                    if "model" != str(acc_res_key).lower() \
                        and "sourcedf" != str(acc_res_key).lower() \
                        and "predictions" != str(acc_res_key).lower() \
                        and "predictionsdf" != str(acc_res_key).lower() \
                        and "confusionmatrix" != str(acc_res_key).lower():

                        self.lg("Adding Acc(" + str(key_name) + "-" + str(acc_res_key) + ")", 6)
                        cur_node[acc_res_key]   = req["Analysis"]["AccuracyResults"][key_name][acc_res_key]
                # end of for each sub key name

                no_models[key_name]         = cur_node
            # end of pruning model objs

            cache_record["Accuracy"]        = accuracy_manifest
            cache_record["PredictionsDF"]   = predictions_df_manifest

            lg("Caching AccuracyResults RLoc(" + str(ra_name) + ":" + str(accuracy_cache_key) + ")", 6)
            self.purge_and_cache_records_in_redis(rds[ra_name],
                                                  accuracy_cache_key,
                                                  { "Pickle" : zlib.compress(cPickle.dumps(no_models)) },
                                                  False)
            lg("Done Caching AccuracyResults", 6)

            lg("Caching PredictionsDF RLoc(" + str(ra_name) + ":" + str(predictionsdf_cache_key) + ")", 6)
            self.purge_and_cache_records_in_redis(rds[ra_name],
                                                  predictionsdf_cache_key,
                                                  { "Pickle" : zlib.compress(cPickle.dumps(req["Analysis"]["PredictionsDF"])) },
                                                  False)
            lg("Done Caching PredictionsDF", 6)

            total_compressed_size           = 0.0
            total_compressed_size           += float(compressed_model_size)


            self.lg("Building Compressed Cache Record", 6)
            creation_date                   = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            compressed_cache_record         = {
                                                "CreationDate"      : creation_date,
                                                "Compression"       : "zlib",
                                                "CacheVersion"      : 1,
                                                "CompressedSize"    : compressed_model_size,
                                                "DecompressedSize"  : decompressed_model_size,
                                                "Tracking"          : tracking_node,
                                                "Manifest"          : cache_record
                                            }
            self.purge_and_cache_records_in_redis(rds[ra_name],
                                            cache_key,
                                            compressed_cache_record,
                                            False)

            self.lg("Validating Cache Works", 6)
            # Take out of cache with: cPickle.loads(zlib.decompress(cPickle.loads( cache_record )["Pickle"]))
            validate_req                    = {
                                                "DSName"        : str(req["Analysis"]["DSName"]),
                                                "TrackingID"    : "",
                                                "RAName"        : "CACHE"
                                            }
            validate_records                = self.ml_get_models_for_request(validate_req, rds, dbs, debug)
            if len(validate_records["Record"]) > 0:
                if validate_records["Record"]["CreationDate"] == creation_date:

                    if len(validate_records["Record"]["Models"]) == len(cache_record["Models"]):
                        self.lg("Validated Compressed Cache Records with Models(" + str(len(validate_records["Record"]["Models"])) + ")", 6)
                        if debug:
                            lg("Validated Compressed Cache Records with Models(" + str(len(validate_records["Record"]["Models"])) + ")", 5)
                            print validate_records["Record"]["Models"][0]["Model"]
                    else:
                        err_msg     = "Failed to validate Compressed Cache Record Models(" + str(len(validate_records["Record"]["Models"])) + ") != Models(" + str(len(cache_record["Models"])) + ")"
                        return self.handle_display_error(err_msg, record, True)
                else:

                    if run_date_validation:
                        err_msg         = "Failed to validate Compressed Cache Record Date(" + str(validate_records["Record"]["CreationDate"]) + ") != CreationDate(" + str(creation_date) + ")"
                        return self.handle_display_error(err_msg, record, True)
            # end of validation of compressed cache

            self.lg("Done Caching Analysis and Models(" + str(len(cache_record["Models"])) + ") RLoc(" + str(ra_name) + ":" + str(cache_key) + ")", 6)

            results                 = self.build_def_hash("SUCCESS", "", record)

        except Exception,k:
            err_msg         = "Unable to Cache Analysis and Models with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of ml_cache_analysis_and_models


    def ml_cache_model(self, req, rds, dbs, debug):

        record                      = {
                                        "RALoc"     : "",
                                        "Pickle"    : "",
                                        "Type"      : "",
                                        "Version"   : "1"
                                    }
        results                     = self.build_def_hash("Display Error", "Not Run", record)

        try:

            import pickle

            ra_name                 = req["Name"]
            ra_key                  = req["Key"]
            model_type              = req["Type"]
            version                 = req["Version"]

            self.lg("Pickling", 6)
            pickle_str              = pickle.dumps(req["Model"])
            
            record["RLoc"]         = str(ra_name) + ":" + str(ra_key)
            self.lg("Storing Pickle Len(" + str(len(pickle_str)) + ") in RLoc(" + str(record["RLoc"]) + ")", 6)

            cache_record            = {
                                        "Pickle"    : str(pickle_str),
                                        "Type"      : str(model_type),
                                        "Version"   : version
                                    }

            self.purge_and_cache_records_in_redis(rds[ra_name],
                                            ra_key,
                                            cache_record,
                                            False)

            self.lg("Done", 6)
            record.update(cache_record)

            results                 = self.build_def_hash("SUCCESS", "", record)

        except Exception,k:
            err_msg         = "Unable to Cache Model with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of ml_cache_model


    def ml_encode_target_column(self, df, target_column, result_column, debug=False):
        
	import pandas as pd

        success = False
        
        if result_column in df:
            lg("Already Have Column(" + str(result_column) + ")", 6)
	    return (success, df, [])

	# Add column to df with integers for the target.

        # make a copy of the df
	df_mod  = df.copy()

        # find the uniques in the target column
	targets     = df_mod[target_column].unique()

        # convert to a dict of names to int values
	map_to_int  = {name: n for n, name in enumerate(targets)}

        # replace the result column with the correct integer values
	df_mod[result_column] = df_mod[target_column].replace(map_to_int)

        success     = True
    
	return (success, df_mod, targets)
    # end of ml_encode_target_column

    
    def ml_is_valid_classifier_request(self, req):

        status      = "Failed Validation"
        err_msg     = ""
        record      = {}
        
        if "TargetColumnName" not in req:
            err_msg = "Classifier Error - Missing required 'TargetColumnName' parameter. Please set it to the name of the column you want the machine to learn."
        # end of TargetColumnName

        if "TrainFeatureNames" not in req:
            err_msg = "Classifier Error - Missing required 'TrainFeatureNames' parameter. Please set it to a list of feature names you want to be trained in the model."
        # end of TargetColumnName

        if "FeaturesTrain" not in req:
            err_msg = "Classifier Error - Missing required 'FeaturesTrain' parameter. Please set it to the features_train result from: features_train, features_test, target_train, target_test = train_test_split(features, train_df[target_col], test_size=test_ratio)."
        # end of FeaturesTrain

        if "FeaturesTest" not in req:
            err_msg = "Classifier Error - Missing required 'FeaturesTest' parameter. Please set it to the features_test result from: features_train, features_test, target_train, target_test = train_test_split(features, train_df[target_col], test_size=test_ratio)."
        # end of FeaturesTest

        if "TargetTrain" not in req:
            err_msg = "Classifier Error - Missing required 'TargetTrain' parameter. Please set it to the target_train result from: features_train, features_test, target_train, target_test = train_test_split(features, train_df[target_col], test_size=test_ratio)."
        # end of TargetTrain

        if "TargetTest" not in req:
            err_msg = "Classifier Error - Missing required 'TargetTest' parameter. Please set it to the target_test result from: features_train, features_test, target_train, target_test = train_test_split(features, train_df[target_col], test_size=test_ratio)."
        # end of TargetTest

        if "MLType" not in req:
            err_msg = "Classifier Error - Missing required 'MLType' parameter. Please set it to a name."
        # end of MLType
        
        if "MLAlgo" not in req:
            err_msg = "Classifier Error - Missing required 'MLAlgo' parameter. Please set it to a dictionary for building the Machine Learning Algorithm."
        # end of MLAlgo

        if "Name" not in req["MLAlgo"]:
            err_msg = "Classifier Error - Missing required 'Name' parameter under 'MLAlgo'. Please set it to a name for the algorithm object."
        # end of MLAlgo.Name

        if "Steps" not in req["MLAlgo"]:
            err_msg = "Classifier Error - Missing required 'Steps' parameter under 'MLAlgo'. Please set it to a dictionary for the algorithm to run."
        # end of MLAlgo.Steps

        if err_msg == "":
            status  = "SUCCESS"

        return self.build_def_hash(status, err_msg, record)
    # end of ml_is_valid_classifier_request


    def ml_is_valid_regression_request(self, req):

        status      = "Failed Validation"
        err_msg     = ""
        record      = {}
        
        if "TargetColumnName" not in req:
            err_msg = "Regressor Error - Missing required 'TargetColumnName' parameter. Please set it to the name of the column you want the machine to learn."
        # end of TargetColumnName

        if "TrainFeatureNames" not in req:
            err_msg = "Regressor Error - Missing required 'TrainFeatureNames' parameter. Please set it to a list of feature names you want to be trained in the model."
        # end of TargetColumnName

        if "FeaturesTrain" not in req:
            err_msg = "Regressor Error - Missing required 'FeaturesTrain' parameter. Please set it to the features_train result from: features_train, features_test, target_train, target_test = train_test_split(features, train_df[target_col], test_size=test_ratio)."
        # end of FeaturesTrain

        if "FeaturesTest" not in req:
            err_msg = "Regressor Error - Missing required 'FeaturesTest' parameter. Please set it to the features_test result from: features_train, features_test, target_train, target_test = train_test_split(features, train_df[target_col], test_size=test_ratio)."
        # end of FeaturesTest

        if "TargetTrain" not in req:
            err_msg = "Regressor Error - Missing required 'TargetTrain' parameter. Please set it to the target_train result from: features_train, features_test, target_train, target_test = train_test_split(features, train_df[target_col], test_size=test_ratio)."
        # end of TargetTrain

        if "TargetTest" not in req:
            err_msg = "Regressor Error - Missing required 'TargetTest' parameter. Please set it to the target_test result from: features_train, features_test, target_train, target_test = train_test_split(features, train_df[target_col], test_size=test_ratio)."
        # end of TargetTest

        if "MLType" not in req:
            err_msg = "Regressor Error - Missing required 'MLType' parameter. Please set it to a name."
        # end of MLType
        
        if "MLAlgo" not in req:
            err_msg = "Regressor Error - Missing required 'MLAlgo' parameter. Please set it to a dictionary for building the Machine Learning Algorithm."
        # end of MLAlgo

        if "Name" not in req["MLAlgo"]:
            err_msg = "Regressor Error - Missing required 'Name' parameter under 'MLAlgo'. Please set it to a name for the algorithm object."
        # end of MLAlgo.Name

        if "Steps" not in req["MLAlgo"]:
            err_msg = "Regressor Error - Missing required 'Steps' parameter under 'MLAlgo'. Please set it to a dictionary for the algorithm to run."
        # end of MLAlgo.Steps

        if err_msg == "":
            status  = "SUCCESS"

        return self.build_def_hash(status, err_msg, record)
    # end of ml_is_valid_regression_request


    def ml_is_valid_train_and_test_set(self, ml_request):

        import pandas as pd
        import numpy as np
        
        err_msg     = ""

        if len(ml_request["FeaturesTrain"].values) != len(ml_request["TargetTrain"].values):
            err_msg = "Confirm the variables are correct: FeaturesTrain(" + str(len(ml_request["FeaturesTrain"].values)) + ") has a different row count than TargetTrain(" + str(len(ml_request["TargetTrain"])) + ")"

        if len(ml_request["FeaturesTest"].values) != len(ml_request["TargetTest"].values):
            err_msg = "Confirm the variables are correct: FeaturesTest(" + str(len(ml_request["FeaturesTest"].values)) + ") has a different row count than TargetTest(" + str(len(ml_request["TargetTest"])) + ")"

        if len(ml_request["FeaturesTest"].values) == 0:
            err_msg = "No Data to Process for: FeaturesTest(" + str(len(ml_request["FeaturesTest"].values)) + ")"
        
        if len(ml_request["TargetTest"].values) == 0:
            err_msg = "No Data to Process for: FeaturesTest(" + str(len(ml_request["FeaturesTest"].values)) + ")"

        if len(ml_request["TrainFeatureNames"]) == 0:
            err_msg = "No Data to Process for: TrainFeatureNames(" + str(len(ml_request["TrainFeatureNames"])) + ")"

        return err_msg
    # end of ml_is_valid_train_and_test_set


    def ml_build_req_node(self, req):

        ml_type                         = str(req["MLType"])
        ml_algo_name                    = str(req["MLAlgo"]["Name"])
        target_column_name              = str(req["TargetColumnName"])
        target_column_values            = req["TargetColumnValues"]
        ignore_features                 = req["IgnoreFeatures"]
        ml_dataset_name                 = ""
        algo_meta_data                  = {}
        train_api_node                  = {}
        cross_val_api_node              = {}
        fit_api_node                    = {}
        predict_api_node                = {}
        predictproba_api_node           = {}
        plot_api_node                   = {}
        cache_api_node                  = {}
        post_proc_api_node              = {}

        debug                           = False
        max_features                    = 10
        
        if "Meta" in req["MLAlgo"]:
            if len(req["MLAlgo"]["Meta"]) > 0:
                algo_meta_data          = req["MLAlgo"]["Meta"]
        
        if "MaxFeatures" in req["MLAlgo"]:
            max_features                = int(req["MaxFeatures"])

        if "Steps" in req["MLAlgo"]:
            algo_meta_data              = req["MLAlgo"]["Steps"]

        if "Train" in algo_meta_data:
            if len(algo_meta_data["Train"]) > 0:
                train_api_node          = algo_meta_data["Train"]
        # end of processing Train api
        
        if "CrossValidation" in algo_meta_data:
            if len(algo_meta_data["CrossValidation"]) > 0:
                cross_val_api_node      = algo_meta_data["CrossValidation"]
        # end of processing CrossValidation api
        
        if "Fit" in algo_meta_data:
            if len(algo_meta_data["Fit"]) > 0:
                fit_api_node            = algo_meta_data["Fit"]
        # end of processing Fit api
        
        if "Predict" in algo_meta_data:
            if len(algo_meta_data["Predict"]) > 0:
                predict_api_node        = algo_meta_data["Predict"]
        # end of processing Predict api
        
        if "PredictProba" in algo_meta_data:
            if len(algo_meta_data["PredictProba"]) > 0:
                predictproba_api_node   = algo_meta_data["PredictProba"]
        # end of processing PredictProba api
        
        if "Cache" in req["MLAlgo"]:
            if len(req["MLAlgo"]["Cache"]) > 0:
                cache_api_node          = req["MLAlgo"]["Cache"]
        # end of processing Cache api
        
        if "Plot" in req["MLAlgo"]:
            if len(req["MLAlgo"]["Plot"]) > 0:
                plot_api_node           = req["MLAlgo"]["Plot"]
        # end of processing Plot api
        
        if "PostProcessing" in algo_meta_data:
            if len(algo_meta_data["PostProcessing"]) > 0:
                post_proc_api_node      = algo_meta_data["PostProcessing"]
        # end of processing PostProcessing api
        
        if "Debug" in req:
            debug                       = bool(req["Debug"])

        record  = {
                    "MLType"    : str(ml_type),
                    "MLAlgo"    : {
                        "Name"      : str(ml_algo_name),
                        "TTRatio"   : 0.1,
                        "Meta"      : {
                            "DSName"    : str(ml_dataset_name),
                            "Src"       : { # Where's the data coming from?
                                "CSVFile"       : "",
                                "S3File"        : "",
                                "RedisKey"      : "" # <App Name>:<Key>
                            },
                            "Dst"       : { # Want to do something after processing?
                                "Emails"        : [],
                                "S3Key"         : "",
                                "S3Bucket"      : ""
                            },
                            "IgnoreFeatures"          : [ # What feature columns should be removed? (strings/dates)
                            ],
                            "TargetColumnValues"      : [ # What do the target values logically represent?
                            ],
                            "TargetPredictionMapping" : { # What did the target predict?
                            },
                            "TargetResultMapping"     : { # Was the target prediction correct?
                            },
                            "SampleMask" : None
                        },
                        "Steps"     : {
                            "MaxFeatures"       : int(max_features),
                            "Train"             : { "Debug" : False },
                            "CrossValidation"   : { "Debug" : False },
                            "Fit"               : { "Debug" : False },
                            "Predict"           : { "Debug" : False },
                            "PredictProba"      : { "Debug" : False },
                            "Plot"              : { "Debug" : False }
                        },
                        "Cache"     : {
                            "RLoc"      : "CACHE:_MODELS_" + str(req["TrackingName"]) + "_LATEST",
                            "UseCaches" : False
                        }
                    },
                    "UnitsAheadSet" : "",
                    "UnitsAheadType": "",
                    "PredictionType": "",
                    "TrackingName"  : "",
                    "TrackingID"    : "ML_" + str(self.build_unique_key())
                }

        # XGB Regressor Implementation
        if ml_algo_name == "xgb-regressor":
            record["MLAlgo"]["Steps"]["Train"]  = {
                                "LearningRate"          : 0.1,
                                "NumEstimators"         : 1000,
                                "Objective"             : "reg:linear",
                                "MaxDepth"              : 3,
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
            } # end of train

            record["MLAlgo"]["Steps"]["CrossValidation"]= {
                                "Metrics"               : "auc",
                                "NumBoostRounds"        : 20,
                                "NumFolds"              : 10,
                                "Stratified"            : False,
                                "Seed"                  : 0,
                                "EarlyStoppingRounds"   : "",
                                "ShowProgress"          : True,
                                "Debug"                 : False
            } # end of cross validation

            record["MLAlgo"]["Steps"]["Fit"]            = {
                                "SampleWeight"          : "",
                                "EvalSet"               : "",
                                "EvalMetric"            : "",
                                "EarlyStoppingRounds"   : "",
                                "Debug"                 : False
            } # end of fit

            record["MLAlgo"]["Steps"]["Predict"]        = {
                                "OutputMargin"          : False,
                                "NumTreeLimit"          : 0
            } # end of predict

            record["MLAlgo"]["Steps"]["PredictProba"]   = {
                                "OutputMargin"          : False,
                                "NumTreeLimit"          : 0
            } # end of proba

            record["MLAlgo"]["Steps"]["Plot"]           = {
                                "ShowPlot"      : False,
                                "PlotType"      : "seaborn",
                                "PlotTitle"     : "Scipype Plot",
                                "YAxisTitle"    : "Actual",
                                "XAxisTitle"    : "Predictions",
                                "XLabel"        : "Dates",
                                "YLabel"        : "Values",
                                "Width"         : 15.0,
                                "Height"        : 15.0,
                                "MaxFeatures"   : 7,
                                "Debug"         : False
            } # end of plot

            record["TargetColumnName"]      = target_column_name
            record["TargetColumnValues"]    = target_column_values
            record["IgnoreFeatures"]        = ignore_features
            record["TrainFeatureNames"]     = []
            record["FeaturesTrain"]         = None
            record["FeaturesTest"]          = None
            record["TargetTrain"]           = None
            record["TargetTest"]            = None
            record["Debug"]                 = debug

        # end of XGB Regressor Implementation
        elif ml_algo_name == "xgb-classifier":
            record["MLAlgo"]["Steps"]["Train"]  = {
                                "LearningRate"          : 0.1,
                                "NumEstimators"         : 1000,
                                "Objective"             : "reg:linear",
                                "MaxDepth"              : 3,
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
            } # end of train

            record["MLAlgo"]["Steps"]["CrossValidation"]= {
                                "Metrics"               : "auc",
                                "NumBoostRounds"        : 20,
                                "NumFolds"              : 10,
                                "Stratified"            : False,
                                "Seed"                  : 0,
                                "EarlyStoppingRounds"   : "",
                                "ShowProgress"          : True,
                                "Debug"                 : False
            } # end of cross validation

            record["MLAlgo"]["Steps"]["Fit"]            = {
                                "SampleWeight"          : "",
                                "EvalSet"               : "",
                                "EvalMetric"            : "",
                                "EarlyStoppingRounds"   : "",
                                "Debug"                 : False
            } # end of fit

            record["MLAlgo"]["Steps"]["Predict"]        = {
                                "OutputMargin"          : False,
                                "NumTreeLimit"          : 0
            } # end of predict

            record["MLAlgo"]["Steps"]["PredictProba"]   = {
                                "OutputMargin"          : False,
                                "NumTreeLimit"          : 0
            } # end of proba

            record["MLAlgo"]["Steps"]["Plot"]           = {
                                "ShowPlot"      : False,
                                "PlotType"      : "seaborn",
                                "PlotTitle"     : "Scipype Plot",
                                "YAxisTitle"    : "Actual",
                                "XAxisTitle"    : "Predictions",
                                "XLabel"        : "Dates",
                                "YLabel"        : "Values",
                                "Width"         : 15.0,
                                "Height"        : 15.0,
                                "MaxFeatures"   : 7,
                                "Debug"         : False
            } # end of plot

            record["TargetColumnName"]      = target_column_name
            record["TargetColumnValues"]    = target_column_values
            record["IgnoreFeatures"]        = ignore_features
            record["TrainFeatureNames"]     = []
            record["FeaturesTrain"]         = None
            record["FeaturesTest"]          = None
            record["TargetTrain"]           = None
            record["TargetTest"]            = None
            record["Debug"]                 = debug

        # end of XGB Classifier Implementation

        record["MLAlgo"]["Steps"]["Train"].update(train_api_node)
        record["MLAlgo"]["Steps"]["CrossValidation"].update(cross_val_api_node)
        record["MLAlgo"]["Steps"]["Fit"].update(fit_api_node)
        record["MLAlgo"]["Steps"]["Predict"].update(predict_api_node)
        record["MLAlgo"]["Steps"]["PredictProba"].update(predictproba_api_node)
        record["MLAlgo"]["Steps"]["Plot"].update(plot_api_node)
        record["MLAlgo"]["Cache"].update(cache_api_node)
        
        record["TrackingName"]              = str(req["TrackingName"])
        record["TrackingID"]                = str(req["TrackingID"])
        record["TrackingType"]              = str(req["TrackingType"])
        record["UnitsAheadSet"]             = str(req["UnitsAheadSet"])
        record["UnitsAheadType"]            = str(req["UnitsAheadType"])
        record["PredictionType"]            = str(req["PredictionType"])

        if "Meta" in req["MLAlgo"]:
            record["MLAlgo"]["Meta"].update(req["MLAlgo"]["Meta"])

        return record
    # end of ml_build_req_node


    def ml_build_res_node(self, ml_req):

        now                     = datetime.datetime.now()
        record  = {
                    "FeatureNames"      : [],
                    "TargetColumnName"  : "",
                    "Rankings"          : [],
                    "Accuracy"          : 0.0,
                    "AUROC"             : 0.0,
                    "ConfusionMatrix"   : None,
                    "CVResults"         : None,
                    "PredictionsDF"     : None,
                    "ProbaPredsDF"      : None,
                    "PredictionAPI"     : None,
                    "ProbaPredAPI"      : None,
                    "Predictions"       : None,
                    "ProbaPreds"        : None,
                    "SourceDF"          : None,
                    "Model"             : None,
                    "SampleMask"        : None,
                    "PredictionMask"    : None,
                    "UnitsAheadSet"     : "",
                    "UnitsAheadType"    : "",
                    "PredictionType"    : "",
                    "MLAlgoName"        : "", 
                    "Meta"              : {},
                    "Tracking"  : {
                        "Start" : now.strftime("%Y-%m-%d %H:%M:%S"),
                        "End"   : ""
                    }
                }

        # Attach custom dictionary by setting it to the Request's "ResponseMeta" value
        if "ResponseMeta" in ml_req:
            record["Meta"]      = ml_req["ResponseMeta"]

        return record
    # end of ml_build_res_node
    
    
    def ml_compile_analysis_dataset(self, req, rds, dbs, debug=False):
       

        analysis_version        = int(req["Version"])
        accuracy_results        = req["AccuracyResults"]
        prediction_markers      = req["PredictionMarkers"]
        ds_name                 = str(req["DSName"])
        track_id                = str(req["Tracking"]["TrackingID"])
        
        # Add meta data as needed to the analysis dataset
        meta_data               = {}
        if "Analysis" in req:
            if "Meta" in req:
                meta_data       = req["Analysis"]["Meta"]

        self.lg("Generating Analysis Dataset Version(" + str(analysis_version) + ") Name(" + str(ds_name) + ")", 6)

        pk_show_plot        = False
        test_show_plot      = str(os.getenv("ENV_SHOW_PLOT", "0"))
        if str(test_show_plot) == "1":
            pk_show_plot    = True
        
        import pandas as pd
        
        self.lg("Creating Predictions DF", 6)
        predictions_df          = pd.DataFrame(prediction_markers)
        predictions_df["Date"]  = pd.to_datetime(predictions_df["Date"], format='%Y-%m-%d %H:%M:%S')
        self.lg("Done Creating Predictions DF", 6)

        # Add custom analysis actions here

        now                     = datetime.datetime.now()
        just_today              = str(now.strftime("%Y-%m-%d"))
        image_base_dir          = str(os.getenv("ENV_DATA_SRC_DIR", "/opt/work/data/dst"))
        if os.path.exists(image_base_dir) == False:
            image_base_dir      = "/opt/work/data/dst"

        forecast_image_file     = "forecast_"  + ds_name + ".png"
        scatter_image_file      = "scatter_"   + ds_name + ".png"
        pairplot_image_file     = "pairplot_"  + ds_name + ".png"
        jointplot_image_file    = "jointplot_" + ds_name + ".png"
        confmatrix_image_file   = "confusionmatrix_" + ds_name + ".png"
        featimp_image_file      = "featimp_" + ds_name + ".png"

        path_to_image_forecast  = image_base_dir + "/" + str(forecast_image_file)
        path_to_image_scatter   = image_base_dir + "/" + str(scatter_image_file)
        path_to_image_pairplot  = image_base_dir + "/" + str(pairplot_image_file)
        path_to_image_jointplot = image_base_dir + "/" + str(jointplot_image_file)
        path_to_image_cmatrix   = image_base_dir + "/" + str(confmatrix_image_file)
        path_to_image_featimp   = image_base_dir + "/" + str(featimp_image_file)

        models                  = []
        confusion_matrices      = []
        model_id                = self.build_unique_key(6)

        for node_idx,key_name in enumerate(accuracy_results):

            res_node            = accuracy_results[key_name]
            if "Model" in res_node:
                model           = res_node["Model"]
                model_name      = track_id + "_" + model_id + "_" + str(node_idx)
                new_model       = {
                                    "ID"            : model_name,
                                    "Target"        : key_name,
                                    "FeatureNames"  : res_node["FeatureNames"],
                                    "Model"         : model
                                }
                models.append(new_model)
        # end for all nodes

        analysis_dataset                        = {}
        analysis_dataset["DSName"]              = str(ds_name)
        analysis_dataset["CreationDate"]        = str(now.strftime("%Y-%m-%d-%H-%M-%S"))
        analysis_dataset["PredictionsDF"]       = predictions_df
        analysis_dataset["AccuracyResults"]     = accuracy_results
        analysis_dataset["Models"]              = models
        analysis_dataset["Version"]             = analysis_version
        analysis_dataset["ShowPlot"]            = pk_show_plot
        analysis_dataset["ForecastImgFile"]     = path_to_image_forecast
        analysis_dataset["ScatterImgFile"]      = path_to_image_scatter
        analysis_dataset["PairPlotImgFile"]     = path_to_image_pairplot
        analysis_dataset["JointPlotImgFile"]    = path_to_image_jointplot
        analysis_dataset["CMatrixImgFile"]      = path_to_image_cmatrix
        analysis_dataset["FeatImpImgFile"]      = path_to_image_featimp
        analysis_dataset["Tracking"]            = req["Tracking"]
        analysis_dataset["UnitsAheadSet"]       = req["MLAlgo"]["UnitsAheadSet"]
        analysis_dataset["UnitsAheadType"]      = req["MLAlgo"]["UnitsAheadType"]
        analysis_dataset["PredictionType"]      = req["MLAlgo"]["PredictionType"]
        analysis_dataset["FeatureColumnNames"]  = req["FeatureColumnNames"]
        analysis_dataset["TargetColumnName"]    = req["TargetColumnName"]
        analysis_dataset["TargetColumnValues"]  = req["TargetColumnValues"]
        analysis_dataset["IgnoreFeatures"]      = req["IgnoreFeatures"]
        analysis_dataset["ConfMatrices"]        = req["ConfMatrices"]
        analysis_dataset["Meta"]                = meta_data # your custom meta data goes in here for inclusion in the s3 objects

        self.lg("Built Analysis Dataset for Request(" + str(track_id) + ") Models(" + str(len(analysis_dataset["Models"])) + ")", 6)

        return analysis_dataset
    # end of ml_compile_analysis_dataset

    
    def ml_load_csv_dataset(self, req, rds, dbs, debug=False):
        
        record          = {
                            "SourceDF"              : None,
                            "AllFeatures"           : [],
                            "TrainAndTestFeatures"  : [],
                            "TrainFeatures"         : []
                        }
        results         = self.build_def_hash("Display Error", "Not Run", record)

        try:

            load_csv_req        = {
                                    "MLType"                : req["MLType"],
                                    "TargetColumnName"      : req["TargetColumnName"],   # What column is getting processed
                                    "IgnoreFeatures"        : req["IgnoreFeatures"],     # Prune non-int/float columns as needed: 
                                    "CSVFile"               : req["MLAlgo"]["Meta"]["Source"]["CSVFile"]
                                }

            lg("Loading CSV(" + str(load_csv_req["CSVFile"]) + ")", 6)

            csv_load_results    = self.sk_load_csv(load_csv_req, rds, dbs)

            if csv_load_results["Status"] != "SUCCESS":
                err_msg         = "Failed to Load CSV(" + str(load_csv_req["CSVFile"]) + ") with Error(" + str(load_csv_req["Error"]) + ")"
                lg("ERROR: " + str(err_msg), 0)
                print err_msg
                return self.build_def_hash("Display Error", err_msg, record)

            record              = csv_load_results["Record"]
            
            results             = self.build_def_hash("SUCCESS", "", record)

        except Exception,k:
            err_msg = "Failed Loading CSV Dataset(" + str(req["MLAlgo"]["Meta"]["Source"]["CSVFile"]) + ") with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of processing results

        return results
    # end of ml_load_csv_dataset


    def ml_process_forecast(self, ml_request, rds, dbs, debug=False):

        record                      = {
                                    }
        last_step                   = ""
        results                     = self.build_def_hash("Display Error", "Not Run", record)

        try:

            last_step               = "Compiling"
            units_ahead_set         = ml_request["UnitsAheadSet"]
            units_ahead_type        = ml_request["UnitsAheadType"]
            feature_column_names    = ml_request["FeatureColumnNames"]
            prediction_type         = ml_request["PredictionType"]

            today                   = datetime.datetime.now().date()
            future_prediction_dates = self.ml_return_prediction_dates(today, units_ahead_set, units_ahead_type, rds, dbs, debug)

            if debug:
                lg("Future Dates: " + str(future_prediction_dates) + ")", 6)

            compile_results         = self.ml_compile_forecast_results(units_ahead_set, feature_column_names, ml_request, rds, dbs, debug)
            source_df               = None
            confusion_matrices      = []
            prediction_markers      = []
            num_algos_done          = 0
            max_algos               = len(feature_column_names) * len(units_ahead_set)
            stop_processing         = False
            accuracy_results        = {}
            unit_done_idx           = 0
            cur_units_ahead         = 5

            if compile_results["Status"] != "SUCCESS":
                lg("ERROR: Failed to build Algo Forecasts with Error(" + str(compile_results["Error"]) + ")", 0)
                stop_processing     = True
            else:
                last_step           = "Adding Algo Results"
                algo_nodes          = compile_results["Record"]["AlgoNodes"]


                self.lg("Algos Done(" + str(num_algos_done) + "/" + str(max_algos) + ") Compiled Results(" + str(len(algo_nodes)) + ")", 6)
                lg("Algos Done(" + str(num_algos_done) + "/" + str(max_algos) + ") Compiled Results(" + str(len(algo_nodes)) + ")", 6)
                last_step           = "Walking through AlgoNodes(" + str(len(algo_nodes)) + ")"
                for units_ahead in algo_nodes:

                    invalid_node        = True
                    forecast_node       = {
                                        }

                    last_step           = "UnitIdx(" + str(unit_done_idx) + ") Walking through Targets(" + str(len(feature_column_names)) + ")"
                    unit_done_idx       += 1
                    for cur_target_col_name in feature_column_names:

                        if cur_target_col_name not in units_ahead:
                            lg("ERROR: Missing TargetColumnName(" + str(cur_target_col_name) + ") from Forecast Results", 0)
                            break
                        if units_ahead[cur_target_col_name] == None:
                            lg("ERROR: Invalid TrackingName(" + str(ml_request["TrackingName"]) + ") TargetColumnName(" + str(cur_target_col_name) + ") from Forecast Results", 0)
                            break

                        invalid_node    = False

                        forecast_node[cur_target_col_name]    = {}

                        node_req        = units_ahead[cur_target_col_name]["Request"]
                        node_res        = units_ahead[cur_target_col_name]["Response"]

                        if num_algos_done == 0:
                            feature_names = node_res["FeatureNames"]
                            source_df   = node_res["SourceDF"]

                        ml_model        = node_res["Model"]
                        predictions     = node_res["Predictions"]
                        predictions_df  = node_res["PredictionsDF"]
                        probapreds_df   = node_res["ProbaPredsDF"]
                        rankings        = node_res["Rankings"]

                        algo_name       = str(node_req["MLAlgo"]["Name"])
                        cur_units_ahead = int(node_req["MLAlgo"]["Meta"]["UnitsAhead"])
                        
                        acc_key         = cur_target_col_name + "_" + str(cur_units_ahead)

                        if "ConfusionMatrix" in node_res:
                            if node_res["ConfusionMatrix"] is not None:
                                confusion_matrices.append({
                                            "ID"                : int(num_algos_done),
                                            "TargetColumnName"  : cur_target_col_name,
                                            "UnitsAhead"        : cur_units_ahead,
                                            "AccuracyKey"       : acc_key,
                                            "CM"                : node_res["ConfusionMatrix"]
                                        })

                        accuracy_results[acc_key]   = node_res

                        if debug: 
                            print ""
                            print "Algo(" + str(num_algos_done + 1) + "/" + str(max_algos) + ") Name(" + str(algo_name) + ") UnitsAhead(" + str(cur_units_ahead) + "-" + str(cur_target_col_name) + ")"
                            print ""
                            num_algos_done      += 1

                        last_step               = "Building New Prediction with Model"
                        prediction_node         = self.ml_build_newest_prediction_with_model(node_res)

                        if prediction_node["PredictionValue"] != None:
                            source_date         = prediction_node["Date"]
                            prediction_date     = prediction_node["PredictionDate"]
                            prediction_value    = prediction_node["PredictionValue"]

                            forecast_node["PredictionDate"]     = prediction_date
                            forecast_node[cur_target_col_name]  = prediction_value

                            if debug:
                                print "Processed Date(" + str(source_date) + ") Predicting(" + str(prediction_date) + ") => " + str(prediction_value)
                    # end of each target column

                    last_step           = "Checking for valid Node"

                    #######################################################################
                    #
                    # V3 Feature:
                    #
                    # Eventually this should be using an object passed in that creates the 
                    # nodes in a class method and returns them here.
                    # For now the core is coupled to how prediction nodes are built
                    if not invalid_node:

                        last_step               = "Building Prediction Node"
                        supported_forecast      = True

                        if ml_request["ForecastType"] == "ReplacedDictKeys":

                            prediction_node     = {}
                            for req_key in ml_request["ForecastDict"]:
                                req_value       = ml_request["ForecastDict"][req_key]
                                if req_key in new_data_node:
                                    prediction_node[req_value]  = new_data_node[req_key]

                                else:
                                    # handle common ones like date columns that do not get renamed
                                    if "Date" == req_key:
                                        prediction_node["Date"] = future_prediction_dates[str(cur_units_ahead)]
                            # end of processing dict
                        # end of ReplacedDictKeys
                        elif ml_request["ForecastType"] == "CustomDefined":
                            lg("Add support for your own custom Forecast here", 5)
                        # end of CustomDefined
                        else:
                            lg("ERROR: Unsupported ForecastType(" + str(ml_request["ForecastType"]) + ") - Please use a supported ForecastType", 0)
                            supported_forecast      = False
                        # end of handling forecasts

                        if supported_forecast:
                            prediction_markers.append(prediction_node)
                    # end of invalid_node detection
                # end for units_ahead in algo_nodes
            # if results to process

            record["StoppedEarly"]          = stop_processing
            record["AccuracyResults"]       = accuracy_results
            record["ConfMatrices"]          = confusion_matrices
            record["PredictionMarkers"]     = prediction_markers
            record["AnalysisVersion"]       = 1
            record["SourceDF"]              = source_df
            record["MLAlgo"]                = ml_request

            tracking_data                   = self.ml_build_tracking_id(ml_request, rds, dbs, debug)
            if "Tracking" in ml_request:
                tracking_data.update(ml_request["Tracking"])

            record["Tracking"]              = tracking_data

            results                         = self.build_def_hash("SUCCESS", "", record)

        except Exception,k:

            err_msg = "Failed Processing ML Forecast(" + str(ml_request["MLAlgo"]["Name"]) + ") LastStep(" + str(last_step) + ") Version(" + str(ml_request["Version"]) + ") with Ex(" + str(k) + ")"

            if "TrackingName" in ml_request:
                err_msg = "Failed Processing ML Forecast(" + str(ml_request["MLAlgo"]["Name"]) + ") Tracking(" + str(ml_request["TrackingName"]) + ") LastStep(" + str(last_step) + ") Version(" + str(ml_request["Version"]) + ") with Ex(" + str(k) + ")"

            return self.handle_display_error(err_msg, record, True)
        # end of processing results

        return results
    # end of ml_process_forecast


    def ml_compile_forecast_results(self, units_ahead_set, target_columns, ml_base_request, rds, dbs, debug=False):

        record                      = {
                                        "AlgoNodes" : []
                                    }
        results                     = self.build_def_hash("Display Error", "Not Run", record)

        try:

            units_ahead_type        = ml_base_request["UnitsAheadType"]

            self.lg("Compiling Forecast for " + str(units_ahead_type) + "(" + str(len(units_ahead_set)) + ")", 6)

            cur_done                = 0
            total_done              = len(units_ahead_set) * len(target_columns)

            for units_ahead in units_ahead_set:

                units_node          = {
                                        "PredictedDate" : None
                                    }
                for col_name in target_columns:
                    units_node[col_name]   = None

                for col_name in target_columns:

                    if debug:
                        self.lg("", 6)
                    
                    self.lg("Processing(" + str(cur_done) + "/" + str(total_done) + ") Algo(" + str(units_ahead) + "-" + str(col_name) + ")", 6)
                    lg("Processing(" + str(cur_done) + "/" + str(total_done) + ") Algo(" + str(units_ahead) + "-" + str(col_name) + ")", 6)
                
                    ml_req                                  = self.ml_build_req_node(ml_base_request)
                    ml_req["TargetColumnName"]              = col_name
                    ml_req["MLAlgo"]["Cache"]["ModelID"]    = str(cur_done)
                    
                    cur_done                                += 1
                    
                    # Customize as needed:
                    ml_req["MLAlgo"]["Meta"]["UnitsAhead"]  = int(units_ahead)

                    # For this run:
                    algo_node               = {
                                                "Request"   : ml_req,
                                                "Response"  : {}
                                            }

                    if bool(ml_req["MLAlgo"]["Cache"]["UseCaches"]):
                        if ml_req["TrackingType"] == "UseTargetColAndUnits":
                            ml_req["ModelCache"]    = {
                                                        "RLoc"  : "CACHE:_MD_" + str(ml_req["TrackingName"]) + "_" + str(ml_req["TargetColumnName"])
                                                    }
                    # end of appending cache support

                    algo_results            = self.ml_run_algo(ml_req, rds, dbs)

                    lg("Done Processing(" + str(cur_done) + "/" + str(total_done) + ") Algo(" + str(units_ahead) + "-" + str(col_name) + ")", 6)

                    if algo_results["Status"] == "SUCCESS":
                        if algo_results["Record"]["Model"] != None:
                            algo_node["Response"]   = algo_results["Record"]
                            units_node[col_name]    = algo_node
                        else:
                            err_msg = "Compile Forecast - Failed to find a valid Model for ML(" + str(ml_req["MLType"]) + ") Algo(" + str(ml_req["MLAlgo"]["Name"]) + ")"
                            lg("ERROR: " + str(err_msg), 0)
                    else:
                        err_msg     = "Compile Forecast - Failed to run ML(" + str(ml_req["MLType"]) + ") Algo(" + str(ml_req["MLAlgo"]["Name"]) + ") with Error(" + str(algo_results["Error"]) + ")"
                        lg("ERROR: " + str(err_msg), 0)
                # end of building the current target col
                
                record["AlgoNodes"].append(units_node)
            # end of processing each algo

            results         = self.build_def_hash("SUCCESS", "", record)

        except Exception,k:
            err_msg         = "Unable to Compile Forecast Results for Algos with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of ml_compile_forecast_results


    def ml_train_models_for_predictions(self, ml_request, rds, dbs, debug=False):

        record                      = {
                                        "StoppedEarly"      : "Not Run",
                                        "AnalysisVersion"   : 1,
                                        "AccuracyResults"   : {},
                                        "MLAlgo"            : ml_request,
                                        "SourceDF"          : None,
                                        "AlgoNodes"         : [],
                                        "Tracking"          : {}
                                    }
        last_step                   = ""
        results                     = self.build_def_hash("Display Error", "Not Run", record)

        try:

            last_step               = "Compiling"
            units_ahead_set         = ml_request["UnitsAheadSet"]
            units_ahead_type        = ml_request["UnitsAheadType"]
            feature_column_names    = ml_request["FeatureColumnNames"]
            prediction_type         = ml_request["PredictionType"]

            today                   = datetime.datetime.now().date()

            compile_results         = self.ml_build_models_for_predictions(feature_column_names, ml_request, rds, dbs, debug)
            source_df               = None
            num_algos_done          = 0
            max_algos               = len(feature_column_names) * len(units_ahead_set)
            stop_processing         = False
            accuracy_results        = {}
            cur_units_ahead         = 0
            algo_nodes              = [] 

            if compile_results["Status"] != "SUCCESS":
                lg("ERROR: TM - Failed to build Algo Forecasts with Error(" + str(compile_results["Error"]) + ")", 0)
                stop_processing     = True
            else:
                last_step           = "Adding Algo Results"
                initial_nodes       = compile_results["Record"]["AlgoNodes"]

                self.lg("TM - Algos Done(" + str(num_algos_done) + "/" + str(max_algos) + ") Compiled Results(" + str(len(initial_nodes)) + ")", 6)
                lg("TM - Algos Done(" + str(num_algos_done) + "/" + str(max_algos) + ") Compiled Results(" + str(len(initial_nodes)) + ")", 6)
                last_step           = "Walking through AlgoNodes(" + str(len(initial_nodes)) + ")"
                for cur_node in initial_nodes:

                    invalid_node        = True

                    last_step           = "Algo(" + str(num_algos_done) + ") Walking through Node(" + str(cur_node["TargetColumn"]) + ")"

                    for cur_target_col_name in feature_column_names:

                        if cur_node["TargetColumn"] == cur_target_col_name:

                            new_node        = cur_node["Algo"]
                            node_req        = new_node["Request"]
                            node_res        = new_node["Response"]

                            if num_algos_done == 0:
                                feature_names = node_res["FeatureNames"]
                                source_df   = node_res["SourceDF"]

                            ml_model        = node_res["Model"]
                            predictions     = node_res["Predictions"]
                            predictions_df  = node_res["PredictionsDF"]
                            probapreds_df   = node_res["ProbaPredsDF"]
                            rankings        = node_res["Rankings"]
                            algo_name       = str(node_req["MLAlgo"]["Name"])
                            cur_units_ahead = int(node_req["MLAlgo"]["Meta"]["UnitsAhead"])

                            acc_key         = cur_target_col_name

                            accuracy_results[acc_key]               = node_res
                            accuracy_results[acc_key]["SourceDF"]   = None

                            new_node["Response"]["SourceDF"]        = None
                            algo_nodes.append(new_node)

                            if debug: 
                                print ""
                                print "TM - Algo(" + str(num_algos_done + 1) + "/" + str(max_algos) + ") Name(" + str(algo_name) + ") UnitsAhead(" + str(cur_units_ahead) + "-" + str(cur_target_col_name) + ")"
                                print ""

                            num_algos_done      += 1
                    # end of each target column
                # end for units_ahead in initial_nodes
            # if results to process

            record["StoppedEarly"]          = stop_processing
            record["AccuracyResults"]       = accuracy_results
            record["AnalysisVersion"]       = 1
            record["SourceDF"]              = source_df

            record["AlgoNodes"]             = algo_nodes
            record["MLAlgo"]                = ml_request

            tracking_data                   = self.ml_build_tracking_id(ml_request, rds, dbs, debug)
            if "Tracking" in ml_request:
                tracking_data.update(ml_request["Tracking"])

            record["Tracking"]              = tracking_data

            results                         = self.build_def_hash("SUCCESS", "", record)

        except Exception,k:

            err_msg = "Failed Processing ML Forecast(" + str(ml_request["MLAlgo"]["Name"]) + ") LastStep(" + str(last_step) + ") Version(" + str(ml_request["Version"]) + ") with Ex(" + str(k) + ")"

            if "TrackingName" in ml_request:
                err_msg = "Failed Processing ML Forecast(" + str(ml_request["MLAlgo"]["Name"]) + ") Tracking(" + str(ml_request["TrackingName"]) + ") LastStep(" + str(last_step) + ") Version(" + str(ml_request["Version"]) + ") with Ex(" + str(k) + ")"

            return self.handle_display_error(err_msg, record, True)
        # end of processing results

        return results
    # end of ml_train_models_for_predictions


    def ml_build_models_for_predictions(self, target_columns, ml_base_request, rds, dbs, debug=False):

        record                      = {
                                        "AlgoNodes" : []
                                    }
        results                     = self.build_def_hash("Display Error", "Not Run", record)

        try:

            self.lg("BuildModels for TargetColumns(" + str(len(target_columns)) + ")", 6)

            cur_done                = 0
            total_done              = len(target_columns)
            creation_date_str       = datetime.datetime.now().strftime("%Y-%M-%D %H:%M:%S")

            for col_name in target_columns:

                new_node            = {
                                        "TargetColumn"  : col_name,
                                        "Algo"          : None,
                                        "Creation"      : creation_date_str
                                    }
           
                if debug:
                    self.lg("", 6)
                
                self.lg("Build Processing(" + str(cur_done) + "/" + str(total_done) + ") Algo(" + str(col_name) + ")", 6)
                lg("Build Processing(" + str(cur_done) + "/" + str(total_done) + ") Algo(" + str(col_name) + ")", 6)
            
                ml_req                                  = self.ml_build_req_node(ml_base_request)
                ml_req["TargetColumnName"]              = col_name
                ml_req["MLAlgo"]["Cache"]["ModelID"]    = str(cur_done)
                
                cur_done                                += 1
                
                # Customize as needed:
                ml_req["MLAlgo"]["Meta"]["UnitsAhead"]  = 0

                # For this run:
                algo_node               = {
                                            "Request"   : ml_req,
                                            "Response"  : {}
                                        }

                if bool(ml_req["MLAlgo"]["Cache"]["UseCaches"]):
                    if ml_req["TrackingType"] == "UseTargetColAndUnits":
                        ml_req["ModelCache"]    = {
                                                    "RLoc"  : "CACHE:_MD_" + str(ml_req["TrackingName"]) + "_" + str(ml_req["TargetColumnName"])
                                                }
                # end of appending cache support

                algo_results            = self.ml_run_algo(ml_req, rds, dbs)

                lg("Build - Done Processing(" + str(cur_done) + "/" + str(total_done) + ") Algo(" + str(col_name) + ")", 6)

                if algo_results["Status"] == "SUCCESS":
                    if algo_results["Record"]["Model"] != None:
                        algo_node["Response"]   = algo_results["Record"]
                        new_node["Algo"]        = algo_node
                    else:
                        err_msg = "BuildModels - Failed to find a valid Model for ML(" + str(ml_req["MLType"]) + ") Algo(" + str(ml_req["MLAlgo"]["Name"]) + ")"
                        lg("ERROR: " + str(err_msg), 0)
                else:
                    err_msg     = "Build - Failed to run ML(" + str(ml_req["MLType"]) + ") Algo(" + str(ml_req["MLAlgo"]["Name"]) + ") with Error(" + str(algo_results["Error"]) + ")"
                    lg("ERROR: " + str(err_msg), 0)
                
                record["AlgoNodes"].append(new_node)
            # end of building the current target col

            results         = self.build_def_hash("SUCCESS", "", record)

        except Exception,k:
            err_msg         = "Unable to Build Models for Predictions with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of ml_build_models_for_predictions


    def ml_compile_predictions_from_models(self, req, rds, dbs, debug=False):

        record                  = {
                                    "ConfMatrices"      : [],
                                    "PredictionMarkers" : []
                                }
        results                 = self.build_def_hash("Display Error", "Not Run", record)

        try:

            confusion_matrices  = []
            prediction_markers  = []
            algo_nodes          = req["AlgoNodes"]
            prediction_row      = req["PredictionRow"]
            total_algos         = len(algo_nodes) 

            lg("Compiling Predictions for AlgoNodes(" + str(total_algos)  + ")", 6)

            for aidx,algo in enumerate(algo_nodes):

                node_res        = algo["Response"]

                lg("Algo(" + str(aidx+1) + "/" + str(total_algos) + ") Predicting TargetColumnName(" + str(node_res["TargetColumnName"]) + ")", 6)
                target_col_name = node_res["TargetColumnName"]
                model           = node_res["Model"]

                predict_req     = node_res
                acc_key         = target_col_name
                        
                if "ConfusionMatrix" in node_res:
                    if node_res["ConfusionMatrix"] is not None:
                        confusion_matrices.append({
                                    "ID"                : int(aidx),
                                    "TargetColumnName"  : target_col_name,
                                    "UnitsAhead"        : -1,
                                    "AccuracyKey"       : acc_key,
                                    "CM"                : node_res["ConfusionMatrix"]
                                })

                predict_req["PredictRow"]       = req["PredictionRow"]
                predict_req["PredictionMask"]   = req["PredictionMask"]
                
                predict_res     = self.ml_determine_model_prediction(predict_req)

                if predict_res["PredictionValue"] != None:

                    marker_node = {
                                    "TargetColumnName"  : predict_res["TargetColumnName"],
                                    "PredictionValue"   : predict_res["PredictionValue"],
                                    "PredictionAPI"     : predict_res["PredictionAPI"],
                                    "ProbaPredAPI"      : predict_res["ProbaPredAPI"],
                                    "Date"              : predict_res["Date"]
                                }
                    prediction_markers.append(marker_node)
            # end of processing all algos for a prediction

            record["PredictionMarkers"] = prediction_markers
            record["ConfMatrices"]      = confusion_matrices

            results             = self.build_def_hash("SUCCESS", "", record)

        except Exception,k:
            err_msg             = "Unable to Build Prediction Results for Algos with Ex(" + str(k) + ")"
            return self.handle_display_error(err_msg, record, True)
        # end of try/ex

        return results
    # end of ml_compile_predictions_from_models


    def ml_run_algo(self, req, rds, dbs, debug=False):
        
        ml_type         = "Unknown ML Type"
        ml_algo_name    = "Unknown ML Algo Name"
        err_msg         = ""

        record          = self.ml_build_res_node(req)

        results         = self.build_def_hash("Display Error", "Not Run", record)

        try:

            is_valid_request        = self.build_def_hash("Display Error", "Unsupported Algo(" + str(req["MLAlgo"]["Name"]) + ")", record) 

            if "regress" in str(req["MLAlgo"]["Name"]):
                is_valid_request    = self.ml_is_valid_regression_request(req)
            else:
                is_valid_request    = self.ml_is_valid_classifier_request(req)

            if is_valid_request["Status"] != "SUCCESS":
                print "ERROR: Not Running ML Algorithm(" + str(is_valid_request["Error"]) + ") Please check the sample_filter_mask is not removing all the rows"
                return is_valid_request
            # validate the request

            import pandas as pd
            from pandas.tseries.offsets import BDay
            import numpy as np
            import matplotlib.pyplot as plt

            now                     = datetime.datetime.now()

            ml_request              = req
            ml_type                 = str(ml_request["MLType"])
            ml_algo_name            = str(ml_request["MLAlgo"]["Name"])
            ml_ds_name              = str(ml_request["MLAlgo"]["Meta"]["DSName"])
            ml_prediction_type      = str(ml_request["PredictionType"])

            dataset_name            = str(ml_ds_name).strip().lstrip()

            load_csv_request_args   = {
                                        "MLType"                : ml_request["MLType"],
                                        "TargetColumnName"      : ml_request["TargetColumnName"], # What column is getting processed
                                        "IgnoreFeatures"        : ml_request["IgnoreFeatures"],   # Prune non-int/float columns as needed: 
                                        "CSVFile"               : ml_request["MLAlgo"]["Meta"]["Source"]["CSVFile"]
                                    }
            lg("Loading CSV(" + str(load_csv_request_args["CSVFile"]) + ")", 6)

            csv_load_results        = self.sk_load_csv(load_csv_request_args, rds, dbs)

            if csv_load_results["Status"] != "SUCCESS":
                err_msg             = "Failed to Load CSV(" + str(load_csv_request_args["CSVFile"]) + ") with Error(" + str(csv_load_results["Error"]) + ")"
                lg("ERROR: " + str(err_msg), 0)
                print err_msg
                record["Tracking"]["End"]   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return self.build_def_hash("Display Error", err_msg, record)

            source_df               = csv_load_results["Record"]["SourceDF"]
            all_feature_names       = csv_load_results["Record"]["AllFeatures"]
            train_feature_names     = csv_load_results["Record"]["TrainFeatures"]
            sample_filter_mask      = (source_df.index > 0)
            prediction_filter_mask  = (source_df.index > 0)

            ml_request["TrainFeatures"] = train_feature_names

            if ml_prediction_type == "Forecast":
                source_df["Date"]       = pd.to_datetime(source_df["Date"],  format="%Y-%m-%d %H:%M:%S")
                source_df["FDate"]      = pd.to_datetime(source_df["FDate"], format="%Y-%m-%d %H:%M:%S")

            run_error_checking          = True

            #######################################################################
            #
            # Support passing in the filter mask from the request to decouple this
            # from the core
            # 
            found_mask_in_api           = False
            if "SamplesFilterMask" in ml_request["MLAlgo"]["Meta"]:

                if ml_request["MLAlgo"]["Meta"]["SamplesFilterMask"] is not None:
                    prediction_filter_mask  = ml_request["MLAlgo"]["Meta"]["SamplesFilterMask"]
                    found_mask_in_api       = True
            # end of applying mask from api request

            # Support v2 api:
            if not found_mask_in_api:
                if ml_type == "Custom Filter From Meta":
                    prediction_filter_mask  =     (source_df["Decision"] == 1) \
                                                & ((source_df["DcsnResult"] == 0) | (source_df["DcsnResult"] == 1))
                else:
                    err_msg             = "Unsupported Machine Learning Type for building a Samples Filter(" + str(ml_type) + ")"
                    lg("ERROR: " + str(err_msg), 0)
                    print err_msg
                    record["Tracking"]["End"]   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    return self.build_def_hash("Display Error", err_msg, record)
            # end of handling filter mask from the API for predictions

            if run_error_checking:

                lg ("Counting Samples from Mask", 6)
                num_samples             = len(source_df[sample_filter_mask].index)
                lg ("Counting Predictions from Mask", 6)
                num_predictions         = len(source_df[prediction_filter_mask].index)
                lg ("Done Counting Samples(" + str(num_samples) + ") Predictions(" + str(num_predictions) + ")", 6)

                if num_samples == 0 or num_predictions == 0:
                    err_msg             = "Failed to Find Samples and Predictions for DSName(" + str(dataset_name) + ") Algo(" + str(ml_algo_name) + ") AlgoType(" + str(ml_type) + ") NumSamples(" + str(num_samples) + ") NumPredictions(" + str(num_predictions) + ") - Please check the sample_filter_mask with UnitsAhead(" + str(units_ahead) + ")"
                    if num_samples == 0:
                        err_msg         = "Failed to Find Samples and Predictions for DSName(" + str(dataset_name) + ") Algo(" + str(ml_algo_name) + ") AlgoType(" + str(ml_type) + ") NumSamples(" + str(num_samples) + ") NumPredictions(" + str(num_predictions) + ") - Please check the sample_filter_mask with UnitsAhead(" + str(units_ahead) + ")"
                        return self.handle_display_error(err_msg, record, True)
                    elif num_predictions == 0:
                        err_msg         = "Failed to Find Samples and Predictions for DSName(" + str(dataset_name) + ") Algo(" + str(ml_algo_name) + ") AlgoType(" + str(ml_type) + ") NumSamples(" + str(num_samples) + ") NumPredictions(" + str(num_predictions) + ") Please check the prediction_filter_mask"
                        return self.handle_display_error(err_msg, record, True)
                    else:
                        return self.handle_display_error(err_msg, record, True)
                else:
                    self.lg("Valid Masks for DSName(" + str(dataset_name) + ") Algo(" + str(ml_algo_name) + ") AlgoType(" + str(ml_type) + ") NumSamples(" + str(num_samples) + ") NumPredictions(" + str(num_predictions) + ")", 6)
                # end of good/bad samples + prediction masks
            # end of error checking for invalid sample and prediction masks
            
            synthesis_request_args  = {
                                        "MLType"                : ml_type,
                                        "TargetColumnName"      : ml_request["TargetColumnName"],    # What column is getting processed
                                        "TargetColumnValues"    : ml_request["TargetColumnValues"],  # possible values each int in the target_column_name maps to
                                        "TrainFeatures"         : ml_request["TrainFeatures"],       # list of feature names to train the model
                                        "SourceDF"              : source_df,
                                        "SampleMask"            : sample_filter_mask,
                                        "SampleFileterJSON"     : {                     # Allow for error handling with json-rules
                                                                },
                                        "TrainToTestRatio"      : float(ml_request["MLAlgo"]["TTRatio"])
                                    }

            synthesis_results       = self.sk_synthesize_dataset_from_csv(synthesis_request_args, rds, dbs)

            if synthesis_results["Status"] != "SUCCESS":
                err_msg             = "Failed to Synthesize dataset with Error(" + str(synthesis_results["Error"]) + ")"
                lg("ERROR: " + str(err_msg), 0)
                print err_msg
                record["Tracking"]["End"]   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return self.build_def_hash("Display Error", err_msg, record)
            else:

                ml_request["TrainFeatureNames"] = synthesis_results["Record"]["TrainFeatures"]
                ml_request["FeaturesTrain"]     = synthesis_results["Record"]["FeatureTrain"]
                ml_request["FeaturesTest"]      = synthesis_results["Record"]["FeatureTest"]
                ml_request["TargetTrain"]       = synthesis_results["Record"]["TargetTrain"]
                ml_request["TargetTest"]        = synthesis_results["Record"]["TargetTest"]

                err_msg                         = self.ml_is_valid_train_and_test_set(ml_request)

                if err_msg != "":
                    print err_msg
                    err_msg         = "Stopping Before Fit and Predict for File(" + str(load_csv_request_args["CSVFile"]) + ") Error(" + str(err_msg) + ") Please check the sample_filter_mask is not removing all the rows for MLType(" + str(ml_type) + ")"
                    return self.handle_display_error(err_msg, record, True)
                    
                ml_result           = self.ml_fit_and_predict(ml_request, rds, dbs)

                if ml_result["Status"] == "SUCCESS":
                    if ml_result["Record"]["Model"] != None:

                        ml_obj                      = ml_result["Record"]["Model"]

                        if debug:
                            print ml_obj

                        record["SourceDF"]          = source_df
                        record["SampleMask"]        = sample_filter_mask     # to examine the sample filter mask and debug the train/test records
                        record["PredictionMask"]    = prediction_filter_mask # to apply the latest prediction for forecasts
                        record["FeatureNames"]      = ml_result["Record"]["FeatureNames"]
                        record["TargetColumnName"]  = ml_result["Record"]["TargetColumnName"]
                        record["MLAlgoName"]        = str(ml_request["MLAlgo"]["Name"])
                        record["Rankings"]          = ml_result["Record"]["Rankings"]
                        record["Accuracy"]          = ml_result["Record"]["Accuracy"]
                        record["AUROC"]             = ml_result["Record"]["AUROC"]
                        record["ConfusionMatrix"]   = ml_result["Record"]["ConfusionMatrix"]
                        record["CVResults"]         = ml_result["Record"]["CVResults"]
                        record["PredictionAPI"]     = ml_result["Record"]["PredictionAPI"]
                        record["ProbaPredsAPI"]     = ml_result["Record"]["ProbaPredAPI"]
                        record["PredictionsDF"]     = ml_result["Record"]["PredictionsDF"]
                        record["ProbaPredsDF"]      = ml_result["Record"]["ProbaPredsDF"]
                        record["Predictions"]       = ml_result["Record"]["Predictions"]
                        record["ProbaPreds"]        = ml_result["Record"]["ProbaPreds"]
                        record["Model"]             = ml_result["Record"]["Model"]

                        record["UnitsAheadSet"]     = req["UnitsAheadSet"]
                        record["UnitsAheadType"]    = req["UnitsAheadType"]
                        record["PredictionType"]    = req["PredictionType"]

                    else:
                        err_msg         = "Failed to build ML Object for Type(" + str(ml_type) + ") Algo(" + str(ml_algo_name) + ") with Error(" + str(ml_result["Error"]) + ")"
                        lg("ERROR: " + str(err_msg), 0)
                        print err_msg
                        record["Tracking"]["End"]   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        return self.build_def_hash("Display Error", err_msg, record)
                    # if there's no ml object
                else:
                    err_msg             = "Failed to ML Fit and Predict ML Type(" + str(ml_type) + ") Algo(" + str(ml_algo_name) + ") with Error(" + str(ml_result["Error"]) + ")"
                    lg("ERROR: " + str(err_msg), 0)
                    print err_msg
                    record["Tracking"]["End"]   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    return self.build_def_hash("Display Error", err_msg, record)
                # if the ml fit and predict failed

            # end of building result
            record["Tracking"]["End"]   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            results                     = self.build_def_hash("SUCCESS", "", record)

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to Run ML Algo(" + str(ml_type) + ") Name(" + str(ml_algo_name) + ") Ex(" + str(k) + ")"
            print err_msg
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of ml_run_algo


    def ml_fit_and_predict(self, req, rds, dbs):

        ml_type                     = req["MLType"]
        ml_algo_name                = req["MLAlgo"]["Name"]
        ml_algo_meta                = req["MLAlgo"]["Steps"]
        debug                       = False
        err_msg                     = ""
        record                      = {
                                        "Rankings"  : {},  # feature importance sorted by rank
                                        "Model"     : None # on success this will hold the classifier object
                                    }
        results                     = self.build_def_hash("Diplay Error", "Not run", {} )

        try:

            status                  = "Display Error"

            if "Debug" in req:
                debug               = bool(str(req["Debug"]).lower() == "true")

            self.lg("Building MLType(" + str(ml_type) + ") Algo(" + str(ml_algo_name) + ")", 6)
            ml_result               = self.build_def_hash("Failed", "Not Run", {})
                                
            if ml_algo_name == "gbm-classifier":
                self.lg("Running GBM", 6)
                ml_result               = self.ml_classifier_run_gbm(req, rds, dbs, debug)
                if ml_result["Status"] != "SUCCESS":
                    err_msg             = "Failed to run MLAlgo(" + str(ml_algo_name) + ") with Error(" + str(ml_result["Error"]) + ")"
                    lg("ERROR: " + str(err_msg), 0)
                    status              = "Display Error"
                else:
                    status              = "SUCCESS"
                    err_msg             = ""
                    record              = ml_result["Record"]
                # end of assigning values back to caller
            # end of gbm-classifier
            elif ml_algo_name == "xgb-classifier":
                self.lg("Running XGB", 6)
                ml_result               = self.ml_classifier_run_xgb(req, rds, dbs, debug)
                if ml_result["Status"] != "SUCCESS":
                    err_msg             = "Failed to run MLAlgo(" + str(ml_algo_name) + ") with Error(" + str(ml_result["Error"]) + ")"
                    lg("ERROR: " + str(err_msg), 0)
                    status              = "Display Error"
                else:
                    status              = "SUCCESS"
                    err_msg             = ""
                    record              = ml_result["Record"]
                # end of assigning values back to caller
            # end of ml_classifier_run_xgb
            elif ml_algo_name == "randomforest-classifier":
                self.lg("Running RF", 6)
                ml_result               = self.ml_classifier_run_random_forest(req, rds, dbs, debug)
                if ml_result["Status"] != "SUCCESS":
                    err_msg             = "Failed to run MLAlgo(" + str(ml_algo_name) + ") with Error(" + str(ml_result["Error"]) + ")"
                    lg("ERROR: " + str(err_msg), 0)
                    status              = "Display Error"
                else:
                    status              = "SUCCESS"
                    err_msg             = ""
                    record              = ml_result["Record"]
                # end of assigning values back to caller
            # end of ml_classifier_run_random_forest
            elif ml_algo_name == "extratrees-classifier":
                self.lg("Running EXT", 6)
                ml_result               = self.ml_classifier_run_extra_trees(req, rds, dbs, debug)
                if ml_result["Status"] != "SUCCESS":
                    err_msg             = "Failed to run MLAlgo(" + str(ml_algo_name) + ") with Error(" + str(ml_result["Error"]) + ")"
                    lg("ERROR: " + str(err_msg), 0)
                    status              = "Display Error"
                else:
                    status              = "SUCCESS"
                    err_msg             = ""
                    record              = ml_result["Record"]
                # end of assigning values back to caller
            # end of ml_classifier_run_extra_trees
            elif ml_algo_name == "xgb-regressor":
                self.lg("Running Regression - XGB", 6)
                ml_result               = self.ml_regression_run_xgb(req, rds, dbs, debug)
                if ml_result["Status"] != "SUCCESS":
                    err_msg             = "Failed to run MLAlgo(" + str(ml_algo_name) + ") with Error(" + str(ml_result["Error"]) + ")"
                    lg("ERROR: " + str(err_msg), 0)
                    status              = "Display Error"
                else:
                    status              = "SUCCESS"
                    err_msg             = ""
                    record              = ml_result["Record"]
                # end of assigning values back to caller
            # end of xgb-regressor
            else:
                err_msg             = "Unsupported MLAlgo(" + str(ml_algo_name) + ")"
                lg("ERROR: " + str(err_msg), 0)
                status              = "Display Error"
            # end of supported ml types

            results                 = self.build_def_hash(status, err_msg, record)

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to Fit and Predict with ML(" + str(ml_type) + ") Name(" + str(ml_algo_name) + ") Ex(" + str(k) + ")"
            print err_msg
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of ml_fit_and_predict

    
    def ml_build_predictions_df(self, req, predictions):

        import pandas as pd
        predictions_df      = pd.DataFrame({
                                "Index"         : req["FeaturesTest"].index,
                                "TargetTest"    : req["TargetTest"].values,
                                "Prediction"    : predictions
                            }).sort_values(by="Index").set_index("Index")

        return predictions_df
    # end of ml_build_predictions_df


    def ml_regression_build_prediction_results_df(self, pred_df, source_df, merge_on_column_name):

        import pandas as pd
        pred_df.reset_index(inplace=True)
        source_df.reset_index(inplace=True)
        merged_preds_df = pd.merge(pred_df, source_df, left_on=merge_on_column_name, right_on=merge_on_column_name, how="inner")

        if "Date" in str(merged_preds_df.columns):
            merged_preds_df["Date"] = pd.to_datetime(merged_preds_df["Date"], format='%Y-%m-%d')
        if "FDate" in str(merged_preds_df.columns):
            merged_preds_df["FDate"] = pd.to_datetime(merged_preds_df["FDate"], format='%Y-%m-%d')

        return merged_preds_df
    # end of ml_regression_build_prediction_results_df


    def ml_regression_build_prediction_test_window(self, req, num_units, rds, dbs):

        import pandas as pd

        ml_type                 = req["MLType"]
        target_column_name      = req["TargetColumnName"]   # What column is getting processed?
        target_column_values    = req["TargetColumnValues"] # Possible values each int in the target_column_name maps to
        train_feature_names     = req["TrainFeatures"]      # Pass in the features to train
        source_df               = req["SourceDF"]
        sample_filter_mask      = (source_df["DSName"] != "")

        new_df                  = source_df.iloc[-1 * int(num_units):]

        if "Date" in str(source_df.columns):
            new_df["Date"]      = pd.to_datetime(new_df["Date"], format='%Y-%m-%d')  # assuming the Date column is present
        if "FDate" in str(source_df.columns):
            new_df["FDate"]     = pd.to_datetime(new_df["FDate"], format='%Y-%m-%d') # assuming the Future Date column is present

        last_row    = new_df.iloc[-1]
            
        return new_df
    # end of ml_regression_build_prediction_test_window


    def ml_classifier_run_random_forest(self, req, rds, dbs, debug=False):

        record          = self.ml_build_res_node(req)

        results         = self.build_def_hash("Display Error", "Not Run", record)

        try:

            ##############################################################
            #
            # Parse Arguments:
            #
            ##############################################################

            # Assign meta data
            algo_meta_data          = req["MLAlgo"]["Steps"]
            target_column_name      = req["TargetColumnName"]
            feature_names           = req["TrainFeatureNames"]
            target_column_values    = req["TargetColumnValues"]
            debug                   = False
            train_api_node          = {}
            cross_val_api_node      = {}
            fit_api_node            = {}
            predict_api_node        = {}
            predictproba_api_node   = {}
            plot_api_node           = {}

            # Plot api
            show_plot               = False
            plot_type               = "pandas"
            plot_title              = ""
            plot_max_features       = 10
            x_axis_title            = ""
            y_axis_title            = ""
            plot_debug              = False

            if "Train" in algo_meta_data:
                if len(algo_meta_data["Train"]) > 0:
                    train_api_node          = algo_meta_data["Train"]
            # end of processing Train api
            
            if "CrossValidation" in algo_meta_data:
                if len(algo_meta_data["CrossValidation"]) > 0:
                    cross_val_api_node      = algo_meta_data["CrossValidation"]
            # end of processing CrossValidation api
            
            if "Fit" in algo_meta_data:
                if len(algo_meta_data["Fit"]) > 0:
                    fit_api_node            = algo_meta_data["Fit"]
            # end of processing Fit api
            
            if "Predict" in algo_meta_data:
                if len(algo_meta_data["Predict"]) > 0:
                    predict_api_node        = algo_meta_data["Predict"]
            # end of processing Predict api
            
            if "PredictProba" in algo_meta_data:
                if len(algo_meta_data["PredictProba"]) > 0:
                    predictproba_api_node   = algo_meta_data["PredictProba"]
            # end of processing PredictProba api
            
            if "Plot" in req["MLAlgo"]:
                if len(req["MLAlgo"]["Plot"]) > 0:
                    plot_api_node   = req["MLAlgo"]["Plot"]
                    if "PlotType" in plot_api_node:
                        plot_type       = str(plot_api_node["PlotType"])
                    if "ShowPlot" in plot_api_node:
                        show_plot       = bool(plot_api_node["ShowPlot"])
                    if "XAxisTitle" in plot_api_node:
                        x_axis_title    = str(plot_api_node["XAxisTitle"])
                    if "YAxisTitle" in plot_api_node:
                        y_axis_title    = str(plot_api_node["YAxisTitle"])
                    if "MaxFeatures" in plot_api_node:
                        plot_max_features = int(plot_api_node["MaxFeatures"])
                    if "Debug" in plot_api_node:
                        plot_debug      = bool(plot_api_node["Debug"])
            # end of processing Plot api

            if "Debug" in req:
                debug               = bool(req["Debug"])

            # Algorithm parameters
            num_jobs                = int(req["MLAlgo"]["NumJobs"])

            ##############################################################
            #
            # Start Processing:
            #
            ##############################################################
            import seaborn as sns
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            from sklearn.ensemble import RandomForestClassifier
            from pandas_ml import ConfusionMatrix # https://github.com/pandas-ml/pandas-ml/

            lg("Building RandomForest Classifier", 1)
            model                   = RandomForestClassifier(n_jobs=num_jobs)

            # Now train it:
            model.fit(req["FeaturesTrain"], req["TargetTrain"])

            # Predict against test data
            if debug:
                self.lg("", 6)
            lg("Predicting Values", 6)
            predictions         = model.predict(req["FeaturesTest"])

            preds               = []
            num_target_values   = len(target_column_values)
            for cur_idx,cur_row in enumerate(predictions):
                if debug:
                    print "Row(" + str(cur_idx) + ") V(" + str(cur_row) + ")"
                if int(cur_row) < num_target_values:
                    preds.append(target_column_values[cur_row])
                #for tar_idx,tar_value
            # end for all predictions        

            if debug:
                self.lg("", 6)
                self.lg("Result of Predictions:", 6)
                print preds
                self.lg("", 6)
                lg(" - Pandas Crosstab for inpsecting the Confusion Matrix:", 6)
                print pd.crosstab(index=record["TargetTest"], columns=preds, rownames= [ x_axis_title ], colnames= [ y_axis_title ], margins=True)
                self.lg("", 6)
                lg(" - Pandas Percentage for inpsecting the Confusion Matrix:", 6)
                print pd.crosstab(index=record["TargetTest"], columns=preds, rownames=[ x_axis_title ], colnames= [ y_axis_title ] ).apply(lambda r: r/r.sum(), axis=1)

            cm      = ConfusionMatrix(req["TargetTest"].tolist(), preds, labels=target_column_values)

            if debug:
                cm.print_stats()

            record["Predictions"]       = predictions
            record["FeatureNames"]      = feature_names
            record["TargetColumnName"]  = target_column_name
            record["MLAlgoName"]        = str(req["MLAlgo"]["Name"])
            record["Model"]             = model
            record["ConfusionMatrix"]   = cm

            if show_plot:

                print cm.print_stats()

                lg("Plotting Confusion Matrix", 1)
                ax          = cm.plot()
                plt.title(plot_title)
                self.pd_add_footnote(ax.get_figure())
                plt.show()
            # end of plot and print
            results         = self.build_def_hash("SUCCESS", "", record)
        
        except Exception as k:
            err_msg         = "Failed to SK Build Random Forest Confusion Matrix with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            print err_msg
            results         = self.build_def_hash("Display Error", err_msg, record)
        # try/ex

        return results
    # end of ml_classifier_run_random_forest


    def ml_classifier_run_extra_trees(self, req, rds, dbs, debug=False):

        record          = self.ml_build_res_node(req)

        results         = self.build_def_hash("Display Error", "Not Run", record)

        try:

            ##############################################################
            #
            # Parse Arguments:
            #
            ##############################################################
            target_column_name      = req["TargetColumnName"]
            feature_names           = req["TrainFeatureNames"]
            target_column_values    = req["TargetColumnValues"]

            # Assign meta data
            algo_meta_data          = req["MLAlgo"]["Steps"]
            target_column_name      = req["TargetColumnName"]
            feature_names           = req["TrainFeatureNames"]
            debug                   = False
            train_api_node          = {}
            cross_val_api_node      = {}
            fit_api_node            = {}
            predict_api_node        = {}
            predictproba_api_node   = {}
            plot_api_node           = {}

            # Plot api
            show_plot               = False
            plot_type               = "pandas"
            plot_title              = ""
            plot_max_features       = 10
            x_axis_title            = ""
            y_axis_title            = ""
            plot_debug              = False

            if "Train" in algo_meta_data:
                if len(algo_meta_data["Train"]) > 0:
                    train_api_node          = algo_meta_data["Train"]
            # end of processing Train api
            
            if "CrossValidation" in algo_meta_data:
                if len(algo_meta_data["CrossValidation"]) > 0:
                    cross_val_api_node      = algo_meta_data["CrossValidation"]
            # end of processing CrossValidation api
            
            if "Fit" in algo_meta_data:
                if len(algo_meta_data["Fit"]) > 0:
                    fit_api_node            = algo_meta_data["Fit"]
            # end of processing Fit api
            
            if "Predict" in algo_meta_data:
                if len(algo_meta_data["Predict"]) > 0:
                    predict_api_node        = algo_meta_data["Predict"]
            # end of processing Predict api
            
            if "PredictProba" in algo_meta_data:
                if len(algo_meta_data["PredictProba"]) > 0:
                    predictproba_api_node   = algo_meta_data["PredictProba"]
            # end of processing PredictProba api
            
            if "Plot" in req["MLAlgo"]:
                if len(req["MLAlgo"]["Plot"]) > 0:
                    plot_api_node   = req["MLAlgo"]["Plot"]
                    if "PlotType" in plot_api_node:
                        plot_type       = str(plot_api_node["PlotType"])
                    if "ShowPlot" in plot_api_node:
                        show_plot       = bool(plot_api_node["ShowPlot"])
                    if "XAxisTitle" in plot_api_node:
                        x_axis_title    = str(plot_api_node["XAxisTitle"])
                    if "YAxisTitle" in plot_api_node:
                        y_axis_title    = str(plot_api_node["YAxisTitle"])
                    if "MaxFeatures" in plot_api_node:
                        plot_max_features = int(plot_api_node["MaxFeatures"])
                    if "Debug" in plot_api_node:
                        plot_debug      = bool(plot_api_node["Debug"])
            # end of processing Plot api

            if "Debug" in req:
                debug               = bool(req["Debug"])

            # Algorithm parameters
            num_estimators          = int(req["MLAlgo"]["NumEstimators"])
            random_state            = int(req["MLAlgo"]["RandomState"])

            ##############################################################
            #
            # Start Processing:
            #
            ##############################################################
            import seaborn as sns
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            from sklearn.ensemble import ExtraTreesClassifier
            from pandas_ml import ConfusionMatrix # https://github.com/pandas-ml/pandas-ml/

            # Build a forest and compute the feature importances
            model = ExtraTreesClassifier(n_estimators=num_estimators,
                                            random_state=random_state)

            # Now train it:
            model.fit(req["FeaturesTrain"], req["TargetTrain"])

            importances             = model.feature_importances_
            std = np.std([tree.feature_importances_ for tree in model.estimators_], axis=0)

            self.lg("ImpFeatures(" + str(len(model.feature_importances_)) + ")", 6)
            indices = np.argsort(importances)[::-1]

            max_valid_features      = 0
            trained_shaped_features = len(indices)
            x_labels                = []

            # Print the feature ranking
            for f in range(trained_shaped_features):
                feature_idx         = indices[f]

                if feature_idx < len(feature_names):
                    max_valid_features  += 1
                    feature_name        = feature_names[int(feature_idx)]
                    feature_imp         = "0.0"
                    if importances[indices[f]]:
                        feature_imp     = self.to_float_str(float(importances[indices[f]]) * 100.0)

                    feature_dispname    = str(feature_name) + " " + str(feature_imp) + "%"
                    x_labels.append(str(feature_dispname))

                    new_node            = {
                                            "Rank"          : str(f),
                                            "Column"        : str(feature_idx),
                                            "Name"          : str(feature_name),
                                            "DisplayName"   : feature_dispname,
                                            "Importance"    : str(feature_imp)
                                        }
                    record["Rankings"].append(new_node)
            # Plot the feature importances of the forest
            
            # Predict against test data
            if debug:
                self.lg("", 6)
            lg("Predicting Values", 6)
            predictions             = model.predict(req["FeaturesTest"])

            record["FeatureNames"]  = feature_names
            record["TargetColumnName"] = str(req["TargetColumnName"])
            record["MLAlgoName"]    = str(req["MLAlgo"]["Name"])
            record["Model"]         = model
            
            lg("Building ConfusionMatrix", 6)

            cm                      = ConfusionMatrix(req["TargetTest"].tolist(), predictions, labels=target_column_values)

            record["ConfusionMatrix"]   = cm
        
            results         = self.build_def_hash("SUCCESS", "", record)
        
        except Exception as k:
            err_msg         = "Failed to determine feature importance with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            print err_msg
            results         = self.build_def_hash("Display Error", err_msg, record)
        # try/ex

        return results
    # end of ml_classifier_run_extra_trees


    def ml_classifier_run_gbm(self, req, rds, dbs, debug=False):

        status                      = "Display Error"
        err_msg                     = ""
        record                      = self.ml_build_res_node(req)
        results                     = self.build_def_hash(status, err_msg, record)

        try:

            status                  = "SUCCESS"
            err_msg                 = ""

            self.load_thirdparty_dir("mlalgorithms")


            # Assign meta data
            algo_meta_data          = req["MLAlgo"]["Steps"]

            target_column_name      = req["TargetColumnName"]
            feature_names           = req["TrainFeatureNames"]
            target_column_values    = req["TargetColumnValues"]

            num_estimators          = 10
            learning_rate           = 0.1
            max_features            = 10
            max_depth               = 2
            min_samples_split       = 10
            
            ##############################################################
            #
            # Parse Arguments:
            #
            ##############################################################
            target_column_name      = req["TargetColumnName"]
            feature_names           = req["TrainFeatureNames"]

            # Assign meta data
            algo_meta_data          = req["MLAlgo"]["Steps"]
            target_column_name      = req["TargetColumnName"]
            feature_names           = req["TrainFeatureNames"]
            debug                   = False
            train_api_node          = {}
            cross_val_api_node      = {}
            fit_api_node            = {}
            predict_api_node        = {}
            predictproba_api_node   = {}
            plot_api_node           = {}

            # Plot api
            show_plot               = False
            plot_type               = "pandas"
            plot_title              = ""
            plot_max_features       = 10
            x_axis_title            = ""
            y_axis_title            = ""
            plot_debug              = False

            if "Train" in algo_meta_data:
                if len(algo_meta_data["Train"]) > 0:
                    train_api_node          = algo_meta_data["Train"]
            # end of processing Train api
            
            if "CrossValidation" in algo_meta_data:
                if len(algo_meta_data["CrossValidation"]) > 0:
                    cross_val_api_node      = algo_meta_data["CrossValidation"]
            # end of processing CrossValidation api
            
            if "Fit" in algo_meta_data:
                if len(algo_meta_data["Fit"]) > 0:
                    fit_api_node            = algo_meta_data["Fit"]
            # end of processing Fit api
            
            if "Predict" in algo_meta_data:
                if len(algo_meta_data["Predict"]) > 0:
                    predict_api_node        = algo_meta_data["Predict"]
            # end of processing Predict api
            
            if "PredictProba" in algo_meta_data:
                if len(algo_meta_data["PredictProba"]) > 0:
                    predictproba_api_node   = algo_meta_data["PredictProba"]
            # end of processing PredictProba api
            
            if "Plot" in req["MLAlgo"]:
                if len(req["MLAlgo"]["Plot"]) > 0:
                    plot_api_node   = req["MLAlgo"]["Plot"]
                    if "PlotType" in plot_api_node:
                        plot_type       = str(plot_api_node["PlotType"])
                    if "ShowPlot" in plot_api_node:
                        show_plot       = bool(plot_api_node["ShowPlot"])
                    if "XAxisTitle" in plot_api_node:
                        x_axis_title    = str(plot_api_node["XAxisTitle"])
                    if "YAxisTitle" in plot_api_node:
                        y_axis_title    = str(plot_api_node["YAxisTitle"])
                    if "MaxFeatures" in plot_api_node:
                        plot_max_features = int(plot_api_node["MaxFeatures"])
                    if "Debug" in plot_api_node:
                        plot_debug      = bool(plot_api_node["Debug"])
            # end of processing Plot api

            if "Debug" in req:
                debug               = bool(req["Debug"])

            # Algorithm parameters
            num_estimators          = int(req["MLAlgo"]["NumEstimators"])
            learning_rate           = float(req["MLAlgo"]["LearningRate"])
            max_features            = int(req["MLAlgo"]["MaxFeatures"])
            max_depth               = int(req["MLAlgo"]["MaxDepth"])
            min_samples_split       = int(req["MLAlgo"]["MinSamplesSplit"])


            ##############################################################
            #
            # Start Processing:
            #
            ##############################################################
            import seaborn as sns
            from sklearn.metrics import roc_auc_score
            from mla.ensemble.gbm import GradientBoostingClassifier, GradientBoostingRegressor
            from mla.metrics.metrics import mean_squared_error
            from pandas_ml import ConfusionMatrix # https://github.com/pandas-ml/pandas-ml/
            
            model                   = GradientBoostingClassifier(n_estimators=num_estimators, 
                                                max_depth=max_depth,
                                                max_features=max_features, 
                                                learning_rate=learning_rate,
                                                min_samples_split=min_samples_split)

            lg("Building GBM - Features(" + str(len(req["TrainFeatureNames"])) \
                                    + ") TargetColumn(" + str(req["TargetColumnName"]) \
                                    + ") Train(" + str(len(req["FeaturesTrain"])) \
                                    + ") Test(" + str(len(req["FeaturesTest"])) \
                                    + ") Target Train(" + str(len(req["TargetTrain"])) \
                                    + ") Test(" + str(len(req["TargetTest"])) \
                                    + ")", 6)

            model.fit(req["FeaturesTrain"].values, req["TargetTrain"].values)

            lg("Predicting Values", 6)
            predictions = model.predict(req["FeaturesTest"].values)
            
            max_prediction          = predictions.max()
            min_prediction          = predictions.min()
            auroc_score             = roc_auc_score(req["TargetTest"], predictions)
            rankings                = []
            
            lg("Predictions(" + str(len(predictions)) + ") Max(" + str(max_prediction) + ") Min(" + str(min_prediction) + ") AUROC(" + str(auroc_score) + ") Rankings(" + str(len(rankings)) + ")", 6)

            record["TargetColumnName"] = str(req["TargetColumnName"])
            record["MLAlgoName"]    = str(req["MLAlgo"]["Name"])
            record["FeatureNames"]  = req["TrainFeatureNames"]
            record["AUROC"]         = auroc_score
            record["Predictions"]   = predictions
            record["Predictions"]   = predictions
            record["Model"]         = model
            record["Rankings"]      = rankings
            
            lg("Building ConfusionMatrix", 6)

            cm                      = ConfusionMatrix(req["TargetTest"].tolist(), predictions, labels=target_column_values)

            record["ConfusionMatrix"]   = cm

            results                 = self.build_def_hash(status, err_msg, record)

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to run GBM Ex(" + str(k) + ")"
            print err_msg
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of ml_classifier_run_gbm


    def ml_classifier_run_xgb(self, req, rds, dbs, debug=False):

        status                      = "Display Error"
        err_msg                     = ""
        record                      = {
                                        "Rankings"      : [],
                                        "AUROC"         : 0.0,
                                        "Predictions"   : None,
                                        "Model"         : None
                                    }
        results                     = self.build_def_hash(status, err_msg, record)

        try:

            status                  = "SUCCESS"
            err_msg                 = ""
            use_model_cache         = req["MLAlgo"]["Cache"]["UseCaches"]

            import seaborn as sns
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            from sklearn.metrics import roc_auc_score
            import xgboost as xgb
            from xgboost.sklearn import XGBClassifier
            from sklearn import cross_validation, metrics   # Additional scklearn functions
            from sklearn.grid_search import GridSearchCV    # Perforing grid search
            from pandas_ml import ConfusionMatrix # https://github.com/pandas-ml/pandas-ml/
            
            target_column_name      = req["TargetColumnName"]
            feature_names           = req["TrainFeatureNames"]
            target_column_values    = req["TargetColumnValues"]

            # Assign meta data
            algo_meta_data          = req["MLAlgo"]["Steps"]

            max_features            = int(algo_meta_data["MaxFeatures"])

            train_api_node          = algo_meta_data["Train"]
            cross_val_api_node      = algo_meta_data["CrossValidation"]
            fit_api_node            = algo_meta_data["Fit"]
            predict_api_node        = algo_meta_data["Predict"]
            predictproba_api_node   = algo_meta_data["PredictProba"]

            # Train api
            learning_rate           = float(train_api_node["LearningRate"])
            num_estimators          = int(train_api_node["NumEstimators"])
            objective               = str(train_api_node["Objective"]) # binary:logistic 
            max_depth               = int(train_api_node["MaxDepth"])
            max_delta_step          = int(train_api_node["MaxDeltaStep"])
            min_child_weight        = int(train_api_node["MinChildWeight"])
            gamma                   = float(train_api_node["Gamma"])
            subsample               = float(train_api_node["SubSample"])
            colsample_by_tree       = float(train_api_node["ColSampleByTree"])
            colsample_by_level      = float(train_api_node["ColSampleByLevel"])
            reg_alpha               = float(train_api_node["RegAlpha"])
            reg_lambda              = float(train_api_node["RegLambda"])
            base_score              = float(train_api_node["BaseScore"])
            nthread                 = int(train_api_node["NumThreads"])
            scale_pos_weight        = int(train_api_node["ScaledPositionWeight"])
            seed                    = int(train_api_node["Seed"])
            silent                  = int(train_api_node["Debug"])
            
            # Cross Validation api
            cv_enabled              = False
            cv_metrics              = "auc"
            cv_num_boost_rounds     = 10 
            cv_num_folds            = 3
            cv_stratified           = False
            cv_folds                = None
            cv_seed                 = 0
            cv_early_stopping_rounds= None
            cv_verbose_eval         = False

            if "CrossValidation" in algo_meta_data:
                cv_enabled          = True
            if "Metrics" in cross_val_api_node:
                cv_metrics          = str(cross_val_api_node["Metrics"])
            if "NumBoostRounds" in cross_val_api_node:
                cv_num_boost_rounds = int(cross_val_api_node["NumBoostRounds"]) 
            if "NumFolds" in cross_val_api_node:
                cv_num_folds        = int(cross_val_api_node["NumFolds"])
            if "Stratified" in cross_val_api_node:
                cv_stratified       = bool(cross_val_api_node["Stratified"])
            if "Seed" in cross_val_api_node:
                cv_seed             = int(cross_val_api_node["Seed"])
            if "EarlyStoppingRounds" in cross_val_api_node:
                cv_early_stopping_rounds = int(cross_val_api_node["Seed"])
            if "ShowProgress" in cross_val_api_node:
                cv_verbose_eval     = bool(cross_val_api_node["ShowProgress"])

            # Fit api
            sample_weight           = None
            eval_set                = None
            eval_metric             = None
            early_stopping_rounds   = None
            fit_debug               = False
            if fit_api_node["SampleWeight"] != "":
                sample_weight       = fit_api_node["SampleWeight"]
            if fit_api_node["EvalSet"] != "":
                eval_set            = fit_api_node["EvalSet"]
            if fit_api_node["EvalMetric"] != "":
                eval_metric         = fit_api_node["EvalMetric"]
            if fit_api_node["Debug"] != "":
                fit_debug           = bool(fit_api_node["Debug"])
            # EarlyStoppingRounds:
	    # Activates early stopping. Validation error needs to decrease at
	    # least every <early_stopping_rounds> round(s) to continue training.
	    # Requires at least one item in evals.  If there's more than one,
	    # will use the last. Returns the model from the last iteration
	    # (not the best one). If early stopping occurs, the model will
	    # have three additional fields: bst.best_score, bst.best_iteration
	    # and bst.best_ntree_limit.
	    # (Use bst.best_ntree_limit to get the correct value if num_parallel_tree
	    #and/or num_class appears in the parameters)
            if fit_api_node["EarlyStoppingRounds"] != "":
                early_stopping_rounds = int(fit_api_node["EarlyStoppingRounds"]) 

            # Predict api
            pred_output_margin      = False
            pred_ntree_limit        = 0
            if predict_api_node["OutputMargin"] != "":
                pred_output_margin  = bool(predict_api_node["OutputMargin"]) 
            if predict_api_node["NumTreeLimit"] != "":
                pred_ntree_limit    = int(predict_api_node["NumTreeLimit"]) 

            # PredictProba api
            proba_output_margin      = False
            proba_ntree_limit        = 0
            if predictproba_api_node["OutputMargin"] != "":
                proba_output_margin  = bool(predictproba_api_node["OutputMargin"]) 
            if predictproba_api_node["NumTreeLimit"] != "":
                proba_ntree_limit    = int(predictproba_api_node["NumTreeLimit"]) 

            #Choose all predictors except target & IDcols

            lg("Building predictors", 6)
            predictors              = [x for x in req["FeaturesTrain"].columns if x not in [target_column_name] ]
            lg("Predictors(" + str(len(predictors)) + ") Building XGB Classifier", 6)

            model                   = None

            if use_model_cache:

                ra_name             = req["ModelCache"]["RLoc"].split(":")[0]
                ra_key              = req["ModelCache"]["RLoc"].split(":")[1]

                cached_model_req    = {
                                        "RAName"    : str(ra_name),
                                        "RAKey"     : str(ra_key)
                                    }

                self.lg("Getting Model(" + str(ra_key) + ") from Cache", 6)

                model_results       = self.ml_get_single_model_from_cache(cached_model_req, rds, dbs, debug)

                if model_results["Model"] == None or model_results["Model"] == "":
                    err_msg         = "Did not find a valid Model(" + str(ra_key) + ") Key(" + str(ra_key) + ") RLoc(" + str(ra_name) + ":" + str(ra_key) + ")"
                    return self.handle_display_error(err_msg, record, True)
                else:
                    self.lg("Found Model(" + str(ra_key) + ") from Cache", 6)
                    model           = model_results["Model"]
                # end of if the found the model
            else:
                #
                # Here's the supported api variables from 11/17/2016 build:
                #
                # https://github.com/dmlc/xgboost/blob/c52b2faba4d070fb6fe9e0f8fcda34f296522230/python-package/xgboost/sklearn.py#L332
                model               = XGBClassifier(learning_rate=learning_rate,
                                            n_estimators        = num_estimators,
                                            objective           = objective,
                                            max_depth           = max_depth,
                                            max_delta_step      = max_delta_step,
                                            min_child_weight    = min_child_weight,
                                            gamma               = gamma,
                                            subsample           = subsample,
                                            colsample_bytree    = colsample_by_tree,
                                            colsample_bylevel   = colsample_by_level,
                                            reg_alpha           = reg_alpha,
                                            reg_lambda          = reg_lambda,
                                            base_score          = base_score,
                                            nthread             = nthread,
                                            scale_pos_weight    = scale_pos_weight,
                                            silent              = silent,
                                            seed                = seed)
            # end of using from cache or not

            lg("Training Classifier", 6)
            if cv_enabled:
            
                lg("Getting XGB Params", 6)
                xgb_param           = model.get_xgb_params()
                lg("Building DMatrix for Target(" + str(req["TargetColumnName"]) + ")", 6)
                xg_training_dmatrix = xgb.DMatrix(req["FeaturesTrain"].values, label=req["TargetTrain"].values)

                #lg("Building CV", 6)
                #cvresult            = xgb.cv(params=xgb_param, 
                #                                dtrain                  = xg_training_dmatrix, 
                #                                metrics                 = cv_metrics, 
                #                                num_boost_round         = cv_num_boost_rounds,
                #                                nfold                   = cv_num_folds,
                #                                stratified              = cv_stratified,
                #                                folds                   = cv_folds, 
                #                                seed                    = cv_seed, 
                #                                early_stopping_rounds   = cv_early_stopping_rounds, 
                #                                verbose_eval            = cv_verbose_eval)
                #lg("Setting the model's params", 6)
                #model.set_params(n_estimators=cvresult.shape[0])
            #end of building the cv
                
            if use_model_cache:
                self.lg("Model already trained and fit", 6)
            else:
                lg("Fitting XGB - Features(" + str(len(req["TrainFeatureNames"])) \
                                        + ") TargetColumn(" + str(req["TargetColumnName"]) \
                                        + ") Train(" + str(len(req["FeaturesTrain"])) \
                                        + ") Test(" + str(len(req["FeaturesTest"])) \
                                        + ") Target Train(" + str(len(req["TargetTrain"])) \
                                        + ") Test(" + str(len(req["TargetTest"])) \
                                        + ")", 6)

                model.fit(  X                       = req["FeaturesTrain"], 
                            y                       = req["TargetTrain"],
                            sample_weight           = sample_weight,
                            eval_set                = eval_set,
                            eval_metric             = eval_metric,
                            early_stopping_rounds   = early_stopping_rounds,
                            verbose                 = fit_debug)
            # end of using cache or newly-built model object

            lg("Predicting Values", 6)
            #Predict training set:

            predictions                 = model.predict(req["FeaturesTest"],
                                                output_margin   = pred_output_margin,
                                                ntree_limit     = pred_ntree_limit)
            
            predictions_df              = pd.DataFrame({
                                            "index"         : req["FeaturesTest"].index,
                                            "TargetTest"    : req["TargetTest"].values,
                                            "Prediction"    : predictions
                                        }).sort_values(by="index").set_index("index")

            proba_predictions           = model.predict_proba(req["FeaturesTest"],
                                                output_margin   = proba_output_margin,
                                                ntree_limit     = proba_ntree_limit)[:,1]
                
            lg("Building Accuracy", 6)
            accuracy                = None
            try:
                accuracy            = model.score(req["FeaturesTest"], req["TargetTest"])
            except Exception,x:
                self.lg("Unable to build Accuracy for TargetColumnName(" + str(req["TargetColumnName"]) + ")", 6)

            max_prediction          = predictions.max()
            min_prediction          = predictions.min()
            auroc_score             = None
            try:
                auroc_score         = roc_auc_score(req["TargetTest"], predictions)
            except Exception,x:
                self.lg("Unable to build AUROC for TargetColumnName(" + str(req["TargetColumnName"]) + ")", 6)
            rankings                = []
            
            lg("Predictions(" + str(len(predictions)) + ") Max(" + str(max_prediction) + ") Min(" + str(min_prediction) + ") AUROC(" + str(auroc_score) + ") Rankings(" + str(len(rankings)) + ")", 6)

            record["TargetColumnName"] = str(req["TargetColumnName"])
            record["MLAlgoName"]    = str(req["MLAlgo"]["Name"])
            record["FeatureNames"]  = req["TrainFeatureNames"]
            record["Accuracy"]      = accuracy
            record["CVResults"]     = None
            record["Predictions"]   = predictions
            record["PredictionAPI"] = predict_api_node
            record["ProbaPredAPI"]  = predictproba_api_node
            record["Predictions"]   = predictions
            record["PredictionsDF"] = predictions_df
            record["ProbaPredsDF"]  = None
            record["ProbaPreds"]    = None
            record["Model"]         = model
            record["Rankings"]      = rankings
            record["AUROC"]         = auroc_score
        
            lg("Building ConfusionMatrix", 6)
            cm                      = ConfusionMatrix(req["TargetTest"].tolist(), predictions, labels=target_column_values)
            record["ConfusionMatrix"]   = cm

            if os.getenv("ENV_SHOW_XGB_CLASSIFIER_PLOT", "0") == "1":
                feat_imp = pd.Series(model.booster().get_fscore()).sort_values(ascending=False)
                feat_imp.plot(kind='bar', title='Feature Importances')
                plt.ylabel('Feature Importance Score')    
                plt.show()
            # end of showing feature importance
            
            results                 = self.build_def_hash(status, err_msg, record)

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to run XGB Ex(" + str(k) + ")"
            print err_msg
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of ml_classifier_run_xgb


    def ml_regression_run_xgb(self, req, rds, dbs, debug=False):

        status                      = "Display Error"
        err_msg                     = ""
        record                      = self.ml_build_res_node(req)
        results                     = self.build_def_hash(status, err_msg, record)

        try:

            status                  = "SUCCESS"
            err_msg                 = ""
            use_model_cache         = req["MLAlgo"]["Cache"]["UseCaches"]

            import seaborn as sns
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            from sklearn.metrics import roc_auc_score
            import xgboost as xgb
            from xgboost.sklearn import XGBRegressor
            from sklearn import cross_validation, metrics   # Additional scklearn functions
            from sklearn.grid_search import GridSearchCV    # Perforing grid search
            
            target_column_name      = req["TargetColumnName"]
            feature_names           = req["TrainFeatureNames"]
            target_column_values    = req["TargetColumnValues"]

            # Assign meta data
            algo_meta_data          = req["MLAlgo"]["Steps"]

            max_features            = int(algo_meta_data["MaxFeatures"])

            train_api_node          = algo_meta_data["Train"]
            cross_val_api_node      = algo_meta_data["CrossValidation"]
            fit_api_node            = algo_meta_data["Fit"]
            predict_api_node        = algo_meta_data["Predict"]
            predictproba_api_node   = algo_meta_data["PredictProba"]
            plot_api_node           = {}

            # Train api
            learning_rate           = float(train_api_node["LearningRate"])
            num_estimators          = int(train_api_node["NumEstimators"])
            objective               = str(train_api_node["Objective"]) # binary:logistic / reg:linear
            max_depth               = int(train_api_node["MaxDepth"])
            max_delta_step          = int(train_api_node["MaxDeltaStep"])
            min_child_weight        = int(train_api_node["MinChildWeight"])
            gamma                   = float(train_api_node["Gamma"])
            subsample               = float(train_api_node["SubSample"])
            colsample_by_tree       = float(train_api_node["ColSampleByTree"])
            colsample_by_level      = float(train_api_node["ColSampleByLevel"])
            reg_alpha               = float(train_api_node["RegAlpha"])
            reg_lambda              = float(train_api_node["RegLambda"])
            base_score              = float(train_api_node["BaseScore"])
            nthread                 = int(train_api_node["NumThreads"])
            scale_pos_weight        = int(train_api_node["ScaledPositionWeight"])
            seed                    = int(train_api_node["Seed"])
            silent                  = int(train_api_node["Debug"])
            
            # Cross Validation api
            cv_enabled              = False
            cv_metrics              = "auc"
            cv_num_boost_rounds     = 10 
            cv_num_folds            = 3
            cv_stratified           = False
            cv_folds                = None
            cv_seed                 = 0
            cv_early_stopping_rounds= None
            cv_verbose_eval         = False

            if "CrossValidation" in algo_meta_data:
                cv_enabled          = True
            if "Metrics" in cross_val_api_node:
                cv_metrics          = str(cross_val_api_node["Metrics"])
            if "NumBoostRounds" in cross_val_api_node:
                cv_num_boost_rounds = int(cross_val_api_node["NumBoostRounds"]) 
            if "NumFolds" in cross_val_api_node:
                cv_num_folds        = int(cross_val_api_node["NumFolds"])
            if "Stratified" in cross_val_api_node:
                cv_stratified       = bool(cross_val_api_node["Stratified"])
            if "Seed" in cross_val_api_node:
                cv_seed             = int(cross_val_api_node["Seed"])
            if "EarlyStoppingRounds" in cross_val_api_node:
                cv_early_stopping_rounds = int(cross_val_api_node["Seed"])
            if "ShowProgress" in cross_val_api_node:
                cv_verbose_eval     = bool(cross_val_api_node["ShowProgress"])

            # Fit api
            sample_weight           = None
            eval_set                = None
            eval_metric             = None
            early_stopping_rounds   = None
            fit_debug               = False
            if fit_api_node["SampleWeight"] != "":
                sample_weight       = fit_api_node["SampleWeight"]
            if fit_api_node["EvalSet"] != "":
                eval_set            = fit_api_node["EvalSet"]
            if fit_api_node["EvalMetric"] != "":
                eval_metric         = fit_api_node["EvalMetric"]
            if fit_api_node["Debug"] != "":
                fit_debug           = bool(fit_api_node["Debug"])
            # EarlyStoppingRounds:
	    # Activates early stopping. Validation error needs to decrease at
	    # least every <early_stopping_rounds> round(s) to continue training.
	    # Requires at least one item in evals.  If there's more than one,
	    # will use the last. Returns the model from the last iteration
	    # (not the best one). If early stopping occurs, the model will
	    # have three additional fields: bst.best_score, bst.best_iteration
	    # and bst.best_ntree_limit.
	    # (Use bst.best_ntree_limit to get the correct value if num_parallel_tree
	    #and/or num_class appears in the parameters)
            if fit_api_node["EarlyStoppingRounds"] != "":
                early_stopping_rounds = int(fit_api_node["EarlyStoppingRounds"]) 

            # Predict api
            pred_output_margin      = False
            pred_ntree_limit        = 0
            if predict_api_node["OutputMargin"] != "":
                pred_output_margin  = bool(predict_api_node["OutputMargin"]) 
            if predict_api_node["NumTreeLimit"] != "":
                pred_ntree_limit    = int(predict_api_node["NumTreeLimit"]) 

            # PredictProba api
            proba_output_margin      = False
            proba_ntree_limit        = 0
            if predictproba_api_node["OutputMargin"] != "":
                proba_output_margin  = bool(predictproba_api_node["OutputMargin"]) 
            if predict_api_node["NumTreeLimit"] != "":
                proba_ntree_limit    = int(predictproba_api_node["NumTreeLimit"]) 
            

            # Plot api
            show_plot               = False
            plot_type               = "pandas"
            plot_title              = ""
            plot_max_features       = 10
            x_axis_title            = ""
            y_axis_title            = ""
            default_x_axis          = []
            default_y_axis          = []
            plot_debug              = False
            if "Plot" in req["MLAlgo"]:
                if len(req["MLAlgo"]["Plot"]) > 0:
                    plot_api_node   = req["MLAlgo"]["Plot"]
                    if "PlotType" in plot_api_node:
                        plot_type       = str(plot_api_node["PlotType"])
                    if "ShowPlot" in plot_api_node:
                        show_plot       = bool(plot_api_node["ShowPlot"])
                    if "XAxisTitle" in plot_api_node:
                        x_axis_title    = str(plot_api_node["XAxisTitle"])
                    if "YAxisTitle" in plot_api_node:
                        y_axis_title    = str(plot_api_node["YAxisTitle"])
                    if "MaxFeatures" in plot_api_node:
                        plot_max_features = int(plot_api_node["MaxFeatures"])
                    if "DefaultXAxis" in plot_api_node:
                        default_x_axis  = plot_api_node["DefaultXAxis"] # Series
                    if "DefaultYAxis" in plot_api_node:
                        default_y_axis  = plot_api_node["DefaultYAxis"] # Series
                    if "Debug" in plot_api_node:
                        plot_debug      = bool(plot_api_node["Debug"])
            # end of processing Plot api
            
            self.lg("Building predictors", 6)
            predictors              = [x for x in req["FeaturesTrain"].columns if x not in [target_column_name] ]
            self.lg("Predictors(" + str(len(predictors)) + ") Building XGB Regressor", 6)

            model                   = None

            if use_model_cache:
            
                ra_name             = req["ModelCache"]["RLoc"].split(":")[0]
                ra_key              = req["ModelCache"]["RLoc"].split(":")[1]

                cached_model_req    = {
                                        "RAName"    : str(ra_name),
                                        "RAKey"     : str(ra_key)
                                    }

                self.lg("Getting Model(" + str(ra_key) + ") from Cache", 6)

                model_results       = self.ml_get_single_model_from_cache(cached_model_req, rds, dbs, debug)

                if model_results["Model"] == None or model_results["Model"] == "":
                    err_msg         = "Did not find a valid Model(" + str(ra_key) + ") Key(" + str(ra_key) + ") RLoc(" + str(ra_name) + ":" + str(ra_key) + ")"
                    return self.handle_display_error(err_msg, record, True)
                else:
                    self.lg("Found Model(" + str(ra_key) + ") from Cache", 6)
                    model           = model_results["Model"]
                # end of if the found the model
            else:
                #
                # Here's the supported api variables from 11/17/2016 build:
                #
                # https://github.com/dmlc/xgboost/blob/c52b2faba4d070fb6fe9e0f8fcda34f296522230/python-package/xgboost/sklearn.py#L332
                model               = XGBRegressor(learning_rate=learning_rate,
                                            n_estimators        = num_estimators,
                                            objective           = objective,
                                            max_depth           = max_depth,
                                            max_delta_step      = max_delta_step,
                                            min_child_weight    = min_child_weight,
                                            gamma               = gamma,
                                            subsample           = subsample,
                                            colsample_bytree    = colsample_by_tree,
                                            colsample_bylevel   = colsample_by_level,
                                            reg_alpha           = reg_alpha,
                                            reg_lambda          = reg_lambda,
                                            base_score          = base_score,
                                            nthread             = nthread,
                                            scale_pos_weight    = scale_pos_weight,
                                            silent              = silent,
                                            seed                = seed)
            # end of if out of cache or train a new one

            self.lg("Training Regressor", 6)
            if cv_enabled:
            
                self.lg("Getting XGB Params", 6)
                xgb_param           = model.get_xgb_params()
                self.lg("Building DMatrix for Target(" + str(req["TargetColumnName"]) + ")", 6)

                xg_training_dmatrix = xgb.DMatrix(req["FeaturesTrain"].values, label=req["TargetTrain"].values)

                self.lg("Building CV", 6)
                #cvresult            = xgb.cv(params=xgb_param, 
                #                                dtrain                  = xg_training_dmatrix, 
                #                                metrics                 = cv_metrics, 
                #                                num_boost_round         = cv_num_boost_rounds,
                #                                nfold                   = cv_num_folds,
                #                                stratified              = cv_stratified,
                #                                folds                   = cv_folds, 
                #                                seed                    = cv_seed, 
                #                                early_stopping_rounds   = cv_early_stopping_rounds, 
                #                                verbose_eval            = cv_verbose_eval)
                self.lg("Setting the model's params", 6)
                #model.set_params(n_estimators=cvresult.shape[0])
            #end of building the cv
                
            if use_model_cache:
                self.lg("Model already trained and fit", 6)
            else:
                self.lg("Fitting XGB - Features(" + str(len(req["TrainFeatureNames"])) \
                                        + ") TargetColumn(" + str(req["TargetColumnName"]) \
                                        + ") Train(" + str(len(req["FeaturesTrain"])) \
                                        + ") Test(" + str(len(req["FeaturesTest"])) \
                                        + ") Target Train(" + str(len(req["TargetTrain"])) \
                                        + ") Test(" + str(len(req["TargetTest"])) \
                                        + ")", 6)

                model.fit(  X                       = req["FeaturesTrain"], 
                            y                       = req["TargetTrain"],
                            eval_set                = eval_set,
                            eval_metric             = eval_metric,
                            early_stopping_rounds   = early_stopping_rounds,
                            verbose                 = fit_debug)
            # end of using cache or newly-built model object

            self.lg("Predicting Values", 6)
            #Predict training set:
            predictions             = model.predict(req["FeaturesTest"],
                                                output_margin   = pred_output_margin,
                                                ntree_limit     = pred_ntree_limit)

            predictions_df          = pd.DataFrame({
                                        "index"         : req["FeaturesTest"].index,
                                        "TargetTest"    : req["TargetTest"].values,
                                        "Prediction"    : predictions
                                    }).sort_values(by="index").set_index("index")

            #Print model report:
            self.lg("Scoring Model with FeaturesTest and TargetTest", 6)
            lg("Building Accuracy", 6)
            accuracy                = None
            try:
                accuracy            = model.score(req["FeaturesTest"], req["TargetTest"])
            except Exception,x:
                self.lg("Unable to build Accuracy for TargetColumnName(" + str(req["TargetColumnName"]) + ")", 6)
            
            max_prediction          = predictions.max()
            min_prediction          = predictions.min()
            rankings                = []
            
            self.lg("Predictions(" + str(len(predictions)) + ") Max(" + str(max_prediction) + ") Min(" + str(min_prediction) + ") Accuracy(" + str(accuracy) + ") Rankings(" + str(len(rankings)) + ")", 6)

            record["TargetColumnName"] = str(req["TargetColumnName"])
            record["MLAlgoName"]    = str(req["MLAlgo"]["Name"])
            record["FeatureNames"]  = req["TrainFeatureNames"]
            record["Accuracy"]      = accuracy
            record["CVResults"]     = None
            record["PredictionAPI"] = predict_api_node
            record["ProbaPredAPI"]  = predictproba_api_node
            record["Predictions"]   = predictions
            record["PredictionsDF"] = predictions_df
            record["ProbaPredsDF"]  = None
            record["Model"]         = model
            record["Rankings"]      = rankings
            record["AUROC"]         = None      # http://scikit-learn.org/stable/modules/model_evaluation.html - No AUROC on a regression
        
            #Choose all predictors except target & IDcols
            results                 = self.build_def_hash(status, err_msg, record)

        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to run XGB Regressor with Ex(" + str(k) + ")"
            print err_msg
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of ml_regression_run_xgb

    
    def ml_build_newest_prediction_with_model(self, req, date_col="Date", future_date_col="FDate", debug=False):

        prediction_mask     = req["PredictionMask"]
        predict_newest      = req["SourceDF"][prediction_mask].sort_values(by="Date", ascending=True).iloc[-1]
        train_features      = req["FeatureNames"]
        target_column       = req["TargetColumnName"]

        source_date         = predict_newest[date_col]
        prediction_date     = predict_newest[future_date_col]

        if debug:
            print "Current Date(" + str(source_date) + ") Predicting(" + str(prediction_date) + ")"

        prediction_value    = None
        feature_test_row    = predict_newest.loc[train_features]
        samples_df          = req["SourceDF"].loc[prediction_mask]
        feature_test_df     = samples_df.sort_values(by="Date", ascending=True)[train_features]
        target_test_df      = samples_df.sort_values(by="Date", ascending=True)[target_column]

        # test= [1,2,3,4,5,6,7,8] since it's date sorted make sure to slice it the right way
        # print test[-1:]
        # [8]
        feature_test_row    = feature_test_df[-1:]
        target_test_row     = target_test_df[-1:]

        if req["MLAlgoName"] == "xgb-regressor":
            predictions     = req["Model"].predict(feature_test_row,
                                        output_margin   = req["PredictionAPI"]["OutputMargin"],
                                        ntree_limit     = req["PredictionAPI"]["NumTreeLimit"])

            prediction_value = predictions[-1]
        else:
            self.lg("ERROR: Unsupported Predictor(" + str(req["MLAlgoName"]) + ")", 0)
            self.lg("ERROR: Unsupported Predictor(" + str(req["MLAlgoName"]) + ")", 0)
            self.lg("ERROR: Unsupported Predictor(" + str(req["MLAlgoName"]) + ")", 0)
            
        if prediction_value != None:
            if debug:
                print "ML Model is Predicting(" + str(prediction_date) + ") '" + str(target_column) + "' will be: " + str(prediction_value)
        else:
            print "FAILED to Predict Date(" + str(source_date) + ") Predicting(" + str(prediction_date) + ")"

        marker              = {
                                "Date"              : source_date.strftime("%Y-%m-%d %H:%M:%S"),
                                "PredictionDate"    : prediction_date.strftime("%Y-%m-%d %H:%M:%S"),
                                "PredictionValue"   : prediction_value,
                                "PredictionAPI"     : req["PredictionAPI"],
                                "ProbaPredAPI"      : req["ProbaPredAPI"],
                                "FeatureTestRow"    : feature_test_row,
                                "TargetTestRow"     : target_test_row
                            }

        return marker
    # end of ml_build_newest_prediction_with_model


    def ml_determine_model_prediction(self, req, debug=False):

        predict_row_df      = req["PredictRow"]
        prediction_mask     = req["PredictionMask"]
        train_features      = req["FeatureNames"]
        target_column       = req["TargetColumnName"]

        lg("Determine Model Prediction", 6)

        prediction_value    = None
        feature_test_row    = predict_row_df
        feature_test_df     = predict_row_df[train_features]
        target_test_df      = predict_row_df[target_column]

        # test= [1,2,3,4,5,6,7,8] since it's date sorted make sure to slice it the right way
        # print test[-1:]
        # [8]
        feature_test_row    = feature_test_df
        target_test_row     = target_test_df

        if req["MLAlgoName"] == "xgb-regressor":
            predictions     = req["Model"].predict(feature_test_row,
                                        output_margin   = req["PredictionAPI"]["OutputMargin"],
                                        ntree_limit     = req["PredictionAPI"]["NumTreeLimit"])

            prediction_value = predictions[-1]

        elif req["MLAlgoName"] == "xgb-classifier":
            predictions     = req["Model"].predict(feature_test_row,
                                        output_margin   = req["PredictionAPI"]["OutputMargin"],
                                        ntree_limit     = req["PredictionAPI"]["NumTreeLimit"])

            prediction_value = predictions[-1]
        else:
            self.lg("ERROR: Unsupported Predictor(" + str(req["MLAlgoName"]) + ")", 0)
            self.lg("ERROR: Unsupported Predictor(" + str(req["MLAlgoName"]) + ")", 0)
            self.lg("ERROR: Unsupported Predictor(" + str(req["MLAlgoName"]) + ")", 0)
            
        if prediction_value != None:
            if debug:
                print "ML Model is Predicting(" + str(prediction_date) + ") '" + str(target_column) + "' will be: " + str(prediction_value)
        else:
            lg("ERROR: FAILED to Predict(" + str(predict_row_df) + ")", 0)

        now                 = datetime.datetime.now()

        marker              = {
                                "Date"              : now.strftime("%Y-%m-%d %H:%M:%S"),
                                "PredictionValue"   : prediction_value,
                                "PredictionAPI"     : req["PredictionAPI"],
                                "ProbaPredAPI"      : req["ProbaPredAPI"],
                                "TargetColumnName"  : target_column,
                                "FeatureTestRow"    : feature_test_row,
                                "TargetTestRow"     : target_test_row
                            }

        return marker
    # end of ml_determine_model_prediction


    def ml_return_prediction_dates(self, simulated_date, ahead_set, ahead_type, rds, dbs, debug=False):

        import pandas as pd
        from pandas.tseries.offsets import BDay

        prediction_dates        = {}
        for n in ahead_set:

            if ahead_type == "Days":
                new_prediction_date = simulated_date + BDay(int(n))
                new_node            = {
                                        "Date"          : new_prediction_date.date(),
                                        "Timestamp"     : new_prediction_date,
                                        "Ahead"         : int(n)
                                    }
                prediction_dates[str(n)] = new_prediction_date
            # just get a simple dict of prediction dates
        # end of all units in ahead_set

        return prediction_dates
    # end of ml_return_prediction_dates


    def ml_get_training_base_dir(self, dataset_name, debug=False):

        basedir_path        =  os.getenv("ENV_SYNTHESIZE_DIR", "/opt/work/data/src")

        # Prob want to sync these with a common s3 location in the future:
        if self.running_on_aws():
            basedir_path    =  os.getenv("ENV_SYNTHESIZE_DIR", "/opt/work/data/src")
            
        return basedir_path
    # end of ml_get_training_base_dir


    #####################################################################################################
    #
    # Seaborn Methods
    #
    #####################################################################################################


    def sb_initialize_fonts(self, font_size=12, title_size=12, label_size=10):
        import seaborn as sns
        sns.set_context("paper", rc={"font.size":font_size,"axes.titlesize":title_size,"axes.labelsize":label_size})
    # end of sb_initialize_fonts


    def sb_model_feature_importance(self, req, debug=False):
    
        image_list      = []
        image_filename  = req["ImgFile"]
        ml_model        = req["Model"]
        x_label         = req["XLabel"]
        y_label         = req["YLabel"]
        plot_title      = req["Title"]
        max_features    = -1
        cur_xlabel      = "Dates"
        cur_width       = 15.0
        cur_height      = 15.0

        if "MaxFeatures" in req:
            max_features= int(req["MaxFeatures"])
        if "XLabel" in req:
            cur_xlabel  = str(req["XLabel"])
        if "Width" in req:
            cur_width   = float(req["Width"])
        if "Height" in req:
            cur_height  = float(req["Height"])

        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns

        series_feat_imp = pd.Series(ml_model.booster().get_fscore()).sort_values(ascending=False).iloc[0:max_features]
        df_feat_imp     = pd.DataFrame({x_label : series_feat_imp.index, y_label : series_feat_imp.values})
        
        plt.figure(figsize=(cur_width, cur_height))
        ax              = sns.barplot(  x           = x_label, 
                                        y           = y_label, 
                                        hue         = x_label, 
                                        data        = df_feat_imp, 
                                        palette     = "Set1", 
                                        linewidth   = 0.5)
        ax.figure.suptitle(plot_title)
        self.pd_add_footnote(ax.figure)
        ax.set(xlabel=x_label, ylabel=y_label)
        sns.plt.legend(loc='best')

        if image_filename != "":
            if debug:
                self.lg("Saving File(" + str(image_filename) + ")", 6)
            fig = ax.get_figure()
            fig.savefig(image_filename)

            if os.path.exists(image_filename) == False:
                err_msg = "Failed to save image file(" + str(image_filename) + ")"
                lg("WARNING: " + str(err_msg), 1)
            else:
                image_list.append(image_filename)
                if debug:
                    lg("Saved File: " + str(image_filename), 6)
            # end of if the image file was saved
        # end of if image file

        if req["ShowPlot"] == True:
            plt.show()

        return image_list
    # end of sb_model_feature_importance


    def sb_plot_xgb_regression_line(self, prediction_df, x_col_name, x_label, y_label, target_label, prediction_label, plot_title, image_filename="", show_plot=False, debug=False):

        image_list      = []

        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        sns.set_style("whitegrid", {'axes.grid' : True})
        sns.color_palette("Set1", n_colors=8, desat=.5)

        fig, ax         = plt.subplots(figsize=(15.0, 10.0))
        
        target_plot     = plt.plot(prediction_df[x_col_name], prediction_df["TargetTest"], label=target_label, color=self.pd_get_color_from_id(0))
        prediction_plot = plt.plot(prediction_df[x_col_name], prediction_df["Prediction"], label=prediction_label, color=self.pd_get_color_from_id(2))

        ax.set_title(plot_title)

        self.pd_add_footnote(ax.figure)
        ax.set(xlabel=x_label, ylabel=y_label)

        leg = plt.legend(handles=[target_plot[0], prediction_plot[0]], loc="best", frameon=True)
        leg.get_frame().set_edgecolor("#696969")
        leg.get_frame().set_linewidth(2)

        if show_plot:
            plt.show()

        if image_filename != "":
            if debug:
                self.lg("Saving File(" + str(image_filename) + ")", 6)
            fig = ax.get_figure()
            fig.savefig(image_filename)

            if os.path.exists(image_filename) == False:
                err_msg = "Failed to save image file(" + str(image_filename) + ")"
                lg("WARNING: " + str(err_msg), 1)
            else:
                image_list.append(image_filename)
                if debug:
                    lg("Saved File: " + str(image_filename), 6)
            # end of if the image file was saved
        # end of if image file

        return image_list
    # end of sb_plot_xgb_regression_line


    def sb_plot_predictions(self, req, debug=False):
            
        image_list      = []

        image_filename  = req["ImgFile"]

        import seaborn as sns 
        import numpy as np
        from matplotlib import pyplot
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.patches import Rectangle
        from matplotlib.finance import volume_overlay
        import pandas as pd
        from pandas.tseries.offsets import BDay

        predictions_df  = req["PredictionsDF"]
        ds_name         = req["DSName"]

        sns.set_style("whitegrid", {'axes.grid' : True})
        sns.color_palette("Set1", n_colors=8, desat=.5)

        cur_xlabel      = "Dates"
        cur_width       = 15.0
        cur_height      = 15.0

        if "XLabel" in req:
            cur_xlabel  = str(req["XLabel"])
        if "Width" in req:
            cur_width   = float(req["Width"])
        if "Height" in req:
            cur_height  = float(req["Height"])

        fig, ax     = plt.subplots(figsize=(cur_width, cur_height))

        # Add custom plots here

        for plot_idx,plot_node in enumerate(req["Predictions"]):

            x_axis  = plot_node["XCol"]
            y_axis  = plot_node["YCol"]
            label   = plot_node["Label"]
            color   = self.pd_get_color_from_id(plot_idx)
            alpha   = 1.0
            if "Color" in plot_node:
                color   = self.pd_get_color(plot_node["Color"])
            if "Alpha" in plot_node:
                alpha   = float(plot_node["Alpha"])

            ax.plot(predictions_df[x_axis], predictions_df[y_axis], label=label, color=color, alpha=alpha)
        # end of for all plots

        plt.grid(True)
        plt.xlabel("Dates")
        plt.ylabel(ds_name + " Targets")

        # Build a Date title
        start_date = str(predictions_df.iloc[0]["Date"].strftime('%Y-%m-%d'))
        end_date   = str(predictions_df.iloc[-1]["Date"].strftime('%Y-%m-%d'))
        ax.set_title(ds_name + " Predictions from " + str(start_date) + " to " + str(end_date))

        # Merge in the second axis (Volume) Legend
        handles, labels = pyplot.gca().get_legend_handles_labels()
        newLabels, newHandles = [], []
        for handle, label in zip(handles, labels):
            if label not in newLabels:
                newLabels.append(label)
                newHandles.append(handle)

        lines           = ax.get_lines() + newHandles
        unique_labels   = []
        already_stored  = {}
        for l in lines:
            new_label   = str(l.get_label())
            if str(new_label) not in already_stored:
                unique_labels.append(l)
                already_stored[str(new_label)] = True
        # end of building list

        leg = plt.legend(handles=unique_labels, loc="best", frameon=True)
        leg.get_frame().set_edgecolor("#696969")
        leg.get_frame().set_linewidth(2)

        # Build out the xtick chart by the dates
        ax.xaxis.grid(True, which='minor')
        xfmt = mdates.DateFormatter('%Y-%m-%d')
        ax.xaxis.set_major_formatter(xfmt)
        ax.xaxis.set_minor_formatter(xfmt)

        xtick       = predictions_df["Date"].tolist()
        xticklabels = [dt.strftime("%b-%d") for dt in xtick]
        ax.set_xticks( xtick, minor=False )
        ax.set_xticklabels( xticklabels, rotation=90, minor=False )

        self.lg("Saving File(" + str(image_filename) + ")", 6)
        fig = ax.get_figure()
        fig.savefig(image_filename)
        image_list.append(image_filename)

        if req["ShowPlot"] == True:
            plt.show()

        return image_list
    # end of sb_plot_predictions


    def sb_plot_all_predictive_accuracy(self, req, debug=False):

        images_list                 = []
        pk_show_plot                = bool(req["ShowPlot"])
        ds_name                     = str(req["DSName"]).replace(" ", "-")
        units_ahead_type            = str(req["UnitsAheadType"])
        
        label_suffix                = ""
        x_column_name               = "Date"
        x_column_label              = "Date"

        if "XColName" in req:
            x_column_name           = str(req["XColName"])
        if "XColLabel" in req:
            x_column_label          = str(req["XColLabel"])
        if "LabelSuffix" in req:
            label_suffix            = str(req["LabelSuffix"])

        if len(req["AccuracyResults"]) > 0:

            for key_name in req["AccuracyResults"]:
                split_type          = key_name.split("_")
                key_type            = str(split_type[0])
                cur_units_ahead     = str(split_type[1])
                dataset_to_plot     = req["AccuracyResults"][key_name]
                logical_name        = key_name.replace("_", " ")[1:] + " " + str(units_ahead_type)
                acc_image_name      = "/tmp/" + str(ds_name) + "-" + str(key_name) + "-Prediction-Accuracy.png"
                if os.path.exists(acc_image_name):
                    os.system("rm -f " + str(acc_image_name))

                self.lg("Plotting Regression Forecast with Accuracy(" + str(key_name) + ") ImageFile(" + str(acc_image_name) + ")", 6)
                pred_df             = self.ml_regression_build_prediction_results_df(dataset_to_plot["PredictionsDF"], dataset_to_plot["SourceDF"], "index")
                # Build the prediction results
                pred_x_col_name     = x_column_name
                pred_x_label        = x_column_label
                pred_y_col_name     = logical_name
                pred_y_label        = logical_name
                if label_suffix != "":
                    pred_y_col_name = logical_name + " " + str(label_suffix)
                    pred_y_label    = logical_name + " " + str(label_suffix)

                pred_target_label   = "Actual " + str(logical_name)
                pred_label          = "Predicted " + str(logical_name) + " " + str(cur_units_ahead) + " " + str(units_ahead_type) + " ahead"
                pred_plot_title     = ds_name + " " + str(cur_units_ahead) + "-" + str(units_ahead_type) + " - Predictive Accuracy\nPredicted " + str(logical_name) + " vs Actual " + str(logical_name)
                if label_suffix != "":
                    pred_plot_title = ds_name + " " + str(cur_units_ahead) + "-" + str(units_ahead_type) + " - Predictive Accuracy\nPredicted " + str(logical_name) + " " + str(label_suffix) + " vs Actual " + str(logical_name) + " " + str(label_suffix) 

                self.sb_plot_xgb_regression_line(pred_df.iloc[-250:], pred_x_col_name, pred_x_label, pred_y_label, pred_target_label, pred_label, pred_plot_title, acc_image_name, pk_show_plot)

                images_list.append(acc_image_name)
            # for all nodes in the list, try to plot the regression lines to showcase the predictiveness
        # if there's more than one

        return images_list
    # end of sb_plot_all_predictive_accuracy


    def sb_confusion_matrix(self, req, debug=False):
            
        image_list      = []

        image_filename  = req["ImgFile"]

        import seaborn as sns 
        import numpy as np
        from matplotlib import pyplot
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.patches import Rectangle
        from matplotlib.finance import volume_overlay
        import pandas as pd
        from pandas.tseries.offsets import BDay

        source_df       = req["SourceDF"]
        ds_name         = req["DSName"]

        sns.set_style("whitegrid", {'axes.grid' : True})
        sns.color_palette("Set1", n_colors=8, desat=.5)

        cur_xlabel      = "Dates"
        cur_ylabel      = "Value"
        cur_width       = 15.0
        cur_height      = 15.0
        cur_title       = ds_name + " Confusion Matrix"
        if "XLabel" in req:
            cur_xlabel  = str(req["XLabel"])
        if "YLabel" in req:
            cur_xlabel  = str(req["YLabel"])
        if "Width" in req:
            cur_width   = float(req["Width"])
        if "Height" in req:
            cur_height  = float(req["Height"])
        if "Title" in req:
            cur_title   = str(req["Title"])
        # end of parsing inputs

        # Add custom plots here

        for cm_node in req["ConfMatrices"]:

            target_col      = str(cm_node["TargetColumnName"])
            ax              = cm_node["CM"].plot()
            plt.title(cur_title + " - " + str(target_col))
            self.pd_add_footnote(ax.get_figure())

            new_suffix      = "_" + target_col + "_" + str(cm_node["ID"]) + ".png"
            save_filename   = image_filename.replace(".png", new_suffix)

            fig = ax.get_figure()
            fig.savefig(save_filename)
            image_list.append(save_filename)

            if req["ShowPlot"] == True:
                plt.show()
        # end of for all confusion matrices

        return image_list
    # end of sb_confusion_matrix


    def sb_pairplot(self, req, debug=False):

        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns

        image_filename  = req["ImgFile"]
        image_list      = []

	width       	= 10.0
	height      	= 10.0
	plot_title  	= "PairPlot"
	style       	= "default"
        x_label         = ""
        y_label         = ""
        plot_palette    = "Set2"
        col_targets     = {
                            "0" : "Good",
                            "1" : "Bad"
                        }
        hue_targets     = {
                            "0" : "Unknown",
                        }

        hue_column_name = ""
        col_column_name = ""
        map_type        = "scatter"
        x_col_name      = ""
        y_col_name      = ""
        kind            = "reg"
        diag_kind       = "hist"
        hue_order       = None
        markers         = None
        aspect          = 1
        drop_na         = False
        size            = 2.5
        plot_columns    = []
        cur_width       = 7.0
        cur_height      = 7.0

        if "Width" in req:
            cur_width   = float(req["Width"])
        if "Height" in req:
            cur_height  = float(req["Height"])
        if "Title" in req:
            plot_title  = str(req["Title"])
        if "Style" in req:
            style       = str(req["Style"])
        if "XLabel" in req:
            x_label     = str(req["XLabel"])
        if "YLabel" in req:
            y_label     = str(req["YLabel"])
        if "Size" in req:
            size        = float(req["Size"])
        if "Palette" in req:
            plot_palette= str(req["Palette"])
        if "HueColumnName" in req:
            hue_column_name= str(req["HueColumnName"])
        if "ColColumnName" in req:
            col_column_name= str(req["ColColumnName"])
        if "MapType" in req:
            map_type    = str(req["MapType"])
        if "ColTargetDict" in req:
            col_targets = req["ColTargetDict"]
        if "HueTargetDict" in req:
            hue_targets = req["HueTargetDict"]
        if "XColumnName" in req:
            x_col_name  = str(req["XColumnName"])
        if "YColumnName" in req:
            y_col_name  = str(req["YColumnName"])
        if "PlotKind" in req:
            kind        = str(req["PlotKind"])
        if "DiagKind" in req:
            diag_kind   = str(req["DiagKind"])
        if "HueOrder" in req:
            if len(req["HueOrder"]) > 0:
                hue_order   = req["HueOrder"]
            else:
                hue_order   = None
        if "Markers" in req:
            if len(req["Markers"]) > 0:
                markers = req["Markers"]
            else:
                markers = None
        if "Aspect" in req:
            aspect      = req["Aspect"]
        if "DropNA" in req:
            drop_na     = bool(req["DropNA"])
        if "CompareColumns" in req:
            plot_columns= req["CompareColumns"]

        # Start Processing Request 

        if style == "default":
            #sns.set_context("poster")
            sns.color_palette("Set2", 10)
            sns.axes_style("darkgrid")

        max_col         = 4
        num_fts         = len(plot_columns)
        max_plots       = int(num_fts / max_col) 
        max_plot_idx    = max_plots + 1
        start_idx       = 0
        ahead_idx       = (start_idx + max_col)
        plot_idx        = 1
        if max_plots == 0:
            max_plots   = 1
            plot_idx    = 0

        for i in range(max_plots):
            stop        = False
            if ahead_idx > num_fts:
                stop        = True
                ahead_idx   = -1
    
            sub_fts         = plot_columns[start_idx:ahead_idx]
    
            start_idx       += max_col
            ahead_idx       = (start_idx + max_col) 

            found_in_list   = False
            for node in sub_fts:
                if str(hue_column_name) == node:
                    found_in_list   = True

            if not found_in_list:
                if hue_column_name != "":
                    sub_fts.append(hue_column_name)
            
            if len(sub_fts) > 0:

                self.sb_initialize_fonts(12, 12, 12)
                grid = sns.pairplot(data        = req["SourceDF"][sub_fts], 
                                    hue         = hue_column_name,
                                    palette     = plot_palette,
                                    markers     = markers,
                                    dropna      = True,
                                    kind        = kind,
                                    diag_kind   = diag_kind,
                                    size        = size)

                #sns.plt.legend(loc='best')
                sub_plot_title   = "Analysis(" + str(plot_idx) + "/" + str(max_plot_idx-1) + "): " + str(json.dumps(sub_fts)).replace("[", "").replace("]", "")
                if plot_title == "":
                    grid.fig.suptitle(sub_plot_title)
                else:
                    grid.fig.suptitle(plot_title)

                grid.fig.get_children()[-1].set_bbox_to_anchor((1.1, 0.5, 0, 0))
                self.pd_add_footnote(grid.fig)

                if max_plots == 1:
                    save_filename   = image_filename
                else:
                    new_suffix      = "_" + str(plot_idx) + ".png"
                    save_filename   = image_filename.replace(".png", new_suffix)

                grid.fig.set_figwidth(cur_width)
                grid.fig.set_figheight(cur_height)

                grid.fig.savefig(save_filename)
                image_list.append(save_filename)

                if req["ShowPlot"] == True:
                    plt.show()

            plot_idx    += 1

            if stop:
                break
        # end of all features

        return image_list
    # end of sb_pairplot


    def sb_scatter(self, req, debug=False):
            
        image_list      = []

        image_filename  = req["ImgFile"]

        import seaborn as sns 
        import numpy as np
        from matplotlib import pyplot
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.patches import Rectangle
        from matplotlib.finance import volume_overlay
        import pandas as pd
        from pandas.tseries.offsets import BDay

        source_df       = req["SourceDF"]
        ds_name         = req["DSName"]

        sns.set_style("whitegrid", {'axes.grid' : True})
        sns.color_palette("Set1", n_colors=8, desat=.5)

        cur_xlabel      = "measurement"
        cur_ylabel      = "value"
        cur_hue         = "ResultLabel"
        cur_width       = 10.0
        cur_height      = 10.0
        if "X" in req:
            cur_xlabel  = str(req["X"])
        if "Y" in req:
            cur_ylabel  = str(req["Y"])
        if "Width" in req:
            cur_width   = float(req["Width"])
        if "Height" in req:
            cur_height  = float(req["Height"])
        if "Hue" in req:
            cur_hue     = str(req["Hue"])
        # end of parsing inputs

        # Add custom plots here

        plt.figure(figsize=(cur_width, cur_height))
        ax              = sns.swarmplot(x=cur_xlabel, y=cur_ylabel, hue=cur_hue, data=source_df)

        if debug:
            self.lg("Saving File(" + str(image_filename) + ")", 6)

        self.pd_add_footnote(ax.figure)
        ax.figure.savefig(image_filename)
        image_list.append(image_filename)

        if req["ShowPlot"] == True:
            plt.show()

        return image_list
    # end of sb_scatter

    
    def sb_all_scatterplots(self, req, debug=False):

        org_image_filename  = req["ImgFile"]
        feature_column_names= req["FeatureColumnNames"]
        image_list          = []
        plot_idx            = 0
        already_done        = {}
        for cur_x in feature_column_names:
            for cur_y in feature_column_names:
                if cur_x != cur_y and cur_x not in already_done:
                    new_suffix          = "_" + str(plot_idx) + ".png"
                    save_filename       = org_image_filename.replace(".png", new_suffix)

                    new_req             = req
                    new_req["X"]        = cur_x
                    new_req["Y"]        = cur_y
                    new_req["ImgFile"]  = save_filename
                    new_req["SourceDF"] = req["SourceDF"]
                    new_req["ShowPlot"] = req["ShowPlot"]
                    new_req["DSName"]   = req["DSName"]

                    new_images          = self.sb_scatter(new_req, debug)
                    for new_img in new_images:
                        image_list.append(new_img)
        
                    already_done[cur_x] = True
                    plot_idx        += 1
                # end for all names that are not the same
            # end for all y
        # end for all x
                
        return image_list
    # end of sb_all_scatterplots


    def sb_jointplot(self, req, debug=False):
            
        image_list      = []

        image_filename  = req["ImgFile"]

        import seaborn as sns 
        import numpy as np
        from matplotlib import pyplot
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.patches import Rectangle
        from matplotlib.finance import volume_overlay
        import pandas as pd
        from pandas.tseries.offsets import BDay

        source_df       = req["SourceDF"]
        ds_name         = req["DSName"]

        sns.set_style("whitegrid", {'axes.grid' : True})
        sns.color_palette("Set1", n_colors=8, desat=.5)

        cur_xlabel      = "measurement"
        cur_ylabel      = "value"
        cur_kind        = "reg"
        cur_width       = 15.0
        cur_height      = 15.0
        if "X" in req:
            cur_xlabel  = str(req["X"])
        if "Y" in req:
            cur_ylabel  = str(req["Y"])
        if "Width" in req:
            cur_width   = float(req["Width"])
        if "Height" in req:
            cur_height  = float(req["Height"])
        if "Kind" in req:
            cur_kind    = str(req["Kind"])
        # end of parsing inputs

        # Add custom plots here

        grid            = sns.jointplot(cur_xlabel, cur_ylabel, kind=cur_kind, data=source_df, annot_kws=dict(stat="r"))

        if debug:
            self.lg("Saving File(" + str(image_filename) + ")", 6)
                
        grid.fig.set_figwidth(cur_width)
        grid.fig.set_figheight(cur_height)

        ax              = grid.ax_joint
        self.pd_add_footnote(ax.figure)
        ax.figure.savefig(image_filename)
        image_list.append(image_filename)

        if req["ShowPlot"] == True:
            plt.show()

        return image_list
    # end of sb_jointplot

    
    def sb_all_jointplots(self, req, debug=False):

        org_image_filename  = req["ImgFile"]
        feature_column_names= req["FeatureColumnNames"]
        image_list          = []
        plot_idx            = 0
        already_done        = {}
        for cur_x in feature_column_names:
            for cur_y in feature_column_names:
                if cur_x != cur_y and cur_x not in already_done:
                    new_suffix          = "_" + str(plot_idx) + ".png"
                    save_filename       = org_image_filename.replace(".png", new_suffix)

                    new_req             = req
                    new_req["X"]        = cur_x
                    new_req["Y"]        = cur_y
                    new_req["ImgFile"]  = save_filename
                    new_req["SourceDF"] = req["SourceDF"]
                    new_req["ShowPlot"] = req["ShowPlot"]
                    new_req["DSName"]   = req["DSName"]

                    new_images          = self.sb_jointplot(new_req, debug)
                    for new_img in new_images:
                        image_list.append(new_img)
        
                    already_done[cur_x] = True
                    plot_idx        += 1
                # end for all names that are not the same
            # end for all y
        # end for all x
                
        return image_list
    # end of sb_all_jointplots


    #####################################################################################################
    #
    # Scikit Methods
    #
    #####################################################################################################


    def sk_synthesize_train_and_test_data_from_pd(self, ml_type, train_feature_names, source_df, target_column_name, filter_by_mask, org_test_ratio, rds, dbs):

        record              = {
                                "TrainFeatures" : [],
                                "TrainColName"  : target_column_name,
                                "SamplesDF"     : None,
                                "FeatureTrain"  : None,
                                "FeatureTest"   : None,
                                "TargetTrain"   : None,
                                "TargetTest"    : None
                            }
        test_ratio          = org_test_ratio
        if org_test_ratio > 1:
            test_ratio      = org_test_ratio / 100.0

        results             = self.build_def_hash("Display Error", "Not Run", record )

        try:

            import numpy as np
            import pandas as pd 

            self.lg("Building Training Data ML(" + str(ml_type) + ") Features(" + str(len(train_feature_names)) + ") Rows(" + str(len(source_df.index)) + ") Train(" + str(target_column_name) + ") Ratio(" + str(test_ratio) + ") Filter(" + str(filter_by_mask)[0:10] + ")", 6)

            total_rows                      = len(source_df.index)

            if total_rows > 2:
                num_train                   = int(total_rows * float(test_ratio)) + 1
                num_test                    = int(total_rows) - int(num_train)
                self.lg("SK - Train Breakdown(" + str(num_train) + "/" + str(total_rows) + ") Test(" + str(num_test) + ")", 6)

                if num_train < total_rows:

                    from sklearn.cross_validation import train_test_split

                    # Now break it all up:
                    samples_df              = source_df.loc[filter_by_mask]
                    test                    = samples_df[target_column_name]
                    train                   = samples_df[train_feature_names]

                    feature_train, feature_test, target_train, target_test = train_test_split(train, test, test_size=0.44, random_state=42)

                    record["TrainFeatures"] = train_feature_names
                    record["TrainColName"]  = target_column_name
                    record["SamplesDF"]     = samples_df
                    record["FeatureTrain"]  = feature_train
                    record["FeatureTest"]   = feature_test
                    record["TargetTrain"]   = target_train 
                    record["TargetTest"]    = target_test

                    results                 = self.build_def_hash("SUCCESS", "", record)
                else:
                    self.lg("ERROR: NumTrain(" + str(num_train) + ") cannot be more than the Total(" + str(total_rows) + ") Train(" + str(total_rows) + ")", 6)
                    results                 = self.build_def_hash("Display Error", "Failed to build train set from less than 2 rows", record)
                # end of if/else
            else:
                self.lg("ERROR: Invalid Rows to Train(" + str(total_rows) + ")", 6)
                results                     = self.build_def_hash("Display Error", "Failed to build train set from less than 2 rows", record)
            # end of if/else
    
        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to Build SK Data set from PD with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of sk_synthesize_train_and_test_data_from_pd


    def sk_generate_random_classification_set(self, samples, features, classes, informative, rds, dbs, debug=False):

        record              = {
                                "Test"  : { 
                                            "X" : {},
                                            "Y" : {}
                                        },
                                "Train" : { 
                                            "X" : {},
                                            "Y" : {}
                                        }
                            }
        results             = self.build_def_hash("Display Error", "Not Run", record )

        try:

            from sklearn.datasets import make_classification

            self.lg("Processing ROC", 6)

            X, Y = make_classification(n_samples=samples, 
                                        n_features=features, 
                                        n_classes=classes, 
                                        n_informative=informative)

            record["Test"]["X"]     = X[9000:] 
            record["Test"]["Y"]     = Y[9000:] 
            record["Train"]["X"]    = X[:9000]
            record["Train"]["Y"]    = Y[:9000]

            results         = self.build_def_hash("SUCCESS", "", record)
    
        except Exception,k:
            status          = "FAILED"
            err_msg         = "Unable to Generate Random Classification set with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            results         = self.build_def_hash("Display Error", err_msg, {})
        # end of try/ex

        return results
    # end of sk_generate_random_classification_set


    def sk_load_csv(self, request_args, rds, dbs):
        record          = {
                            "SourceDF"              : None,
                            "AllFeatures"           : [],
                            "TrainAndTestFeatures"  : [],
                            "TrainFeatures"         : []
                        }

        results         = self.build_def_hash("Display Error", "Not Run", record)

        try:

            import pandas as pd

            ml_type                     = request_args["MLType"]
            target_column_name          = request_args["TargetColumnName"]  # What column is getting processed
            feature_remove_these        = request_args["IgnoreFeatures"]    # Prune non-int/float columns as needed: 
            ml_csv                      = request_args["CSVFile"]
            if os.path.exists(ml_csv) == False:
                err_msg                 = "Failed to find CSV File(" + str(ml_csv) + ")"
                self.lg("ERROR: " + str(err_msg), 0)
                print err_msg
                results                 = self.build_def_hash("Display Error", err_msg, record)
                return results

            source_df                   = pd.read_csv(ml_csv, encoding='utf-8-sig')
            new_feature_names           = source_df.columns.values
            org_feature_names           = []
            fit_feature_names           = []
            debug                       = False
            for fn in new_feature_names:
                add_column              = True
                for ig in feature_remove_these:
                    if str(fn).lower() == str(ig).lower() \
                        or "unnamed: " in str(fn).lower():
                        add_column      = False
                        break
                # end of for all to skip

                if add_column:
                    org_feature_names.append(fn)

                    if str(target_column_name).lower() != str(fn).lower() \
                        and "unnamed: " not in str(fn).lower():
                        fit_feature_names.append(fn)
            # only add those columns that can be changed

            record["SourceDF"]              = source_df
            record["AllFeatures"]           = new_feature_names
            record["TrainAndTestFeatures"]  = org_feature_names
            record["TrainFeatures"]         = fit_feature_names

            if len(source_df.index) > 1:
                results                     = self.build_def_hash("SUCCESS", "", record)
            else:
                results                     = self.build_def_hash("Display Error", "Failed to find more than 1 row in the CSV(" + str(ml_csv) + ")", record)

        except Exception as k:
            err_msg         = "Failed to load CSV(" + str(request_args["CSVFile"]) + ") into df with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            print err_msg
            results         = self.build_def_hash("Display Error", err_msg, record)
        # try/ex

        return results
    # end of sk_load_csv


    def sk_synthesize_dataset_from_csv(self, request_args, rds, dbs):

        record          = {
                            "TrainColName"  : "",
                            "TrainFeatures" : [],
                            "FeatureTrain"  : None,
                            "FeatureTest"   : None,
                            "TargetTrain"   : None,
                            "TargetTest"    : None
                        }

        results         = self.build_def_hash("Display Error", "Not Run", record)

        try:

            ml_type                     = request_args["MLType"]
            target_column_name          = request_args["TargetColumnName"]      # What column is getting processed
            target_column_values        = request_args["TargetColumnValues"]    # possible values each int in the target_column_name maps to
            train_feature_names         = request_args["TrainFeatures"]         # pass in the features to train
            source_df                   = request_args["SourceDF"]
            sample_filter_mask          = request_args["SampleMask"]
            test_ratio                  = float(request_args["TrainToTestRatio"])
            org_feature_names           = []
            fit_feature_names           = []

            self.lg("Synthesize Dataset Rows(" + str(len(source_df.index)) + ")", 6)
            synthesis_results          = self.sk_synthesize_train_and_test_data_from_pd(ml_type,
                                                    train_feature_names,
                                                    source_df,
                                                    target_column_name,
                                                    sample_filter_mask,
                                                    test_ratio,
                                                    rds,
                                                    dbs)

            if synthesis_results["Status"] != "SUCCESS":
                err_msg                 = "Failed to Synthesize dataset with Error(" + str(synthesis_results["Error"]) + ")"
                self.lg("ERROR: " + str(err_msg), 0)
                print err_msg
                results                 = self.build_def_hash("Display Error", err_msg, record)
                return results
            else:

                self.lg("Done Synthesis Building Results", 6)

                train_feature_names     = synthesis_results["Record"]["TrainFeatures"]
                feature_train           = synthesis_results["Record"]["FeatureTrain"]
                feature_test            = synthesis_results["Record"]["FeatureTest"]
                target_train            = synthesis_results["Record"]["TargetTrain"]
                target_test             = synthesis_results["Record"]["TargetTest"]
                samples_df              = synthesis_results["Record"]["SamplesDF"]

                record["TrainColName"]  = target_column_name
                record["SamplesDF"]     = samples_df
                record["TrainFeatures"] = train_feature_names
                record["FeatureTrain"]  = feature_train
                record["FeatureTest"]   = feature_test
                record["TargetTrain"]   = target_train
                record["TargetTest"]    = target_test

                results                 = self.build_def_hash("SUCCESS", "", record)
            # if/else synthesis success
        
        except Exception as k:
            err_msg         = "Failed to build Playbook Dataset with Ex(" + str(k) + ")"
            self.lg("ERROR: " + str(err_msg), 0)
            print err_msg
            results         = self.build_def_hash("Display Error", err_msg, record)
        # try/ex

        return results
    # end of sk_build_playbook_dataset_from_csv


# end of PyCore
