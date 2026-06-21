"""
Envio de notificações para o Teams via fluxo do Power Automate.

O fluxo do Power Automate expõe uma URL de webhook (gatilho HTTP) que recebe
um JSON e posta a mensagem diretamente no chat pessoal do destinatário,
usando o "Bot do Fluxo". Veja o README.md -> "Configurando o Power Automate"
para o passo a passo de criação do fluxo.
"""
import logging

import requests

logger = logging.getLogger(__name__)


def _enviar(webhook_url: str, payload: dict) -> bool:
    try:
        resposta = requests.post(webhook_url, json=payload, timeout=15)
        resposta.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Falha ao enviar notificação para o Teams: %s", exc)
        return False


def enviar_alerta_processo(webhook_url: str, destinatario_email: str, numero_processo: str, link_processo: str = "") -> bool:
    payload = {
        "destinatario": destinatario_email,
        "processo": numero_processo,
        "mensagem": f"📌 O processo {numero_processo} teve uma movimentação nova no SEI.",
        "link": link_processo,
    }
    sucesso = _enviar(webhook_url, payload)
    if sucesso:
        logger.info("Alerta enviado para o processo %s", numero_processo)
    return sucesso


def enviar_alerta_generico(webhook_url: str, destinatario_email: str, mensagem: str) -> bool:
    payload = {
        "destinatario": destinatario_email,
        "processo": "",
        "mensagem": mensagem,
        "link": "",
    }
    return _enviar(webhook_url, payload)
