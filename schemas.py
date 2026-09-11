from pydantic import BaseModel, Field
from datetime import datetime

class TransacaoCreate(BaseModel):
    descricao: str = Field(..., min_length=1, example="Almoço")
    valor: float = Field(..., gt=0, example=35.50)
    tipo: str = Field(..., pattern="^(receita|despesa)$", example="despesa")
    categoria: str = Field(..., min_length=1, example="alimentacao")

class TransacaoResponse(TransacaoCreate):
    id: int
    data: datetime

    class Config:
        from_attributes = True