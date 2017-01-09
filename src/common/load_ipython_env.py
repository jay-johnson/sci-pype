#!/usr/bin/env python

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

# Set up the ENV
default_env     = "Local"
use_env         = os.getenv("ENV_DEPLOYMENT_TYPE", default_env)
os.environ["ENV_DEPLOYMENT_TYPE"] = use_env
if os.path.exists("/opt/aws/bin/ec2-metadata"):
    os.environ["ENV_DEPLOYMENT_TYPE"] = "Test"

debug           = False
if debug:
    lg("Start common python initialization Env(" + str(os.getenv("ENV_DEPLOYMENT_TYPE")) + ")", 6)

core_config     = os.getenv("ENV_CORE_CONFIG_FILE", "/opt/work/configs/jupyter.json")
data_dir        = os.getenv("ENV_DATA_SRC_DIR", "/opt/scipype/data/src")
db_enabled      = os.getenv("ENV_DBS_ENABLED", "0")
rd_enabled      = os.getenv("ENV_RDS_ENABLED", "1")
lg_enabled      = os.getenv("ENV_SYSLOG_ENABLED", "0")      # unless your docker daemon has exposed syslog...keep this at 0
logger_name     = os.getenv("ENV_PY_LOGGER_NAME", "ds")
env_name        = os.getenv("ENV_DEPLOYMENT_TYPE", "Local")

core            = PyCore(core_config)
now             = datetime.datetime.now()
ra_name         = "CACHE"
ra_key          = "NODB_PERFORM_THIS_WORK"
logger          = None

if str(lg_enabled) == "1" or str(lg_enabled).lower() == "true":
    logger      = Logger(logger_name, "/dev/log", logging.DEBUG)

if debug:
    lg("Loading Redis Apps", 6)

if str(rd_enabled) == "1" or str(rd_enabled).lower() == "true":
    core.load_redis_apps()

core.m_log      = logger
core.m_name     = logger_name
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
