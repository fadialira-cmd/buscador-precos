"""Mercado Livre — API pública de busca (sites/MLB/search).

A API pode exigir um access token do Mercado Livre Developers. Coloque em
ML_ACCESS_TOKEN no .env. O link retornado é o do produto: para comissão,
converta-o em link de afiliado no painel de Afiliados do ML (não há API
pública para isso).
"""
import os
import requests
from .base import Fonte, Oferta

URL = "https://api.mercadolibre.com/sites/MLB/search"


class MercadoLivre(Fonte):
    nome = "Mercado Livre"

    def __init__(self):
        self.token = os.getenv("ML_ACCESS_TOKEN", "")

    def configurada(self):
        return True  # tenta mesmo sem token; se a API exigir, avisa no erro

    def buscar(self, termo, limite=10):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        r = requests.get(URL, params={"q": termo, "limit": limite},
                         headers=headers, timeout=20)
        if r.status_code in (401, 403):
            raise RuntimeError("API do ML pediu autenticação: preencha ML_ACCESS_TOKEN no .env")
        r.raise_for_status()
        ofertas = []
        for it in r.json().get("results", []):
            ofertas.append(Oferta(
                fonte=self.nome,
                titulo=it.get("title", ""),
                preco=float(it.get("price") or 0),
                preco_original=it.get("original_price"),
                link=it.get("permalink", ""),
                loja=(it.get("seller") or {}).get("nickname", ""),
                imagem=it.get("thumbnail", ""),
                frete_gratis=(it.get("shipping") or {}).get("free_shipping"),
                extra={"id": it.get("id")},
            ))
        return ofertas
