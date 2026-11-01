import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

# garante o diretorio do arquivo .db antes de abrir a conexao
if DATABASE_URL.startswith("sqlite"):
    db_path = DATABASE_URL.split("sqlite:///")[-1]
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Cria as tabelas e semeia as categorias padrao (RN06)."""
    from app.models import Categoria  # import tardio: models depende de Base

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if db.query(Categoria).count() == 0:
            db.add_all(
                [
                    Categoria(nome="Alimentação"),
                    Categoria(nome="Salário"),
                    Categoria(nome="Outros"),
                ]
            )
            db.commit()
