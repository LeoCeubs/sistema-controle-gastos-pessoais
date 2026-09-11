import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import Select, extract, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Categoria, Transacao
from app.schemas import TransacaoIn, TransacaoOut

router = APIRouter(prefix="/transacoes", tags=["Transações"])


def _filtrar(
    stmt: Select,
    mes: int | None,
    ano: int | None,
    categoria: int | None,
) -> Select:
    """RF05 - filtros por mes/ano/categoria. Sem resultado nao e erro (RN08)."""
    if mes is not None:
        stmt = stmt.where(extract("month", Transacao.data) == mes)
    if ano is not None:
        stmt = stmt.where(extract("year", Transacao.data) == ano)
    if categoria is not None:
        stmt = stmt.where(Transacao.categoria_id == categoria)
    return stmt


def _validar_categoria(db: Session, categoria_id: int) -> None:
    if db.get(Categoria, categoria_id) is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")


def _buscar(db: Session, transacao_id: int) -> Transacao:
    transacao = db.get(Transacao, transacao_id)
    if transacao is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")
    return transacao


@router.post("", response_model=TransacaoOut, status_code=status.HTTP_201_CREATED)
def criar_transacao(dados: TransacaoIn, db: Session = Depends(get_db)):
    """RF01 - cadastra receita ou despesa (RN01/RN02/RN03 validadas no schema)."""
    _validar_categoria(db, dados.categoria_id)

    transacao = Transacao(**dados.model_dump())
    transacao.tipo = dados.tipo.value
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    return transacao


@router.get("", response_model=list[TransacaoOut])
def listar_transacoes(
    db: Session = Depends(get_db),
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=1900, le=2999),
    categoria: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """RF03/RF05 - lista as movimentacoes com filtros e paginacao."""
    stmt = select(Transacao).options(selectinload(Transacao.categoria))
    stmt = _filtrar(stmt, mes, ano, categoria)
    stmt = stmt.order_by(Transacao.data.desc(), Transacao.id.desc())
    return db.scalars(stmt.limit(limit).offset(offset)).all()


# precisa vir antes de /{transacao_id}, senao o path param captura "exportar"
@router.get("/exportar", tags=["Resumos e Exportação"])
def exportar_transacoes(
    db: Session = Depends(get_db),
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=1900, le=2999),
    categoria: int | None = Query(default=None, ge=1),
):
    """RF09 - exporta as movimentacoes filtradas em CSV."""
    stmt = select(Transacao).options(selectinload(Transacao.categoria))
    stmt = _filtrar(stmt, mes, ano, categoria).order_by(Transacao.data, Transacao.id)

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["id", "data", "tipo", "categoria", "valor", "descricao"])
    for t in db.scalars(stmt):
        writer.writerow(
            [
                t.id,
                t.data.isoformat(),
                t.tipo,
                t.categoria.nome,
                f"{t.valor:.2f}",
                t.descricao or "",
            ]
        )

    # BOM para o Excel abrir acentuacao corretamente
    conteudo = "﻿" + buffer.getvalue()
    return Response(
        content=conteudo,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="relatorio_gastos.csv"'
        },
    )


@router.get("/{transacao_id}", response_model=TransacaoOut)
def consultar_transacao(transacao_id: int, db: Session = Depends(get_db)):
    """RF03 - consulta uma movimentacao especifica pelo ID."""
    return _buscar(db, transacao_id)


@router.put("/{transacao_id}", response_model=TransacaoOut)
def atualizar_transacao(
    transacao_id: int, dados: TransacaoIn, db: Session = Depends(get_db)
):
    """Ajuste 1 da SDD - edicao de uma movimentacao existente."""
    transacao = _buscar(db, transacao_id)
    _validar_categoria(db, dados.categoria_id)

    for campo, valor in dados.model_dump().items():
        setattr(transacao, campo, valor)
    transacao.tipo = dados.tipo.value

    db.commit()
    db.refresh(transacao)
    return transacao


@router.delete("/{transacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_transacao(transacao_id: int, db: Session = Depends(get_db)):
    """RF04 - exclui uma movimentacao pelo ID."""
    transacao = _buscar(db, transacao_id)
    db.delete(transacao)
    db.commit()
