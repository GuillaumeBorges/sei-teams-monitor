"""
Camada de acesso ao banco SQLite que guarda o estado de cada processo.

Lógica de negócio (a parte importante):

  - Cada processo tem um estado "tem_novidade" (True/False), espelhando o
    indicador de movimentação não vista que o próprio SEI mostra na lista.
  - Cada processo também tem "notificado_atual": já mandamos aviso no Teams
    para a novidade ATUAL desse processo?
  - Só disparamos um aviso novo quando o processo TRANSICIONA de
    "sem novidade" para "com novidade" (ou aparece pela primeira vez já com
    novidade, fora da primeira carga). Isso evita ficar reavisando a cada
    5 minutos sobre algo que já foi avisado e ainda não foi tratado.
  - Quando o processo deixa de ter novidade (alguém abriu/leu no SEI),
    resetamos o estado para poder avisar de novo no futuro, se uma nova
    movimentação acontecer depois.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS processos (
    numero TEXT PRIMARY KEY,
    tem_novidade INTEGER NOT NULL DEFAULT 0,
    notificado_atual INTEGER NOT NULL DEFAULT 0,
    primeira_vez_visto TEXT NOT NULL,
    ultima_verificacao TEXT NOT NULL,
    ultima_notificacao TEXT
);

CREATE TABLE IF NOT EXISTS execucoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sucesso INTEGER NOT NULL,
    total_processos INTEGER,
    total_notificados INTEGER,
    mensagem TEXT
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def conectar(caminho_db: str):
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def buscar_processo(conn, numero: str):
    cur = conn.execute("SELECT * FROM processos WHERE numero = ?", (numero,))
    return cur.fetchone()


def primeira_carga(conn) -> bool:
    """True se o banco ainda não tem nenhum processo catalogado (primeira execução)."""
    cur = conn.execute("SELECT COUNT(*) AS total FROM processos")
    return cur.fetchone()["total"] == 0


def upsert_processo(conn, numero: str, tem_novidade: bool, eh_primeira_execucao: bool):
    existente = buscar_processo(conn, numero)
    agora = _now_iso()

    if existente is None:
        # Na primeira execução geral do programa, catalogamos tudo sem marcar
        # como pendente de notificação (senão avisaria de uma vez de tudo que
        # já estava parado antes de a automação existir).
        ja_notificado = eh_primeira_execucao or (not tem_novidade)
        conn.execute(
            """INSERT INTO processos
               (numero, tem_novidade, notificado_atual, primeira_vez_visto, ultima_verificacao)
               VALUES (?, ?, ?, ?, ?)""",
            (numero, int(tem_novidade), int(ja_notificado), agora, agora),
        )
        return

    novidade_anterior = bool(existente["tem_novidade"])
    notificado_anterior = bool(existente["notificado_atual"])

    if tem_novidade and not novidade_anterior:
        # Transição "sem novidade" -> "com novidade": é uma novidade fresca.
        notificado_atual = False
    elif tem_novidade and novidade_anterior:
        # Continua com novidade pendente; mantém o que já tinha (se já
        # notificamos, não notifica de novo; se ainda não, segue pendente).
        notificado_atual = notificado_anterior
    else:
        # Sem novidade agora (foi lido, ou nunca teve) -> nada pendente.
        notificado_atual = True

    conn.execute(
        """UPDATE processos
           SET tem_novidade = ?, notificado_atual = ?, ultima_verificacao = ?
           WHERE numero = ?""",
        (int(tem_novidade), int(notificado_atual), agora, numero),
    )


def processos_pendentes_de_notificacao(conn):
    cur = conn.execute(
        "SELECT * FROM processos WHERE tem_novidade = 1 AND notificado_atual = 0"
    )
    return cur.fetchall()


def marcar_como_notificado(conn, numero: str):
    conn.execute(
        "UPDATE processos SET notificado_atual = 1, ultima_notificacao = ? WHERE numero = ?",
        (_now_iso(), numero),
    )


def registrar_execucao(conn, sucesso: bool, total_processos: int, total_notificados: int, mensagem: str = ""):
    conn.execute(
        """INSERT INTO execucoes (timestamp, sucesso, total_processos, total_notificados, mensagem)
           VALUES (?, ?, ?, ?, ?)""",
        (_now_iso(), int(sucesso), total_processos, total_notificados, mensagem),
    )
