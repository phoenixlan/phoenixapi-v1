import os

from pyramid.authorization import Allow, Everyone

from sqlalchemy import (
	Column,
	Integer,
	Text,
	MetaData,
	create_engine
)

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
	scoped_session,
	sessionmaker,
)
from zope.sqlalchemy import register

import logging
log = logging.getLogger(__name__)

meta = MetaData(naming_convention={
		"ix": "ix_%(column_0_label)s",
		"uq": "uq_%(table_name)s_%(column_0_name)s",
		"ck": "ck_%(table_name)s_%(constraint_name)s",
		"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
		"pk": "pk_%(table_name)s"
	  })


Base = declarative_base(metadata=meta)


def get_postgresql_url(username, password, host, db):
	return "postgresql://%s:%s@%s/%s" % (username, password, host, db)

def setup_connections(username=None, password=None, host=None):
	username = os.environ['POSTGRES_USER'] if username is None else username
	password = os.environ['POSTGRES_PASSWORD'] if password is None else password
	host = os.environ['DB_HOST'] if host is None else host
	log.info("Setting up database connections")

	engine = create_engine(get_postgresql_url(username, password, host, "phoenix"))

	db = scoped_session(sessionmaker(autoflush=False))
	register(db)

	db.configure(bind=engine)
	# TODO
	Base.metadata.bind = engine

	log.info("Done setting up database connections")
	return db