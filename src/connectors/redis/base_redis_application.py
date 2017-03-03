import json, sys, os

sys.path.append("/opt/src")
from connectors.redis.redis_wrapper import RedisWrapper

class BaseRedisApplication:

    def __init__(self, name, redis_address, port, redis_queue, logger, request_key_name=None, response_key_name=None, debug=False):

        self.m_name                 = name
        self.m_host_address         = redis_address
        self.m_port                 = port
        self.m_queue_name           = redis_queue
        self.m_log                  = logger
        self.m_debug                = debug

        self.m_db                   = int(os.getenv("ENV_REDIS_DB_ID", 0))
        self.m_redis_password       = os.getenv("ENV_REDIS_PASSWORD", "") # if set to empty string use password=None

        if str(self.m_redis_password) == "":
            self.m_redis_password   = None

        self.m_rw                   = None
        self.m_put_count            = 0
        self.m_get_count            = 0
        self.m_failed_get_count     = 0
        self.m_fetch_timeout        = 60
        self.m_overflowed           = False
        self.m_max_count_on_arch    = sys.maxsize - 1
        self.m_sleep_for_connection_outage = 1

        self.m_request_key          = request_key_name
        self.m_response_key         = response_key_name
    # end of __init__
    

    def enable_debug(self):
        self.m_debug = True
        return None
    # end of enable_debug


    def disable_debug(self):
        self.m_debug = False
        return None
    # end of enable_debug

    
    def reset_counts(self):
        self.m_get_count = 0
        self.m_put_count = 0
        self.m_failed_get_count = 0
        self.m_overflowed = False
        return None
    # end of reset_counts
    

    def update_failed_get_count(self):
        if self.m_failed_get_count == self.m_max_count_on_arch:
            self.m_overflowed = True
            self.m_failed_get_count = 0
        else:
            self.m_failed_get_count += 1
        
        return None
    # end of update_failed_get_count


    def update_get_count(self):
        if self.m_get_count == self.m_max_count_on_arch:
            self.m_overflowed = True
            self.m_get_count = 0
        else:
            self.m_get_count += 1
        
        return None
    # end of update_get_count

     
    def update_put_count(self):
        if self.m_put_count == self.m_max_count_on_arch:
            self.m_overflowed = True
            self.m_put_count = 0
        else:
            self.m_put_count += 1
        
        return None
    # end of update_put_count


    def lg(self, msg, level=6):

        if self.m_log:
            full_msg = self.m_name + ": " + msg

            if self.m_debug:
                print full_msg

            self.m_log.log(full_msg, level)

        return None
    # end of lg

    
    # Force ALL Derived clients to Disconnect correctly
    def disconnect(self):
        return None
    # end of disconnect


    # Force ALL Derived clients to Connect correctly
    def connect(self):
        return None
    # end of connect
        
    
    def get_message(self):
        self.lg("Testing Get Message Timeout(" + str(self.m_fetch_timeout) + ")", 7)

        # By default RedisWrapper returns None when the timeout is hit
        msg = self.m_rw.get(False, self.m_fetch_timeout)

        self.update_get_count()

        return msg
    # end of get_message
    
    
    def put_message(self, msg_object):
        self.lg("Putting Message(" + str(msg_object.__class__.__name__) + ")", 7)

        msg = self.m_rw.put(msg_object)

        self.update_put_count()
        return None
    # end of put_message

# end of BaseRedisApplication
