from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

DB_URL = "postgresql://aziz:aziz@postgres-container:5432/aziz"

engine = create_engine(DB_URL)
sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
