from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    tipo = Column(String, nullable=False)  # receita ou despesa
    categoria = Column(String, nullable=False)  # alimentacao, transporte, etc.
    data = Column(DateTime, default=datetime.utcnow)