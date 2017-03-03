import json, os, datetime

from functools import wraps
try:
    import cPickle as pickle
except ImportError:
    import pickle

from redis import Redis
from time import sleep


class RedisWrapper(object):
    
    def __init__(self, name, serializer=pickle, **kwargs):
        self.m_debug            = False
        self.m_name             = name
        self.m_theserializer    = serializer
        self.m_redis            = Redis(**kwargs)
        self.m_retry_interval   = 1
        self.m_retry_count      = 1
        self.m_max_retries      = -1
        self.m_max_sleep_secs   = 30 # 30 seconds
        
        self.m_host             = ""
        self.m_port             = ""
        self.m_address          = ""
        self.m_id               = "Name(" + str(self.m_name) + ")"

        for key, value in kwargs.iteritems():
            if str(key) == "host":
                self.m_host     = str(value)
            if str(key) == "port":
                self.m_port     = str(value)
        
        if self.m_host != "" and self.m_port != "":
            self.m_id           = "Name(" + str(self.m_name) + ") RedisAddress(" + str(self.m_host) + ":" + str(self.m_port) + ")"

        self.m_error_log        = "/tmp/__redis_errors.log"
        self.m_state            = "Disconnected"
    # end of __init__


    def retry_throttled_connection(self, ex, debug=False):

        msg  = "ERROR - " + str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) + " - " + self.m_id + " - RW EX - " + str(ex) + "\n"

        # append to the error log
        with open(self.m_error_log, "a") as output_file:
            output_file.write(str(msg))

        try:
            self.m_state        = "Disconnected"
            cur_sleep           = (self.m_retry_interval * self.m_retry_count) + 1
            if debug:
                print "Retrying Connection"
            while self.m_state == "Disconnected":

                try:
                    msg = self.safe_get_cached_single_set("RetryingRedisConnection")
                    
                    if "Status" in msg and str(msg["Status"]) != "EXCEPTION":
                        print "------"
                        print "SUCCESS(" + str(msg) + ")"
                        print str(msg)
                        print ""
                        self.m_state = "Connected"
                    
                except Exception,e:
                    if debug:
                        print "Redis Failed Connection Retry(" + str(e) + ")"

                if self.m_state != "Connected":
                    cur_sleep               = (self.m_retry_interval * self.m_retry_count) + 1
                    if cur_sleep > self.m_max_sleep_secs:
                        cur_sleep           = self.m_max_sleep_secs
                        if debug:
                            print "---MAX SLEEP(" + str(self.m_max_sleep_secs) + ") HIT"
                    else:
                        self.m_retry_count      += 1
                        self.m_retry_interval   += 2

                    if debug:
                        print " - Sleeping before Retry(" + str(cur_sleep) + ")"
                    sleep(cur_sleep)
                    
            # end of while disconnected
            if debug:
                print "Retrying Connection - SUCCESS"

            self.m_retry_count      = 1
            self.m_retry_interval   = 1

        except Exception, k:
            print "ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")"
            print "ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")"
            print "ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")"
            print "ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")"
            print "ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")"
            print "ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")"

        # end of try/ex

        msg  = "Retry Completed - " + str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) + " - " + self.m_id + " - RW.m_state(" + str(self.m_state) + ")" + "\n"
        # append to the error log
        with open(self.m_error_log, "a") as output_file:
            output_file.write(str(msg))

        if debug:
            print msg

        return True
    # end of retry_throttled_connection


    def client_kill(self):

        try:
            self.m_redis.connection_pool.get_connection("QUIT").disconnect()
            self.m_state = "Disconnected"
        except Exception, p:
            print "ERROR: Failed to Kill: " + str(self.m_id) + " with Ex(" + str(p) + ")"
            self.m_state = "Disconnected"

        return None
    # end of client_kill

    
    def __rlen(self):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################


                return self.m_redis.llen(self.key())


        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of __rlen

    
    def allconsume(self, **kwargs):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################


                kwargs.setdefault('block', True)
                try:
                    while True:
                        msg = self.get(**kwargs)
                        if msg is None:
                            break
                        yield msg
                except KeyboardInterrupt:
                    print; 
                    return


        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of allconsume

    
    def key(self):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################


                return "%s" % self.m_name


        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of key
    
    
    def get_cached_multiple_set(self, start_idx=0, end_idx=-1, queue=None):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################


                msg = None

                if queue == None:
                    msg = self.m_redis.lrange(self.key(), start_idx, end_idx)
                    return msg
                else:
                    msg = self.m_redis.lrange(queue, start_idx, end_idx)
                    return msg

                if msg is not None and self.m_theserializer is not None:
                    msg = self.m_theserializer.loads(msg[0])
                    return msg
                
                return msg


        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of get_cached_multiple_set


    def safe_get_cached_single_set(self, key):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################


                msg = {
                        "Value"     : None,
                        "Status"    : None,
                        "Exception" : None
                }
                try:
                    cached_msg  = self.m_redis.lrange(key, 0, 1)
                    new_msg     = None

                    if cached_msg is not None and len(cached_msg) != 0 and self.m_theserializer is not None:
                        new_msg = self.m_theserializer.loads(cached_msg[0])

                    msg["Value"]        = new_msg
                    msg["Status"]       = "SUCCESS"
                # end of try

                except Exception, e:
                    msg["Status"]       = "EXCEPTION"
                    msg["Exception"]    = "Exception(" + str(e) + ")"
                # end of exception

                return msg


        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of safe_get_cached_single_set


    def get_cached_single_set(self, queue=None):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################


                msg = None

                if queue == None:
                    msg = self.m_redis.lrange(self.key(), 0, 1)
                    return msg
                else:
                    msg = self.m_redis.lrange(queue, 0, 1)
                    return msg

                if msg is not None and self.m_theserializer is not None:
                    msg = self.m_theserializer.loads(msg[0])
                    return msg
                
                return msg


        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of get_cached_single_set


    def get(self, block=False, timeout=None, queue=None):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################


                msg = None
                if block:
                    if timeout is None:
                        timeout = 0

                    if queue == None:
                        msg = self.m_redis.blpop(self.key(), timeout=timeout)
                    else:
                        msg = self.m_redis.blpop(queue, timeout=timeout)

                    if msg is not None:
                        msg = msg[1]
                else:
                    if queue == None:
                        msg = self.m_redis.lpop(self.key())
                    else:
                        msg = self.m_redis.lpop(queue)

                if msg is not None and self.m_theserializer is not None:
                    msg = self.m_theserializer.loads(msg)
                return msg


        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of get
    

    def put_into_key(self, key, *msgs):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################


                if self.m_theserializer is not None:
                    msgs = map(self.m_theserializer.dumps, msgs)

                self.m_redis.rpush(key, *msgs)


        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of put_into_key


    def put(self, *msgs):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################


                if self.m_theserializer is not None:
                    msgs = map(self.m_theserializer.dumps, msgs)

                self.m_redis.rpush(self.key(), *msgs)


        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of put

    
    def exists(self, key):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################

                return self.m_redis.exists(key)

        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of exists


    def delete_cache(self, queue=None):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################

                if queue == None:
                    self.m_redis.delete(self.key())
                else:
                    self.m_redis.delete(queue)
                return None

        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of delete_cache


    def flush_all(self):
        ############################################################################################
        # START common safety net for high availability connectivity handling
        # This class will automatically retry connections for Redis Instances that are not available
        success = False
        while not success:
            try:
        # END common safety net for high availability connectivity handling
        ############################################################################################

                self.m_redis.flushall()
                return None

        ############################################################################################
        # START common safety net for high availability connectivity handling
                success = True
            except Exception,R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
        # END common safety net for high availability connectivity handling
        ############################################################################################

    # end of flush_all

# end of class RedisWrapper

