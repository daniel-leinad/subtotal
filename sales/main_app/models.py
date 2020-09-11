from pyramid.security import Allow, Everyone
from datetime import datetime, timezone
from dateutil import tz

import pytz
import sqlalchemy as sa 
from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    Float,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import register

DBSession = scoped_session(sessionmaker())
register(DBSession)
Base = declarative_base()

class TimeStamp(sa.types.TypeDecorator):
    impl = sa.types.DateTime
    LOCAL_TIMEZONE = datetime.utcnow().astimezone().tzinfo

    def process_bind_param(self, value: datetime, dialect):
        if value.tzinfo is None:
            value = value.astimezone(self.LOCAL_TIMEZONE)

        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

class Sale(Base):
    __tablename__ = 'sales'
    uid = Column(Integer, primary_key=True)
    date = Column(TimeStamp)
    num = Column(Integer, unique=True)

class Product(Base):
    __tablename__ = 'products'
    uid = Column(Integer, primary_key=True)
    sale_id = Column(Integer)
    product = Column(Text)
    price = Column(Float)
    amount = Column(Float)

class Root(object):
    __acl__ = [(Allow, Everyone, 'view'),
               (Allow, 'group:editors', 'edit')]

    def __init__(self, request):
        pass
