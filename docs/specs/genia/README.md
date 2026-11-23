# Genia: integração com a API Gemini

Specs do pacote `cmj/utils/genia`, uma por capacidade. Marcadores das regras: `[observado]` veio da
leitura do código, `[acordado]` foi confirmado pelo responsável, `[desejado]` ainda não existe e
`[implementado]` foi acordado e tem teste. IDs são estáveis: não reutilize nem renumere.

| Spec | Prefixo | Classe | Módulo |
| --- | --- | --- | --- |
| [conexao-e-cotas.md](./conexao-e-cotas.md) | `GENIA-BASE` | `IAGenaiBase` | `base.py` |
| [chat.md](./chat.md) | `GENIA-CHAT` | `IAChatService` | `chat.py` |
| [embeddings.md](./embeddings.md) | `GENIA-EMB` | `IAEmbeddingService` | `embeddings.py` |
| [classificacao-materia.md](./classificacao-materia.md) | `GENIA-CLA` | `IAClassificacaoMateriaService` | `classificacao.py` |
| [similaridade.md](./similaridade.md) | `GENIA-SIM` | `IAAnaliseSimilaridadeService` | `similaridade.py` |
| [ementa-emenda-coletiva.md](./ementa-emenda-coletiva.md) | `GENIA-LOA` | `IAEmentaEmendaColetiva` | `loa_agrupamento.py` |

Testes: `python -m pytest cmj/utils/genia cmj/search/test_chat_manager.py cmj/search/test_embeddings.py`.
Cada teste de `cmj/utils/genia/test_genia.py` aponta a regra com `@pytest.mark.spec("<ID>")`.

## Estrutura

```
IAGenaiBase                      conexão, cota e geração; sem regra de funcionalidade
├── IAChatService                chat RAG: system instruction, limites de uso, cota "IAChatService"
├── IAEmbeddingService           vetorização; isento de cota
├── IAClassificacaoMateriaService  cota "IAClassificacaoMateriaService"
├── IAAnaliseSimilaridadeService   cota "IAAnaliseSimilaridadeService"
└── IAEmentaEmendaColetiva       modelo fixo; isento de cota
```

| Arquivo | Conteúdo |
| --- | --- |
| `__init__.py` | Reexporta `IAGenaiBase`, `IAQuotaUnavailableError`, `IAChatService` e `IAEmbeddingService` |
| `extracao.py` | Texto de PDF com OCR de páginas ilegíveis (funções, sem classe) |
| `prompts_similaridade.py`, `prompts_loa_agrupamento.py` | Textos dos prompts, em uso e históricos |
| `genia_system_instruction_v3.py` | System instruction do chat em uso |
| `genia_system_instruction_v1.py`, `_v2.py` | Versões anteriores, não importadas por nenhum módulo |

## Como criar um serviço

1. Herde de `IAGenaiBase` em um módulo próprio do pacote.
2. Declare a cota: `quota_service_name` com uma chave de `IAQuota.ServicosAutorizados`
   (`cmj/core/models.py:1108`), ou `quota_exempt = True` com `ia_model_name` fixo. Chave nova exige
   migration de `cmj.core`, porque as chaves são `choices` do campo.
3. Sobrescreva só os parâmetros de geração que diferem do padrão. `None` deixa o padrão da API.
4. Chame `self.generate_content(...)`. Não chame `self.client.models.generate_content` direto: isso
   pula o controle de cota.
5. Escreva a spec da capacidade nesta pasta e os testes ligados aos IDs.

## Dúvidas transversais

As dúvidas de cada capacidade estão na spec correspondente. As de maior risco ainda abertas:

1. [ementa-emenda-coletiva.md](./ementa-emenda-coletiva.md) D1: o serviço chama a API sem limite de
   cota, com modelo fixo no código. Em [embeddings.md](./embeddings.md) a falta de cota foi aceita.
2. [chat.md](./chat.md) D1: a chave legada `IAGenaiBase` ainda existe em `IAQuota` e deve sair depois do blue/green.
