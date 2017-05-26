################################################################
#
# ENV variables in use:
#
# ENV_CORE_CONFIG_FILE - the core configuration file to use
# ENV_RDS_ENABLED - are the redis applications enabled
# ENV_DBS_ENABLED - are the database applications enabled
# ENV_DATA_SRC_DIR - where is the data dir
# ENV_DEPLOYMENT_TYPE - where is this core running local vs aws using /opt/aws/bin/ec2-metadata
# ENV_PY_LOGGER_NAME - name the core uses for logging
#
################################################################


################################################################
#
# Load common imports and system envs
import sys, os, datetime, requests, json, uuid, glob, argparse, copy, logging, time, io
from time import sleep
from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, MetaData, Date, DateTime, Float, cast, or_, and_, asc

from src.common.shellprinting   import *
from src.logger.logger          import Logger
from src.pycore                 import PyCore

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas.io.json         import json_normalize

from IPython.display import Image as ipyImage
from IPython.core.display import HTML as ipyHTML
from IPython.display import display as ipyDisplay

# Set up the ENV
default_env = "Local"
use_env = os.getenv("ENV_DEPLOYMENT_TYPE", default_env)
os.environ["ENV_DEPLOYMENT_TYPE"] = use_env
if os.path.exists("/opt/aws/bin/ec2-metadata"):
    os.environ["ENV_DEPLOYMENT_TYPE"] = "Test"

debug = False
if debug:
    lg("Start common python initialization Env(" + str(os.getenv("ENV_DEPLOYMENT_TYPE")) + ")", 6)

core_config = os.getenv("ENV_CORE_CONFIG_FILE", "/opt/work/configs/jupyter.json")
data_dir = os.getenv("ENV_DATA_SRC_DIR", "/opt/scipype/data/src")
db_enabled = os.getenv("ENV_DBS_ENABLED", "0")
rd_enabled = os.getenv("ENV_RDS_ENABLED", "1")
lg_enabled = os.getenv("ENV_SYSLOG_ENABLED", "0")      # unless your docker daemon has exposed syslog...keep this at 0
logger_name = os.getenv("ENV_PY_LOGGER_NAME", "ds")
env_name = os.getenv("ENV_DEPLOYMENT_TYPE", "Local")

core = PyCore(core_config)
now = datetime.datetime.now()
ra_name = "CACHE"
ra_key = "NODB_PERFORM_THIS_WORK"
logger = None

if str(lg_enabled) == "1" or str(lg_enabled).lower() == "true":
    logger = Logger(logger_name, "/dev/log", logging.DEBUG)

if debug:
    lg("Loading Redis Apps", 6)

if str(rd_enabled) == "1" or str(rd_enabled).lower() == "true":
    core.load_redis_apps()

core.m_log = logger
core.m_name = logger_name
core.is_notebook()

if str(db_enabled) == "1" or str(db_enabled).lower() == "true":
    if debug:
        lg("Loading Database Apps", 6)
    core.load_db_apps()

if debug:
    lg("End common python initialization Env(" + str(os.getenv("ENV_DEPLOYMENT_TYPE")) + ")", 6)
#
#
################################################################


################################################################
#
# Loading Jupyter client methods for Red10
#
rt_user = os.getenv("ENV_REDTEN_USER", "USER")
rt_pass = os.getenv("ENV_REDTEN_PASS", "PASSWORD")
rt_email = os.getenv("ENV_REDTEN_EMAIL", "email@email.com")
rt_url = os.getenv("ENV_REDTEN_URL", "https://redten.io")

def uni_key(length=-1):
    return str(str(uuid.uuid4()).replace("-", "")[0:length])
# end of uni_key


def ppj(json_data):
    return str(json.dumps(json_data, sort_keys=True, indent=4, separators=(',', ': ')))
# end of ppj


def download_url_to_disk(image_url, path_to_file):

    f = open(path_to_file, 'wb')
    f.write(requests.get(image_url).content)
    f.close()
    
    return path_to_file
# end of download_url_to_disk


def download_to_uni_file(image_url, file_prefix="ctfile", storage_loc="/opt/web", extension=""):

    path_to_file    = str(storage_loc) + "/" + file_prefix + "_" + str(uuid.uuid4()).replace("-", "")
    if extension != "":
        path_to_file += "." + str(extension)

    with open(path_to_file, "w") as output_file:
        output_file.write(requests.get(image_url).content)
        output_file.close()
    
    return path_to_file
# end of download_to_uni_file


def rest_login_as_user(username, password, api_url="", debug=False):

    url = rt_url
    if api_url != "":
        url = api_url

    auth_headers    = {
                        "Content-Type"  : "application/json",
                        "Accept"        : "application/json"
                    }
    data            = {
                        "username"      : username,
                        "password"      : password
                    }

    if debug:
        lg("Sending Post Request", 5)
    use_url         = url + "/login/"
    response        = requests.post(use_url, headers=auth_headers, data=json.dumps(data))

    if response.status_code != 200:
        if response.status_code == 400:
            lg("Login url=" + str(url) + " Failed - Wrong Username or Password for User=" + str(username) + " with Status=" + str(response.status_code) + " Reason=" + str(response.reason), 0)
        else:
            lg("Login url=" + str(url) + " Failed for User=" + str(username) + " with Status=" + str(response.status_code) + " Reason=" + str(response.reason), 0)
            lg("Response Test:\n" + str(response.text) + "\n", 0)
        return ""
    else:
        if debug:
            lg("Post Response Status=" + str(response.status_code) + " Reason=" + str(response.reason), 5)

    res             = {}
    try:
        res         = json.loads(str(response.text))
    except Exception as e:
        lg("ERROR: Failed to Login=" + str(use_url), 0)

    user_token      = str(res["token"])
    if debug:
        lg("Response:", 6)
        lg(user_token, 6)
        lg("", 6)

    return user_token
# end of rest_login_as_user


def rest_full_login(username, password, api_url="", debug=False):

    url = rt_url
    if api_url != "":
        url = api_url

    auth_headers    = {
                        "Content-Type"  : "application/json",
                        "Accept"        : "application/json"
                    }
    data            = {
                        "username"      : username,
                        "password"      : password
                    }

    if debug:
        lg("Sending Post Request", 5)
    use_url         = url + "/login/"
    response        = requests.post(use_url, headers=auth_headers, data=json.dumps(data))

    if response.status_code != 200:
        if response.status_code == 400:
            lg("Login url=" + str(url) + " Failed - Wrong Username or Password for User=" + str(username) + " with Status=" + str(response.status_code) + " Reason=" + str(response.reason), 0)
        else:
            lg("Login url=" + str(url) + " Failed for User=" + str(username) + " with Status=" + str(response.status_code) + " Reason=" + str(response.reason), 0)
            lg("Response Test:\n" + str(response.text) + "\n", 0)
    else:
        if debug:
            lg("Post Response Status=" + str(response.status_code) + " Reason=" + str(response.reason), 5)

    res             = {}
    try:
        res         = json.loads(str(response.text))
    except Exception as e:
        lg("ERROR: Failed to Login=" + str(use_url), 0)

    if debug:
        lg("Response:", 6)
        lg(res, 6)
        lg("", 6)

    return res
# end of rest_full_login


class VariableInspectorWindow(object):
    instance = None
    
    def __init__(self, ipython):
        """Public constructor."""
        if VariableInspectorWindow.instance is not None:
            raise Exception("""Only one instance of the Variable Inspector can exist at a 
                time.  Call close() on the active instance before creating a new instance.
                If you have lost the handle to the active instance, you can re-obtain it
                via `VariableInspectorWindow.instance`.""")
        
        VariableInspectorWindow.instance = self
        self.closed = False
        self.namespace = NamespaceMagics()
        self.namespace.shell = ipython.kernel.shell
        
        self._box = widgets.Box()
        self._box.layout.overflow_y = 'scroll'
        self._table = widgets.HTML(value = 'Not hooked')
        self._box.children = [self._table]
        
        self._ipython = ipython
        self._ipython.events.register('post_run_cell', self._fill)
        
    def close(self):
        """Close and remove hooks."""
        if not self.closed:
            self._ipython.events.unregister('post_run_cell', self._fill)
            self._box.close()
            self.closed = True
            VariableInspectorWindow.instance = None

    def _fill(self):
        """Fill self with variable information."""
        values = self.namespace.who_ls()
        self._table.value = '<div class="rendered_html jp-RenderedHTMLCommon"><table><thead><tr><th>Name</th><th>Type</th><th>Value</th></tr></thead><tr><td>' + \
            '</td></tr><tr><td>'.join(['{0}</td><td>{1}</td><td>{2}'.format(v, type(eval(v)).__name__, str(eval(v))) for v in values]) + \
            '</td></tr></table></div>'

    def _ipython_display_(self):
        """Called when display() or pyout is used to display the Variable 
        Inspector."""
        self._box._ipython_display_()
    
# end of VariableInspectorWindow


def log_progress(sequence, every=None, size=None, name='Items'):

    is_iterator = False
    if size is None:
        try:
            size = len(sequence)
        except TypeError:
            is_iterator = True
    if size is not None:
        if every is None:
            if size <= 200:
                every = 1
            else:
                every = int(size / 200)     # every 0.5%
    else:
        assert every is not None, 'sequence is iterator, set every'

    if is_iterator:
        progress = IntProgress(min=0, max=1, value=1)
        progress.bar_style = 'info'
    else:
        progress = IntProgress(min=0, max=size, value=0)
    label = HTML()
    box = VBox(children=[label, progress])
    display(box)

    index = 0
    try:
        for index, record in enumerate(sequence, 1):
            if index == 1 or index % every == 0:
                if is_iterator:
                    label.value = '{name}: {index} / ?'.format(
                        name=name,
                        index=index
                    )
                else:
                    progress.value = index
                    label.value = u'{name}: {index} / {size}'.format(
                        name=name,
                        index=index,
                        size=size
                    )
            yield record
    except:
        progress.bar_style = 'danger'
        raise
    else:
        progress.bar_style = 'success'
        progress.value = index
        label.value = "{name}: {index}".format(
            name=name,
            index=str(index or '?')
        )
# end of log_progress


def wait_on_job(job_id, debug=False):

    status = "Failed"
    err_msg = ""
    record = {}
    results = {}

    start_time = datetime.datetime.now()
    end_time = datetime.datetime.now()

    total_steps = 10

    # too many notebooks loading with this thing in here
    use_progres_widget = False

    progress = None
    label = None
    box = None
    
    if use_progres_widget:
        try:
            progress = IntProgress(min=0, max=total_steps, value=1)
            prefix_label = "Waiting for Job=" + str(job_id) + " progress=" + str(progress.value) + "/" + str(total_steps)
            label = HTML(prefix_label)
            box = VBox(children=[label, progress])
        except Exception as p:
            progress = None
            label = None
            box = None

        if box:
            display(box)
    # only create this once the bugs are resolved

    try:

        every = 1

        if total_steps <= 200:
            every = 1
        else:
            every = int(total_steps / 200)     # every 0.5%

        query_params = {}
        post_data = {}
        resource_url = rt_url + "/ml/" + str(job_id) + "/"

        lg("Waiting on job=" + str(job_id) + " url=" + str(resource_url), 5)

        last_status = ""
        job_status = "active"
        max_retries = 10
        retry = 0
        sleep_interval = 1.0
        not_done = True

        while not_done:

            # log in again for log running jobs
            user_token = rest_login_as_user(rt_user, rt_pass, rt_url)
            auth_headers = {
                            "Authorization" : "JWT " + str(user_token)
                        }
            get_response = requests.get(resource_url, params=query_params, data=post_data, headers=auth_headers)

            if get_response.status_code != 201 and get_response.status_code != 200:

                if use_progres_widget:
                    progress.bar_style = 'danger'
                err_msg = "Failed with GET Response Status=" + str(get_response.status_code) + " Reason=" + str(get_response.reason)
                lg(err_msg, 0)
                lg("Details:\n" + str(get_response.text) + "\n", 0)
                
                status = "Failed"
                
                retry += 1
                if retry > max_retries: 
                    not_done = False
                    lg("Failed to get job=" + str(job_id) + " status", 0)
                    break
                else:
                    lg("Failed to get job=" + str(job_id) + " status retry=" + str(retry) + "/" + str(max_retries), 0)
                # end of if/else
            else:
                if debug:
                    lg("SUCCESS - GET Response Status=" + str(get_response.status_code) + " Reason=" + str(get_response.reason), 5)

                retry = 0
                status = "SUCCESS"
                err_msg = ""
                job_status = "unknown"
                as_json = True
                record = {}

                if as_json:
                    record = json.loads(get_response.text)
                    job_status = str(record["job"]["status"]).strip().lstrip().lower()
                # end of as_json
            
                if job_status == "requested":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is requested - Step: 0/10", 5)
                    if use_progres_widget:
                        progress.value = 0
                elif job_status == "initial":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is initial - Step 1/10", 5)
                    if use_progres_widget:
                        progress.value = 1
                elif job_status == "active":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is active - Step 2/10", 5)
                    if use_progres_widget:
                        progress.value = 2
                elif job_status == "training":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is training - Step 3/10", 5)
                    if use_progres_widget:
                        progress.value = 3
                elif job_status == "predicting":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is predicting - Step 4/10", 5)
                    if use_progres_widget:
                        progress.value = 4
                elif job_status == "analyzing":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is analyzing - Step 5/10", 5)
                    if use_progres_widget:
                        progress.value = 5
                elif job_status == "caching":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is caching - Step 6/10", 5)
                    if use_progres_widget:
                        progress.value = 6
                elif job_status == "plotting":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is plotting - Step 7/10", 5)
                    if use_progres_widget:
                        progress.value = 7
                elif job_status == "emailing":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is emailing - Step 8/10", 5)
                    if use_progres_widget:
                        progress.value = 8
                elif job_status == "uploading":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is uploading - Step 9/10", 5)
                    if use_progres_widget:
                        progress.value = 9
                elif job_status == "archiving":
                    if last_status != job_status:
                        lg("Job=" + str(job_id) + " is archiving - Step 10/10", 5)
                    if use_progres_widget:
                        progress.value = 10
                elif job_status == "completed":
                    if use_progres_widget:
                        progress.value = 10
                        progress.bar_style = 'success'
                    not_done = False
                    lg("Job=" + str(job_id) + " completed", 5)
                    end_time = datetime.datetime.now()
                    prefix_label = "Done waiting on job=" + str(job_id) + " status=" + str(job_status) + " after waiting " + str((end_time - start_time).total_seconds())[0:5] + "s"
                    prefix_label = str((end_time - start_time).total_seconds())[0:5] + "s - Done waiting on job=" + str(job_id) + " status=" + str(job_status)

                    if use_progres_widget:
                        label.value = u'{name}: {index} / {size}'.format(
                                                        name=prefix_label,
                                                        index=progress.value,
                                                        size=total_steps
                                                    )

                    break
                elif job_status == "cancelled":
                    if use_progres_widget:
                        progress.bar_style = 'danger'
                    not_done = False
                    lg("Job=" + str(job_id) + " cancelled", 5)
                    end_time = datetime.datetime.now()

                    if use_progres_widget:
                        prefix_label = str((end_time - start_time).total_seconds())[0:5] + "s - Done waiting on job=" + str(job_id) + " status=" + str(job_status) + " progress=" + str(progress.value) + "/" + str(total_steps)
                        label.value = u'{name}: {index} / {size}'.format(
                                                        name=prefix_label,
                                                        index=progress.value,
                                                        size=total_steps
                                                    )

                    break
                elif job_status == "error":
                    if use_progres_widget:
                        progress.bar_style = 'danger'
                    not_done = False
                    lg("Job=" + str(job_id) + " error", 5)
                    end_time = datetime.datetime.now()

                    if use_progres_widget:
                        prefix_label = str((end_time - start_time).total_seconds())[0:5] + "s - Done waiting on job=" + str(job_id) + " status=" + str(job_status) + " progress=" + str(progress.value) + "/" + str(total_steps)
                        label.value = u'{name}: {index} / {size}'.format(
                                                        name=prefix_label,
                                                        index=progress.value,
                                                        size=total_steps
                                                    )

                    break
                else:
                    if use_progres_widget:
                        progress.bar_style = 'danger'
                    not_done = False
                    lg("Job=" + str(job_id) + " in unexpected status=" + str(job_status) + "", 0)
                    end_time = datetime.datetime.now()
                    if use_progres_widget:
                        prefix_label = str((end_time - start_time).total_seconds())[0:5] + "s - Done waiting on job=" + str(job_id) + " status=" + str(job_status) + " progress=" + str(progress.value) + "/" + str(total_steps)
                        label.value = u'{name}: {index} / {size}'.format(
                                                        name=prefix_label,
                                                        index=progress.value,
                                                        size=total_steps
                                                    )

                    break
                # end of if/else
                
                last_status = job_status
                
            # end of post for running an ML Job

            end_time = datetime.datetime.now()

            if use_progres_widget:
                prefix_label = str((end_time - start_time).total_seconds())[0:5] + "s - Waiting on job=" + str(job_id) + " status=" + str(job_status) + " progress=" + str(progress.value) + "/" + str(total_steps)
                label.value = u'{name}: {index} / {size}'.format(
                                                        name=prefix_label,
                                                        index=progress.value,
                                                        size=total_steps
                                                    )

            if not_done:
                sleep(sleep_interval)

        # end of while not_done

    except Exception as w:
        status = "Exception"
        err_msg = "Failed waiting on job=" + str(job_id) + " with Ex=" + str(w)
        lg(err_msg, 0)
        end_time = datetime.datetime.now()

        if use_progres_widget:
            progress.bar_style = 'danger'
            prefix_label = str((end_time - start_time).total_seconds())[0:5] + "s - Error waiting on job=" + str(job_id) + " status=" + str(status) + " progress=" + str(progress.value) + "/" + str(total_steps) + " hit Exception: " + str(w)
            label.value = u'{name}: {index} / {size}'.format(
                                            name=prefix_label,
                                            index=progress.value,
                                            size=total_steps
                                        )

    # end of try/ex

    results = {
                "status" : status,
                "error" : err_msg,
                "record" : record
            }

    return results
# end of wait_on_job


def wait_for_job_to_finish(job_id):

    status = "Failed"
    err_msg = ""
    record = {}
    results = {}

    try:

        query_params = {}
        post_data = {}
        resource_url = rt_url + "/ml/" + str(job_id) + "/"

        lg("Waiting on job=" + str(job_id) + " url=" + str(resource_url), 5)

        job_status = "active"
        max_retries = 10
        retry = 0
        sleep_interval = 1.0
        not_done = True

        while not_done:

            user_token = rest_login_as_user(rt_user, rt_pass, rt_url)
            auth_headers = {
                        "Authorization" : "JWT " + str(user_token)
                    }
            get_response = requests.get(resource_url, params=query_params, data=post_data, headers=auth_headers)

            if get_response.status_code != 201 and get_response.status_code != 200:
                err_msg = "Failed with GET Response Status=" + str(get_response.status_code) + " Reason=" + str(get_response.reason)
                lg(err_msg, 0)
                lg("Details:\n" + str(get_response.text) + "\n", 0)
                
                status = "Failed"
                
                retry += 1
                if retry > max_retries: 
                    not_done = False
                    lg("Failed to get job=" + str(job_id) + " status", 0)
                    break
                else:
                    lg("Failed to get job=" + str(job_id) + " status retry=" + str(retry) + "/" + str(max_retries), 0)
                # end of if/else
            else:
                lg("SUCCESS - GET Response Status=" + str(get_response.status_code) + " Reason=" + str(get_response.reason), 5)

                retry = 0
                status = "SUCCESS"
                err_msg = ""
                job_status = "unknown"
                as_json = True
                record = {}

                if as_json:
                    record = json.loads(get_response.text)
                    job_status = str(record["job"]["status"]).strip().lstrip().lower()
                # end of as_json
                
                
                if job_status == "requested":
                    lg("Job=" + str(job_id) + " is requested - Step: 0/10", 5)
                    progress = 0
                elif job_status == "initial":
                    lg("Job=" + str(job_id) + " is initial - Step 1/10", 5)
                    progress = 1
                elif job_status == "active":
                    lg("Job=" + str(job_id) + " is active - Step 2/10", 5)
                    progress = 2
                elif job_status == "training":
                    lg("Job=" + str(job_id) + " is training - Step 3/10", 5)
                    progress = 3
                elif job_status == "predicting":
                    lg("Job=" + str(job_id) + " is predicting - Step 4/10", 5)
                    progress = 4
                elif job_status == "analyzing":
                    lg("Job=" + str(job_id) + " is analyzing - Step 5/10", 5)
                    progress = 5
                elif job_status == "caching":
                    lg("Job=" + str(job_id) + " is caching - Step 6/10", 5)
                    progress = 6
                elif job_status == "plotting":
                    lg("Job=" + str(job_id) + " is plotting - Step 7/10", 5)
                    progress = 7
                elif job_status == "emailing":
                    lg("Job=" + str(job_id) + " is emailing - Step 8/10", 5)
                    progress = 8
                elif job_status == "uploading":
                    lg("Job=" + str(job_id) + " is uploading - Step 9/10", 5)
                    progress = 9
                elif job_status == "archiving":
                    lg("Job=" + str(job_id) + " is archiving - Step 10/10", 5)
                    progress = 10
                elif job_status == "completed":
                    progress = 10
                    not_done = False
                    lg("Job=" + str(job_id) + " completed", 5)
                    break
                elif job_status == "cancelled":
                    not_done = False
                    lg("Job=" + str(job_id) + " cancelled", 5)
                    break
                elif job_status == "error":
                    not_done = False
                    lg("Job=" + str(job_id) + " error", 5)
                    break
                else:
                    not_done = False
                    lg("Job=" + str(job_id) + " completed", 5)
                    break
                # end of if/else
                
            # end of post for running an ML Job

            if not_done:
                sleep(sleep_interval)

        # end of while not_done

    except Exception as w:
        status = "Exception"
        err_msg = "Failed waiting for job=" + str(job_id) + " with Ex=" + str(w)
        lg(err_msg, 0)
    # end of try/ex

    results = {
                "status" : status,
                "error" : err_msg,
                "record" : record
            }

    return results
# end of wait_for_job_to_finish


def helper_get_job_analysis(job_id):

    status = "Failed"
    err_msg = ""
    record = {}
    results = {}

    try:

        query_params = {}
        post_data = {}
        resource_url = rt_url + "/ml/analysis/" + str(job_id) + "/"

        lg("Getting analysis for job=" + str(job_id) + " url=" + str(resource_url), 5)

        job_status = "active"
        max_retries = 10
        retry = 0
        sleep_interval = 1.0
        not_done = True

        while not_done:

            user_token = rest_login_as_user(rt_user, rt_pass, rt_url)
            auth_headers = {
                            "Authorization" : "JWT " + str(user_token)
                        }
            get_response = requests.get(resource_url, params=query_params, data=post_data, headers=auth_headers)

            if get_response.status_code != 201 and get_response.status_code != 200:

                # if logged out while waiting, just log back in a retry
                if "Signature has expired." in str(get_response.text):
                    user_token = user_login(rt_user, rt_pass, rt_url)

                    auth_headers = { 
                                    "Authorization" : "JWT " + str(user_token)
                                }
                else:
                    err_msg = "Failed with GET Analysis Response Status=" + str(get_response.status_code) + " Reason=" + str(get_response.reason)
                    lg(err_msg, 0)
                    lg("Details:\n" + str(get_response.text) + "\n", 0)
                
                    status = "Failed"
                    
                    retry += 1
                    if retry > max_retries: 
                        not_done = False
                        lg("Failed to get analysis for job=" + str(job_id) + " status", 0)
                        break
                    else:
                        lg("Failed to get analysis for job=" + str(job_id) + " status retry=" + str(retry) + "/" + str(max_retries), 0)
                # end of if/else

            else:
                lg("SUCCESS - GET Analysis Response Status=" + str(get_response.status_code) + " Reason=" + str(get_response.reason), 5)

                retry = 0
                status = "SUCCESS"
                err_msg = ""
                job_status = "unknown"
                as_json = True
                record = {}

                if as_json:
                    record = json.loads(get_response.text)
                    not_done = False
                    lg("Found Job=" + str(job_id) + " analysis", 5)
                    break
                # end of if/else
                
            # end of post for running an ML Job

            if not_done:
                sleep(sleep_interval)

        # end of while not_done

    except Exception as w:
        status = "Exception"
        err_msg = "Failed waiting on get analysis for job=" + str(job_id) + " with Ex=" + str(w)
        lg(err_msg, 0)
    # end of try/ex

    results = {
                "status" : status,
                "error" : err_msg,
                "record" : record
            }

    return results
# end of helper_get_job_analysis


def search_ml_jobs(search_req, debug=False):

    status = "Failed"
    err_msg = ""
    record = {}
    results = {}

    try:

        query_params = {
                        "title" : search_req["title"],
                        "dsname" : search_req["dsname"],
                        "desc" : search_req["desc"],
                        "features" : search_req["features"],
                        "target_column" : search_req["target_column"]
                    }
        post_data = {}
    

        # Get the ML Job
        resource_url = rt_url + "/ml/search/"

        lg("Searching ML Jobs url=" + str(resource_url), 6)

        job_status = "active"
        max_retries = 10
        retry = 0
        sleep_interval = 1.0
        not_done = True

        while not_done:

            user_token = rest_login_as_user(rt_user, rt_pass, rt_url)
            auth_headers = {
                            "Authorization" : "JWT " + str(user_token)
                        }
            get_response = requests.get(resource_url, params=query_params, data=post_data, headers=auth_headers)

            if get_response.status_code != 201 and get_response.status_code != 200:
                err_msg = "Failed with SEARCH Response Status=" + str(get_response.status_code) + " Reason=" + str(get_response.reason)
                lg(err_msg, 0)
                lg("Details:\n" + str(get_response.text) + "\n", 0)
                
                status = "Failed"
                
                retry += 1
                if retry > max_retries: 
                    not_done = False
                    lg("Failed to search=" + str(search_req) + " for jobs status", 0)
                    break
                else:
                    lg("Failed to search=" + str(search_req) + " for jobs status retry=" + str(retry) + "/" + str(max_retries), 0)
                # end of if/else
            else:
                lg("SUCCESS - Job Search Response Status=" + str(get_response.status_code) + " Reason=" + str(get_response.reason), 5)

                retry = 0
                status = "SUCCESS"
                err_msg = ""
                job_status = "unknown"
                as_json = True
                record = {}

                if as_json:
                    record = json.loads(get_response.text)
                    not_done = False
                    lg("Found Job=" + str(search_req) + " results", 5)
                    break
                # end of if/else
                
            # end of post for running an ML Job

            if not_done:
                sleep(sleep_interval)

        # end of while not_done

    except Exception as w:
        status = "Exception"
        err_msg = "Failed waiting on search=" + str(search_req) + " for jobs with Ex=" + str(w)
        lg(err_msg, 0)
    # end of try/ex

    results = {
                "status" : status,
                "error" : err_msg,
                "record" : record
            }

    return results
# end of search_ml_jobs


def build_api_urls(use_base_url=""):

    base_url = str(os.getenv("ENV_REDTEN_URL", "https://redten.io"))
    if use_base_url != "":
        base_url = use_base_url

    api_urls = {
            "create-job" : base_url + "/ml/run/",
            "get-job" : base_url + "/ml/%s/",
            "get-analysis" : base_url + "/ml/analysis/%s/",
            "import" : base_url + "/ml/import/"
        }
    return api_urls
# end of build_api_urls


def run_job(query_params={}, post_data={}, headers={}, user_id=2, retry=False, debug=False):

    result = {
                "status" : "invalid",
                "data" : {}
            }

    try:
    
        api_urls = build_api_urls()
        
        use_url = str(api_urls["create-job"])
        
        if debug:
            lg("Running ML Job url=" + str(use_url), 5)

        if "user_id" not in post_data:
            post_data["user_id"] = user_id
        # add in my user

        if "ds_name" in post_data:
            ds_name = str(post_data["ds_name"])
        # end of changing the csv file by the data set name

        post_response = requests.post(use_url, params=query_params, data=json.dumps(post_data), headers=headers)

        if post_response.status_code != 201 and post_response.status_code != 200:

            if not retry:
                if "Signature has expired." in str(post_response.text):
                    user_token = user_login(rt_user, rt_pass, rt_url)

                    auth_headers = { 
                                    "Content-type": "application/json",
                                    "Authorization" : "JWT " + str(user_token)
                                }
                    run_job(query_params=query_params, post_data=post_data, headers=auth_headers, user_id=user_id, retry=True, debug=debug)
                else:
                    boom("Failed with Post Response Status=" + str(post_response.status_code) + " Reason=" + str(post_response.reason))
                    boom("Details:\n" + str(post_response.text) + "\n")
            else:
                boom("Failed with Post Response Status=" + str(post_response.status_code) + " Reason=" + str(post_response.reason))
                boom("Details:\n" + str(post_response.text) + "\n")
        else:
            if debug:
                lg("SUCCESS - Post Response Status=" + str(post_response.status_code) + " Reason=" + str(post_response.reason), 5)

            result["data"] = json.loads(post_response.text)
            result["status"] = "valid"
        # end of valid response from the api

    except Exception as e:
        result["status"] = "Failed to Run ML Job with exception='" + str(e) + "'"
        result["data"] = {}
        boom(result["status"])
    # end of try/ex

    return result
# end of run_job


def get_job_analysis(job_id, show_plots=True, debug=False):

    job_report = {}
    if job_id == None:
        boom("Failed to start a new job")
    else:
        job_res = helper_get_job_analysis(job_id)

        if job_res["status"] != "SUCCESS":
            boom("Job=" + str(job_id) + " failed with status=" + str(job_res["status"]) + " err=" + str(job_res["error"]))
        else:
            job_report = job_res["record"]
    # end of get job analysis

    if show_plots:
        if "images" in job_report:
            for img in job_report["images"]:
                anmt(img["title"])
                lg("URL: " + str(img["image"]))
                ipyDisplay(ipyImage(url=img["image"]))
                lg("---------------------------------------------------------------------------------------")
        else:
            boom("Job=" + str(job_id) + " does not have any images yet")
        # end of if images exist
    # end of downloading job plots
    
    return job_report
# end of get_job_analysis


def get_job_results(job_report, cell=0, debug=False):
    try:
        if len(job_report["analyses"]) < cell:
            boom("Failed to get accuracy because job does not have a cell=" + str(cell) + " length=" + str(len(job_report["analyses"])))
            return {}
        else:
            return job_report["analyses"][cell]["analysis_json"]["manifest"]["job_results"]
    except Exception as e:
        boom("Invalid get_job_results - please pass in the full analysis report to this method - exception=" + str(e))
        return {}
# end of get_job_results


def get_job_cache_manifest(job_report, cell=0, debug=False):
    try:
        if len(job_report["analyses"]) < cell:
            boom("Failed to get cache manifest because job does not have a cell=" + str(cell) + " length=" + str(len(job_report["analyses"])))
            return {}
        else:
            return job_report["analyses"][cell]["analysis_json"]["manifest"]["manifest"]
    except Exception as e:
        boom("Invalid get_job_cache_manifest - please pass in the full analysis report to this method - exception=" + str(e))
# end of get_job_cache_manifest


def get_analysis_manifest(job_report, cell=0, debug=False):
    try:
        if len(job_report["analyses"]) < cell:
            boom("Failed to get manifest because job does not have a cell=" + str(cell) + " length=" + str(len(job_report["analyses"])))
            return {}
        else:
            return job_report["analyses"][cell]["analysis_json"]["manifest"]
    except Exception as e:
        boom("Invalid get_analysis_manifest - please pass in the full analysis report to this method - exception=" + str(e))
# end of get_analysis_manifest


def build_prediction_results(job_report, cell=0, debug=False):

    res = {}

    try:
        if len(job_report["analyses"]) < cell:
            boom("Failed to build_prediction_results because job does not have a cell=" + str(cell) + " length=" + str(len(job_report["analyses"])))
            return {}
        else:
            job_results = get_job_results(job_report, cell, debug) 
            if len(job_results) == 0:
                boom("Failed to find job_results for building prediction results")
                return res
            else:
                for col_name in job_results["accuracy_json"]:
                    res[col_name] = {}
                    mse = None
                    try:
                        mse = float(job_results["accuracy_json"][col_name]["MSE"])
                    except Exception as f:
                        mse = None

                    accuracy = None
                    try:
                        accuracy = float(job_results["accuracy_json"][col_name]["TrainAccuracy"])
                    except Exception as f:
                        accuracy = None

                    predictions_df = None
                    try:
                        predictions_df = pd.DataFrame(job_results["accuracy_json"][col_name]["Predictions"])
                    except Exception as f:
                        boom("Failed Converting column=" + str(col_name) + " Predictions to pd.DataFrame with exception=" + str(f))
                        predictions_df = None

                    res[col_name]["mse"] = mse
                    res[col_name]["accuracy"] = accuracy
                    res[col_name]["predictions_df"] = predictions_df
                # for all columns in the accuracy payload

            # if/else valid report to analyze
    except Exception as e:
        boom("Invalid build_prediction_results - please pass in the full analysis report to this method - exception=" + str(e))
    # end of try/ex

    return res
# end of build_prediction_results


def build_forecast_results(job_report, cell=0, debug=False):

    res = {}

    try:
        if len(job_report["analyses"]) < cell:
            boom("Failed to build_forecast_results because job does not have a cell=" + str(cell) + " length=" + str(len(job_report["analyses"])))
            return {}
        else:
            job_results = get_job_results(job_report, cell, debug) 
            if len(job_results) == 0:
                boom("Failed to find job_results for building prediction results")
                return res
            else:
                for col_name in job_results["accuracy_json"]:
                    res[col_name] = {}

                    mse = None
                    try:
                        mse = float(job_results["accuracy_json"][col_name]["MSE"])
                    except Exception as f:
                        mse = None

                    accuracy = None
                    try:
                        accuracy = float(job_results["accuracy_json"][col_name]["TrainAccuracy"])
                    except Exception as f:
                        accuracy = None

                    predictions_df = None
                    try:
                        predictions_df = pd.DataFrame(job_results["accuracy_json"][col_name]["Predictions"])
                    except Exception as f:
                        predictions_df = None

                    forecast_mse = None
                    try:
                        forecast_mse = float(job_results["accuracy_json"][col_name]["ForecastMSE"])
                    except Exception as f:
                        forecast_mse = None

                    train_accuracy = None
                    try:
                        train_accuracy = float(job_results["accuracy_json"][col_name]["TrainAccuracy"])
                    except Exception as f:
                        train_accuracy = None

                    train_predictions = None
                    try:
                        train_predictions = job_results["accuracy_json"][col_name]["TrainPredictions"]
                    except Exception as f:
                        train_predictions = None

                    train_predictions_df = None
                    try:
                        train_predictions_df = pd.DataFrame(json.loads(job_results["accuracy_json"][col_name]["TrainPredictionsDF"]))
                    except Exception as f:
                        boom("Failed Converting column=" + str(col_name) + " TrainPredictionsDF to pd.DataFrame with exception=" + str(f))
                        train_predictions_df = None
                    # end of TrainPredictionsDF

                    date_predictions_df = None
                    try:
                        date_predictions_df = pd.DataFrame(json.loads(job_results["accuracy_json"][col_name]["DatePredictionsDF"])).sort_values(by="Date", ascending=True)
                        date_predictions_df["Date"] = pd.to_datetime(date_predictions_df["Date"], unit='ms')
                        if "Invalid" in date_predictions_df.columns:
                            del date_predictions_df["Invalid"]
                    except Exception as f:
                        boom("Failed Converting column=" + str(col_name) + " DatePredictionsDF to pd.DataFrame with exception=" + str(f))
                        date_predictions_df = None
                    # end of DatePredictionsDF

                    res[col_name]["accuracy"] = accuracy
                    res[col_name]["mse"] = forecast_mse
                    res[col_name]["predictions_df"] = predictions_df
                    res[col_name]["train_mse"] = mse
                    res[col_name]["train_accuracy"] = train_accuracy
                    res[col_name]["train_predictions"] = train_predictions
                    res[col_name]["train_predictions_df"] = train_predictions_df
                    res[col_name]["date_predictions_df"] = date_predictions_df
                # for all columns in the accuracy payload

            # if/else valid report to analyze
    except Exception as e:
        boom("Invalid build_forecast_results - please pass in the full analysis report to this method - exception=" + str(e))
    # end of try/ex

    return res
# end of build_forecast_results


def generic_search(url, term):
    """Simple Elasticsearch Query"""
    query = json.dumps({
        "query": {
            "match": {
                "message": term
            }
        }
    })
    response = requests.get(uri, data=query)
    results = json.loads(response.text)
    return results
# end of search


def get_latest(url, limit=50):
    """Simple Elasticsearch Query"""
    query = json.dumps(
                {
                    "query": {
                        "match_all": {}
                    },
                    "size": limit,
                    "sort": [
                        {
                            "@timestamp": {
                                "order": "desc"
                            }
                        }
                    ]
                }
            )
    response = requests.get(url, data=query)
    results = json.loads(response.text)
    return results
# end of get_latest


def get_latest_errors_in_es(url, limit=50):
    query = json.dumps(
        {
            "query": {
                "bool"  : {
                    "should"  : [
                        {
                            "match"  : {
                                "level" : {
                                    "query"  : "ERROR",
                                    "boost"  : 50
                                }
                            }
                        }
                    ]
                }
            },
            "size": limit,
            "sort": [
                {
                    "@timestamp": {
                        "order": "desc"
                    }
                }
            ]
        }
    )
    response = requests.get(url, data=query)
    results = json.loads(response.text)
    return results
# end of get_latest


def convert_date_string_to_date(date_str, optional_format="%Y-%m-%dT%H:%M:%S.%fZ"):

    date_to_return = None
    try:
        import datetime
        date_to_return = datetime.datetime.strptime(str(date_str), optional_format)
    except Exception,f:
        self.lg("ERROR: Failed Converting Date(" + str(date_str) + ") with Format(" + str(optional_format) + ")", 0)
    # end of tries to read this string as a valid date...

    return date_to_return
# end of convert_date_string_to_date

    
def format_results(results, debug=False):
    data = [doc for doc in results['hits']['hits']]
    logs = []
    for doc in reversed(data):        
        try:
            new_log = {
                "date" : str(convert_date_string_to_date(doc["_source"]["@timestamp"]).strftime("%Y-%m-%d %H:%M:%S")),
                "level" : str(doc["_source"]["level"]).strip().lstrip(),
                "msg" : str(doc["_source"]["message"]).strip().lstrip(),
                "host" : str(doc["_source"]["host"]).strip().lstrip(),
                "logger" : str(doc["_source"]["host"]).strip().lstrip(),
                "tags" : doc["_source"]["tags"]
            }
            if debug:
                print("%s - %s - %s" % (new_log["date"], new_log["level"], new_log["msg"]))

            if "/login/" not in new_log["msg"]:
                logs.append(new_log)
            # ignore the login messages...

        except Exception as e:
            lg("Failed to process log=" + str(doc) + " with ex=" + str(e), 0)
        # end try/ex
    # end of for all docs
    
    return logs
# end of format_results


def get_latest_logs(es_endpoint="https://redten.io:9201/", index="logstash-*", doc_type="restlogs", num_logs=20):
    search_url = str(es_endpoint) + str(index) + "/" + str(doc_type) + "/_search"
    results = get_latest(search_url, num_logs)
    return format_results(results)
# end of get_latest_logs


def get_latest_errors(es_endpoint="https://redten.io:9201/", index="logstash-*", doc_type="restlogs", num_logs=20):
    search_url = str(es_endpoint) + str(index) + "/" + str(doc_type) + "/_search"
    results = get_latest_errors_in_es(search_url, num_logs)
    return format_results(results)
# end of get_latest_errors


def display_logs(log_data=[], debug=False):
    for cur_log in log_data:
        lg(str(cur_log["date"]) + " - " + str(cur_log["level"]) + " - " + str(cur_log["msg"]))
    # end for for all logs to show
# end of display_logs


def show_logs(limit=20, debug=False):
    display_logs(get_latest_logs(num_logs=limit))
    return None
# end of show_logs


def show_errors(limit=20, debug=False):
    display_logs(get_latest_errors(num_logs=limit))
    return None
# end of show_errors


# returns a user token (jwt) for now
def user_login(rt_user, rt_pass, rt_url):

    user_token = rest_login_as_user(rt_user, rt_pass, rt_url)
    if user_token == "":
        boom("Failed logging in - Stopping")
        return ""
    # end of if logged in work

    return user_token
# end of user_login

csv_file = ""
api_urls = build_api_urls()

# log in:
user_token = user_login(rt_user, rt_pass, rt_url)

#
#
################################################################


