from fastapi import FastAPI, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import engine, Base, get_db

# Cria as tabelas no SQLite ao iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Controle de Gastos Pessoais")

@app.post("/transacoes", response_model=schemas.TransacaoResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_transacao(dados: schemas.TransacaoCreate, db: Session = Depends(get_db)):
    nova_transacao = models.Transacao(
        descricao=dados.descricao,
        valor=dados.valor,
        tipo=dados.tipo.lower(),
        categoria=dados.categoria.lower()
    )
    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)
    return nova_transacao

@app.get("/transacoes", response_model=List[schemas.TransacaoResponse])
def listar_transacoes(categoria: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Transacao)
    if categoria:
        query = query.filter(models.Transacao.categoria == categoria.lower())
    return query.all()