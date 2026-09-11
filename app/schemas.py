from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TipoTransacao(str, Enum):
    receita = "receita"
    despesa = "despesa"


# ---------- Categorias ----------


class CategoriaIn(BaseModel):
    nome: str = Field(min_length=1, max_length=80)


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


# ---------- Transacoes ----------


class TransacaoIn(BaseModel):
    # RN01: todos obrigatorios (menos descricao)
    # RN02: valor estritamente maior que zero
    # RN03: `date` do Pydantic exige ISO 8601 e rejeita data inexistente
    valor: float = Field(gt=0)
    data: date
    tipo: TipoTransacao
    categoria_id: int
    descricao: str | None = Field(default=None, max_length=255)


class TransacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    valor: float
    data: date
    tipo: TipoTransacao
    # a SDD mostra `categoria_id` na resposta do POST/PUT e o objeto `categoria`
    # aninhado na listagem; devolvemos os dois para atender aos dois contratos
    categoria_id: int
    categoria: CategoriaOut
    descricao: str | None


# ---------- Resumos ----------


class SaldoOut(BaseModel):
    saldo_atual: float


class ResumoOut(BaseModel):
    total_receitas: float
    total_despesas: float
    saldo_periodo: float
