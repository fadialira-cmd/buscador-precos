"""Fonte de demonstração: dados fictícios para testar o projeto sem chaves.
Use: python buscar.py "garrafa térmica" --demo
"""
import random
from .base import Fonte, Oferta


class Demo(Fonte):
    nome = "Demo"

    def buscar(self, termo, limite=10):
        rnd = random.Random(termo)  # mesmo termo → mesmos produtos
        lojas = ["Mercado Livre", "Shopee", "Amazon", "Magalu"]
        base = rnd.uniform(40, 200)
        ofertas = []
        for i in range(min(limite, 6)):
            preco = round(base * rnd.uniform(0.75, 1.25), 2)
            original = round(preco * rnd.uniform(1.0, 1.6), 2) if rnd.random() > 0.3 else None
            loja = lojas[i % len(lojas)]
            ofertas.append(Oferta(
                fonte=f"Demo ({loja})",
                titulo=f"{termo.title()} — modelo {chr(65 + i)} (exemplo fictício)",
                preco=preco,
                preco_original=original,
                link=f"https://exemplo.com/{termo.replace(' ', '-')}-{i}",
                loja=loja,
                frete_gratis=rnd.random() > 0.5,
                comissao=round(rnd.uniform(3, 12), 1),
                avaliacao=round(rnd.uniform(3.8, 5.0), 1),
            ))
        return ofertas
