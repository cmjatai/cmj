---
name: spec-legado
description: Extrai do código legado uma spec do comportamento atual de uma capacidade, com regras identificadas, evidências em arquivo e linha e dúvidas para decisão humana. Use ao documentar um domínio existente em docs/specs ou antes de alterar um comportamento que ainda não tem spec.
---

# Extrair spec do legado

Produza `docs/specs/<dominio>/<capacidade>.md` descrevendo o que o sistema faz hoje. O código prova
o comportamento, não a intenção: nunca apresente um comportamento observado como regra de negócio
aprovada.

## Limites

- Não altere código, testes, migrations ou dados.
- Documente uma capacidade por vez. Se o pedido for amplo, proponha o recorte antes de ler tudo.
- Não leia `.env` nem credenciais, e não consulte dados de produção.
- Não proponha refatoração na spec. Riscos e incoerências vão para `Dúvidas`.

## Processo

1. Localize a definição central da capacidade: models, constantes e choices.
2. Procure **todos os pontos de escrita**, não só os óbvios: views, forms, API, signals, tasks,
   commands, outros apps e frontend. Neste projeto, confira também `sapl/`, `cmj/api/`,
   `_templates/v2018/` e os dois frontends.
3. Procure quem lê o estado e toma decisões com ele: permissões, filtros, relatórios e cálculos.
4. Leia cada trecho com a indentação original antes de concluir. `return`, `else` e blocos aninhados
   mudam a regra.
5. Quando a leitura for ambígua, confirme com uma verificação sem escrita, como inspecionar o SQL de
   um queryset ou os campos de um serializer.
6. Procure testes existentes e registre se a regra está coberta.
7. Escreva a spec e confira se todo `arquivo:linha` citado continua correto.

## Formato

```markdown
# <Domínio>: <capacidade>

Status: observado
Última verificação: AAAA-MM-DD (commit `<hash>`)
Código principal: `<caminhos>`
Testes: `<caminhos>` ou nenhum

## Escopo
## Regras
- PREFIXO-001 [observado] Regra em uma frase. Evidência: `arquivo:linha`.
## Dúvidas
- D1. Fato observado, risco concreto e pergunta a decidir.
## Fora do escopo
```

## Regras de escrita

- IDs são estáveis: nunca reutilize nem renumere. Use o prefixo do domínio, como `LOA-FASE-001`.
- Cada regra descreve um comportamento verificável e tem ao menos uma evidência.
- Marcadores: `[observado]` veio do código, `[acordado]` foi confirmado por uma pessoa,
  `[desejado]` ainda não existe, `[implementado]` foi acordado e tem teste.
- Só mude uma regra para `[acordado]` com confirmação explícita do responsável.
- Diga como cada conclusão foi obtida quando não houve execução, por exemplo "por leitura do código".
- Ao terminar, informe as dúvidas que exigem decisão, começando pelas de maior risco.
