#!/usr/bin/python

import sys, os, json, inspect
from redis_wrapper import RedisWrapper

port    = 6000
db      = int(os.getenv("ENV_REDIS_DB_ID", 0))
redis_pw= os.getenv("ENV_REDIS_PASSWORD", "") # if set to empty string use password=None

if str(redis_pw) == "":
    redis_pw  = None

queue   = RedisWrapper("example_queue", host="localhost", port=port, db=int(db), password=redis_pw)

queue.put(9)
queue.put(8)
queue.put(7)
queue.put(6)
queue.put(5)


