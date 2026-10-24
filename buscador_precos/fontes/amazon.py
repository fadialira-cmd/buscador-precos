"""Amazon — reservado para a API de Associados.

A Amazon só libera a API de produtos depois que a conta de Associados tem
vendas qualificadas. Até lá, esta fonte fica desligada e o Google Shopping
cobre a comparação com a Amazon.

Quando a API for liberada: preencha AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY e
AMAZON_PARTNER_TAG no .env e peça ao Claude Code para implementar a busca
seguindo a documentação atual do programa de Associados.
"""
import os
from .base import Fonte


class Amazon(Fonte):
    nome = "Amazon"

    def configurada(self):
        return all(os.getenv(k) for k in
                   ("AMAZON_ACCESS_KEY", "AMAZON_SECRET_KEY", "AMAZON_PARTNER_TAG"))

    def buscar(self, termo, limite=10):
        raise NotImplementedError(
            "Busca Amazon ainda não implementada: aguarda liberação da API de Associados.")
