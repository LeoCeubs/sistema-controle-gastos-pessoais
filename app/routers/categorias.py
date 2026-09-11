from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Categoria, Transacao
from app.schemas import CategoriaIn, CategoriaOut

router = APIRouter(prefix="/categorias", tags=["Categorias"])


def _nome_ja_existe(db: Session, nome: str, ignorar_id: int | None = None) -> bool:
    """RN04: unicidade de nome ignorando maiusculas/minusculas."""
    stmt = select(Categoria.id).where(func.lower(Categoria.nome) == nome.lower())
    if ignorar_id is not None:
        stmt = stmt.where(Categoria.id != ignorar_id)
    return db.execute(stmt).first() is not None


def _buscar(db: Session, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return categoria


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar_categoria(dados: CategoriaIn, db: Session = Depends(get_db)):
    """RF02 - cria uma nova categoria personalizada."""
    nome = dados.nome.strip()
    if _nome_ja_existe(db, nome):
        raise HTTPException(status_code=400, detail="Categoria já cadastrada.")

    categoria = Categoria(nome=nome)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.get("", response_model=list[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    """RF02 - lista todas as categorias cadastradas."""
    return db.scalars(select(Categoria).order_by(Categoria.id)).all()


@router.put("/{categoria_id}", response_model=CategoriaOut)
def atualizar_categoria(
    categoria_id: int, dados: CategoriaIn, db: Session = Depends(get_db)
):
    """RF02 - atualiza o nome de uma categoria existente."""
    categoria = _buscar(db, categoria_id)
    nome = dados.nome.strip()
    if _nome_ja_existe(db, nome, ignorar_id=categoria_id):
        raise HTTPException(status_code=400, detail="Categoria já cadastrada.")

    categoria.nome = nome
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_categoria(categoria_id: int, db: Session = Depends(get_db)):
    """RF02 - remove uma categoria, respeitando a RN05 (integridade referencial)."""
    categoria = _buscar(db, categoria_id)

    em_uso = db.execute(
        select(Transacao.id).where(Transacao.categoria_id == categoria_id).limit(1)
    ).first()
    if em_uso:
        raise HTTPException(status_code=400, detail="Categoria em uso.")

    db.delete(categoria)
    db.commit()
