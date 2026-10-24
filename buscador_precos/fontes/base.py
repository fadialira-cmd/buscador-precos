"""Modelo comum de oferta e de fonte de preços."""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Oferta:
    fonte: str                       # "Mercado Livre", "Shopee", ...
    titulo: str
    preco: float                     # preço atual (R$)
    link: str                        # link do produto (de afiliado, quando a fonte gera)
    preco_original: Optional[float] = None   # preço "de" exibido pela loja
    loja: str = ""
    imagem: str = ""
    frete_gratis: Optional[bool] = None
    comissao: Optional[float] = None         # % de comissão de afiliado, se a fonte informar
    vendas: Optional[int] = None
    avaliacao: Optional[float] = None
    extra: dict = field(default_factory=dict)

    @property
    def desconto_anunciado(self) -> Optional[float]:
        if self.preco_original and self.preco_original > self.preco:
            return round((1 - self.preco / self.preco_original) * 100, 1)
        return None

    def to_dict(self):
        d = asdict(self)
        d["desconto_anunciado"] = self.desconto_anunciado
        return d


class Fonte:
    nome = "base"

    def configurada(self) -> bool:
        """True quando as credenciais necessárias estão no .env."""
        return True

    def buscar(self, termo: str, limite: int = 10) -> list[Oferta]:
        raise NotImplementedError
