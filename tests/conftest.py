import os
import tempfile

# RNF05: a suite roda num SQLite temporario, nunca no banco do usuario.
# Precisa vir antes de qualquer import de `app`, que le DATABASE_URL ao carregar.
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "teste.db")

import pytest  # noqa: E402

from app.database import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def banco_de_teste():
    """Cria tabelas e categorias padrao (RN06): o TestClient sem `with` nao roda o lifespan."""
    init_db()
