# Buscador de Preços

Compara o mesmo produto no **Mercado Livre, Shopee e Google Shopping** (que inclui
Amazon, Magalu e outras lojas), guarda o histórico de preços e diz se o desconto
é **real** ou **inflado** — base para escolher o que divulgar nos canais de promoção.

## Como instalar (uma vez)

1. Instale o Python 3.10+ (python.org).
2. Abra o terminal nesta pasta e rode: `pip install -r requirements.txt`
3. Copie `.env.exemplo` para `.env` e preencha as chaves que já tiver.

## Como usar

| Comando | O que faz |
|---|---|
| `python buscar.py "garrafa térmica" --demo` | Testa com dados fictícios (não precisa de chave) |
| `python buscar.py "garrafa térmica"` | Busca nas fontes configuradas |
| `python buscar.py "air fryer" --alvo 299.90` | Avisa (e manda no Telegram) se ficar abaixo do alvo |
| `python buscar.py --lista produtos.txt` | Busca todos os produtos da lista |
| `python buscar.py --lista produtos.txt --a-cada 60` | Repete a lista a cada 60 minutos |

Os resultados vão para a pasta `saida/`: uma **planilha CSV** (abre no Excel) e
uma **página HTML** com os cards ordenados do menor preço.

## Selos de preço

O histórico (pasta `dados/`) começa a valer depois de 3 buscas do mesmo produto:

- **🔥 menor preço do período** — o mais barato dos últimos 30 dias
- **✅ promoção real** — pelo menos 10% abaixo da mediana de 30 dias
- **⚠️ desconto inflado** — loja anuncia 20%+ de desconto, mas o preço é o de sempre
- **preço normal** / **sem histórico**

## Fontes e o que cada uma precisa

| Fonte | Credencial | Link de afiliado? |
|---|---|---|
| Mercado Livre | `ML_ACCESS_TOKEN` (se a API exigir) | Não — gere no painel de Afiliados ML |
| Shopee | `SHOPEE_APP_ID` + `SHOPEE_SECRET` (Open API de Afiliados) | Sim, já vem pronto |
| Google Shopping | `SERPAPI_KEY` (serpapi.com) | Não — só comparação |
| Amazon | Aguarda liberação da API de Associados | — |

Fonte sem chave fica desligada automaticamente; as outras continuam funcionando.

## Estrutura

```
buscar.py          ← comando principal
fontes/            ← um arquivo por marketplace (fácil adicionar novos)
historico.py       ← histórico de preços e selos
relatorio.py       ← CSV e HTML
produtos.txt       ← sua lista de produtos e preços-alvo
```

## Próximos passos sugeridos (pedir ao Claude Code)

- Ligar com o monitor de cupons: oferta com selo ✅ + cupom ativo vira post automático.
- Gerar o texto do anúncio para Telegram, WhatsApp e Instagram a partir do CSV.
- Painel com evolução de preço por produto.
