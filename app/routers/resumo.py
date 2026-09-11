from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transacao
from app.schemas import ResumoOut, SaldoOut

router = APIRouter(tags=["Resumos e Exportação"])


def _totais(db: Session, mes: int | None, ano: int | None) -> tuple[float, float]:
    """Soma receitas e despesas do periodo. coalesce garante 0.0 (RN08)."""
    stmt = select(
        Transacao.tipo, func.coalesce(func.sum(Transacao.valor), 0.0)
    ).group_by(Transacao.tipo)
    if mes is not None:
        stmt = stmt.where(extract("month", Transacao.data) == mes)
    if ano is not None:
        stmt = stmt.where(extract("year", Transacao.data) == ano)

    somas = dict(db.execute(stmt).all())
    return float(somas.get("receita", 0.0)), float(somas.get("despesa", 0.0))


@router.get("/saldo", response_model=SaldoOut)
def consultar_saldo(db: Session = Depends(get_db)):
    """RF06 - saldo atual = receitas - despesas. Pode ser negativo (RN07)."""
    receitas, despesas = _totais(db, None, None)
    return SaldoOut(saldo_atual=round(receitas - despesas, 2))


@router.get("/resumo", response_model=ResumoOut)
def consultar_resumo(
    db: Session = Depends(get_db),
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=1900, le=2999),
):
    """RF07 - resumo financeiro consolidado do periodo."""
    receitas, despesas = _totais(db, mes, ano)
    return ResumoOut(
        total_receitas=round(receitas, 2),
        total_despesas=round(despesas, 2),
        saldo_periodo=round(receitas - despesas, 2),
    )
