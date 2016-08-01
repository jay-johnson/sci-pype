from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, MetaData, Date, DateTime, Float, Boolean
from sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker, relation
from sqlalchemy.ext.declarative import declarative_base 

import sqlalchemy

Base = declarative_base()

##########################################################################################
#
# Lookup Tables 
#
##########################################################################################



##########################################################################################
#
# Primary Tables 
#
##########################################################################################


class BT_Stocks(Base):

    __tablename__               = 'stocks'
    
    id                          = Column(Integer, primary_key = True)
    Symbol                      = Column(String(16)) # Have to support null to start...
    Date                        = Column(DateTime)

    Open                        = Column(Float)
    High                        = Column(Float)
    Low                         = Column(Float)
    Close                       = Column(Float)
    Volume                      = Column(Integer)

    creation_date               = Column(DateTime)
    last_update                 = Column(DateTime)

# end of BT_Stocks


