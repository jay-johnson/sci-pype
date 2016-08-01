from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, MetaData, Date, DateTime, Float, Boolean
from sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker, relation
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy

class DatabaseApplication:

    def __init__(self, name, json_config, logger):

        self.m_name           = name
        self.m_log            = logger

        self.m_type           = json_config["Type"]
        self.m_address_list   = json_config["Address List"]
        self.m_user           = json_config["User"]
        self.m_password       = json_config["Password"]
        self.m_database_name  = json_config["Database Name"]

        # Super nasty bug when this is True
        self.m_autocommit     = False
        if json_config["Autocommit"] == "True":
            self.m_autocommit = True
        
        self.m_autoflush      = False
        if json_config["Autoflush"] == "True":
            self.m_autoflush  = True

        self.m_debug          = False
        if json_config["Debug"] == "True":
            self.m_debug      = True

        self.m_connection_str = ""

        self.m_session        = None
        self.m_connection     = None
        self.m_engine         = None

    # end of __init__


    def lg(self, msg, level=6):

        full_msg = self.m_name + ": " + msg

        if self.m_debug:
            print full_msg

        if self.m_log != None:
            self.m_log.log(full_msg, level)

        return None
    # end of lg


    def build_connection_string(self):

        if self.m_type == "MySQL":
            self.m_connection_str = "mysql://" + str(self.m_user) + ":" + str(self.m_password) + "@" + str(self.m_address_list.split()[0]) + "/" + str(self.m_database_name)
        else:
            self.lg("Unable to connect to database type(" + str(self.m_type) + ")", 0)
            self.m_connection_str = None

        return None
    # end of build_connection_string


    def connect(self):

        self.build_connection_string()
        if self.m_connection_str == None:
            self.lg("Not connecting to this database", 0)
            return None
        
        self.lg("Connecting to databases(" + str(self.m_connection_str) + ") Autocommit(" + str(self.m_autocommit) + ") Autoflush(" + str(self.m_autoflush) + ")", 7)

        Base = declarative_base()

        self.m_engine       = create_engine(self.m_connection_str,
                                                echo=False)

        self.m_connection   = self.m_engine.connect()
        self.m_session      = scoped_session(sessionmaker(autocommit  = self.m_autocommit,
                                                            autoflush = self.m_autoflush,
                                                            bind      = self.m_engine))

        self.lg("Connected to DB(" + str(self.m_name) + ") DBTables(" + str(self.m_database_name) + ")", 7)
        return None
    # end of connect
    

    def disconnect(self):
        return None
    # end of disconnect

    def add_record(self, record):
        self.m_session.add(record)
        return None
    # end of add_record


    def commit_all(self):
        self.m_session.commit()
        return None
    # end of commit_all

# end of DatabaseApplication
