from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    transacoes: Mapped[list["Transacao"]] = relationship(back_populates="categoria")


class Transacao(Base):
    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # receita | despesa
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id"), nullable=False, index=True
    )
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    categoria: Mapped[Categoria] = relationship(back_populates="transacoes")
