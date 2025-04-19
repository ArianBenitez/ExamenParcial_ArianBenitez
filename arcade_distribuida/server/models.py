from sqlalchemy import Column, Integer, Boolean, String, DateTime
from server.db import Base

class ResultadoNReinas(Base):
    __tablename__ = 'nreinas'
    id = Column(Integer, primary_key=True)
    N = Column(Integer, nullable=False)
    resuelto = Column(Boolean, nullable=False)
    intentos = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)

class ResultadoKnightTour(Base):
    __tablename__ = 'knight_tour'
    id = Column(Integer, primary_key=True)
    # JSON y código cliente/servidor deben usar 'posicion_inicial' (sin acento)
    posicion_inicial = Column(String, nullable=True)
    movimientos = Column(Integer, nullable=False)
    completado = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, nullable=False)

class ResultadoHanoi(Base):
    __tablename__ = 'hanoi'
    id = Column(Integer, primary_key=True)
    discos = Column(Integer, nullable=False)
    movimientos = Column(Integer, nullable=False)
    completado = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, nullable=False)
