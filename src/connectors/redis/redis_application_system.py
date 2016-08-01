import sys, json

sys.path.append("/opt/src")

from logger.logger import Logger
from connectors.redis.redis_pickle_application  import RedisPickleApplication
from connectors.redis.redis_json_application    import RedisJSONApplication

class RedisApplicationSystem:

    def __init__(self, logger, debug=False):

        self.m_name         = "PCRA"
        self.m_debug        = debug
        self.m_log          = logger
        self.m_connector    = {}

    # end of __init__
    

    def lg(self, msg, level=6):

        if self.m_log:
            full_msg = self.m_name + ": " + msg

            if self.m_debug:
                print full_msg

            self.m_log.log(full_msg, level)

        return None
    # end of lg


    def return_connectors(self, json_config):

        self.lg("Parsing connector stream(" + str(json_config) + ")", 5)

        for redis_node in json_config:

            name          = redis_node["Name"]
            redis_type    = redis_node["Type"]
            redis_address = redis_node["Address List"]
            redis_array   = redis_address.split()
            redis_server_array = redis_array[0].split(":")
            redis_host    = redis_server_array[0]
            redis_port    = int(redis_server_array[1])
            redis_debug   = bool(redis_node["Debug"] == "True")
            
            redis_request_key   = redis_node["Request Key"]
            redis_response_key  = redis_node["Response Key"]

            if   redis_type == "Pickle":
                self.lg("Connecting RA(" + name + ") Pickle Address List(" + str(redis_address) + ") REQ(" + redis_request_key + ") RES(" + redis_response_key + ")", 5)
                self.m_connector[name] = RedisPickleApplication(name, redis_host, redis_port, "", self.m_log, redis_request_key, redis_response_key, redis_debug)

            elif redis_type == "JSON":
                self.lg("Connecting RA(" + name + ") JSON Address List(" + str(redis_address) + ") REQ(" + redis_request_key + ") RES(" + redis_response_key + ")", 5)
                self.m_connector[name] = RedisJSONApplication(name, redis_host, redis_port, "", self.m_log, redis_request_key, redis_response_key, redis_debug)

            else:
                self.lg("Unknown Redis Connector Type(" + str(redis_node) + ")", 0)
    

        self.lg("Connectors(" + str(len(self.m_connector)) + ")", 7)
        return self.m_connector
    # end of return_connectors


    def connect_all(self):
        self.lg("Connecting All", 5)
        for i in self.m_connector:
            self.lg("Connecting to Redis(" + str(i) + ")", 7)
            self.m_connector[i].connect()
            self.m_connector[i].m_state = "Connected"
        return None
    # end of connect_all


    def disconnect_all(self):
        for i in self.m_connector:
            self.lg("Disconnecting from Redis(" + str(i) + ")", 5)
            self.m_connector[i].disconnect()
            self.m_connector[i].m_state = "Disconnected"
        return None
    # end of disconnect_all


# end of RedisApplicationSystem

