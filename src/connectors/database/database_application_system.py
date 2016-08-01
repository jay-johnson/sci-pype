import sys, json
from   sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, MetaData, Date, DateTime, Float, Boolean
from   sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker, relation
from   sqlalchemy.ext.declarative import declarative_base
import sqlalchemy

sys.path.append("/opt/src")

from logger.logger import Logger

from connectors.database.database_application import DatabaseApplication

class DatabaseApplicationSystem:

    def __init__(self, logger, debug=False):

        self.m_name         = "DatabaseAppSystem"
        self.m_debug        = debug
        self.m_log          = logger
        self.m_connector    = {}

    # end of __init__
    

    def lg(self, msg, level=6):

        full_msg = self.m_name + ": " + msg

        if self.m_debug:
            print full_msg

        if self.m_log != None:
            self.m_log.log(full_msg, level)

        return None
    # end of lg


    def return_connectors(self, json_config):
        self.disconnect_all()

        self.lg("Parsing connector stream(" + str(json_config) + ")", 7)

        for database_node in json_config:

            name          = database_node["Name"]
            database_type = database_node["Type"]

            if database_type == "MySQL":
                self.lg("DB App(" + str(name) + ") Address List(" + str(database_node["Address List"]) + ")", 5)
                self.m_connector[name] = DatabaseApplication(name, database_node, self.m_log)

            else:
                self.lg("Unknown Database Connector Type(" + str(database_node) + ")", 0)

        self.lg("Connectors(" + str(len(self.m_connector)) + ")", 7)
        return self.m_connector
    # end of return_connectors
    
    
    def connect_all(self):
        self.lg("Connecting All", 5)
        for i in self.m_connector:
            self.lg("Connecting to Database(" + str(i) + ")", 5)
            self.m_connector[i].connect()
            self.lg("Connected(" + str(i) + ")", 5)
        return None
    # end of connect_all


    def disconnect_all(self):
        for i in self.m_connector:
            self.lg("Disconnecting from Database(" + str(i) + ")", 7)
            self.m_connector[i].disconnect()
        return None
    # end of disconnect_all

# end of DatabaseApplicationSystem
