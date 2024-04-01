from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    CheckConstraint,
    ForeignKey,
    BigInteger,
)
from sqlalchemy.sql import func
from database import Base
from datetime import datetime, timedelta, date
from sqlalchemy.orm import relationship


class Stagaire(Base):
    __tablename__ = "stagaire"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    ecole = Column(String(50), index=True)
    email = Column(String(50), unique=True, index=True)
    telephone = Column(Integer, unique=True, index=True)
    naissance = Column(Date, index=True)
    start_day = Column(Date, index=True)
    end_day = Column(Date, index=True)
    encadrant_id = Column(Integer, ForeignKey("employe.id"))

    @property
    def encadrant(self):
        return self.employe


class Employe(Base):
    __tablename__ = "employe"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    telephone = Column(BigInteger, unique=True, index=True)
    email = Column(String(50), unique=True, index=True)
    password = Column(String(500), index=True)
    position = Column(String(50), index=True)
    naissance = Column(Date, index=True)
    start_day = Column(Date, index=True)
    salary = Column(BigInteger, index=True)
    admin = Column(Boolean, default=False)
    stagiaire_id = Column(Integer, ForeignKey("stagaire.id"))
    is_authenticated = Column(Boolean, default=False)
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.now())
    session_expiration_minutes = 1

    @property
    def stagiaire(self):
        return self.stagiaire

    @stagiaire.setter
    def stagiaire(self, value):
        self.stagiaire_id = value.id if value else None


class Demand(Base):
    __tablename__ = "demand"
    id = Column(Integer, primary_key=True, index=True)
    id_emp = Column(Integer, index=True)
    name = Column(String(50), index=True)
    password = Column(String(500), index=True)
    selectchoix = Column(String(50), index=True)
    startdate = Column(Date, index=True)
    enddate = Column(Date, index=True)
    statut = Column(String(50), index=True, nullable=False, default="pending")
    __table_args__ = (
        CheckConstraint(
            statut.in_(["declined", "approved", "pending"]), name="check_statut"
        ),
    )
