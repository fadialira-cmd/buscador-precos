"""Shopee — Open API de Afiliados (GraphQL).

Precisa de SHOPEE_APP_ID e SHOPEE_SECRET, liberados no painel de Afiliados
da Shopee (Open API). O offerLink já vem como link de afiliado.
Confira na documentação da Shopee se os nomes dos campos mudaram.
"""
import hashlib
import json
import os
import time
import requests
from .base import Fonte, Oferta

URL = "https://open-api.affiliate.shopee.com.br/graphql"
QUERY = """
query($keyword: String, $limit: Int) {
  productOfferV2(keyword: $keyword, limit: $limit, sortType: 2) {
    nodes {
      itemId productName priceMin priceMax priceDiscountRate
      commissionRate offerLink productLink imageUrl shopName sales ratingStar
    }
  }
}
"""


class Shopee(Fonte):
    nome = "Shopee"

    def __init__(self):
        self.app_id = os.getenv("SHOPEE_APP_ID", "")
        self.secret = os.getenv("SHOPEE_SECRET", "")

    def configurada(self):
        return bool(self.app_id and self.secret)

    def buscar(self, termo, limite=10):
        payload = json.dumps({"query": QUERY,
                              "variables": {"keyword": termo, "limit": limite}},
                             separators=(",", ":"))
        ts = str(int(time.time()))
        assinatura = hashlib.sha256(
            (self.app_id + ts + payload + self.secret).encode()).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={self.app_id}, "
                             f"Timestamp={ts}, Signature={assinatura}",
        }
        r = requests.post(URL, data=payload, headers=headers, timeout=20)
        r.raise_for_status()
        dados = r.json()
        if dados.get("errors"):
            raise RuntimeError(f"Shopee: {dados['errors'][0].get('message')}")
        ofertas = []
        for n in dados["data"]["productOfferV2"]["nodes"]:
            preco = float(n.get("priceMin") or 0)
            desc = n.get("priceDiscountRate") or 0
            original = round(preco / (1 - desc / 100), 2) if 0 < desc < 100 else None
            ofertas.append(Oferta(
                fonte=self.nome,
                titulo=n.get("productName", ""),
                preco=preco,
                preco_original=original,
                link=n.get("offerLink") or n.get("productLink", ""),
                loja=n.get("shopName", ""),
                imagem=n.get("imageUrl", ""),
                comissao=round(float(n.get("commissionRate") or 0) * 100, 1),
                vendas=n.get("sales"),
                avaliacao=float(n.get("ratingStar") or 0) or None,
                extra={"id": n.get("itemId")},
            ))
        return ofertas
