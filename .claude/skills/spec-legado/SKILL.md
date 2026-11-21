---
name: spec-legado
description: Extrai do código legado uma spec do comportamento atual de uma capacidade, com regras identificadas, evidências em arquivo e linha, riscos de segurança e dúvidas para decisão humana. Use ao documentar um domínio existente em docs/specs ou antes de alterar um comportamento que ainda não tem spec. Para funcionalidade que ainda não existe, use spec-nova.
---

# Extrair spec do legado

Produza `docs/specs/<dominio>/<capacidade>.md` descrevendo o que o sistema faz hoje. O código prova
o comportamento, não a intenção: nunca apresente um comportamento observado como regra de negócio
aprovada.

Antes de começar, leia `docs/specs/README.md`: cabeçalho, marcadores, IDs, varredura de segurança,
severidade e regras de publicação valem aqui sem exceção.

## Limites

- Não altere código, testes, migrations ou dados.
- Documente uma capacidade por vez. Se o pedido for amplo, proponha o recorte antes de ler tudo.
- Não leia `.env` nem credenciais, e não consulte dados de produção.
- Não proponha refatoração na spec. Riscos e incoerências vão para `Dúvidas`, e os de segurança
  também para `Riscos de segurança`.
- Confirme falhas de segurança só no ambiente local e sem escrita. Nunca contra produção.

## Processo

1. Localize a definição central da capacidade: models, constantes e choices.
2. Procure **todos os pontos de escrita**, não só os óbvios: views, forms, API, signals, tasks,
   commands, outros apps e frontend. Neste projeto, confira também `sapl/`, `cmj/api/`,
   `_templates/v2018/` e os três frontends (`_frontend/v6`, `v8` e `v2018`).
3. Procure quem lê o estado e toma decisões com ele: permissões, filtros, relatórios e cálculos.
4. Aplique a varredura de segurança de `docs/specs/README.md` aos pontos encontrados nos passos 2
   e 3.
5. Leia cada trecho com a indentação original antes de concluir. `return`, `else` e blocos aninhados
   mudam a regra.
6. Quando a leitura for ambígua, confirme com uma verificação sem escrita, como inspecionar o SQL de
   um queryset ou os campos de um serializer.
7. Procure testes existentes e registre se a regra está coberta.
8. Escreva a spec e confira se todo `arquivo:linha` citado continua correto.
9. Rode `python manage.py specs_check --spec <arquivo da spec>` e resolva todos os achados. A spec
   só está pronta sem achados. No branch de uma spec com risco `-SEG-`, o achado `SPEC-SEG` de
   "risco no master" não aparece. Se aparecer, você está no `master`, e a spec não pode ficar lá.

Spec com risco Crítico ou Alto em aberto segue a seção `Publicação` de `docs/specs/README.md`
(branch local, sem push, aviso imediato de Crítico). Isso vale também para quem escrever o teste da
correção: esta skill não altera testes.

## Formato

Cabeçalho conforme `docs/specs/README.md`, com `Status: observado`.

```markdown
## Escopo
## Regras
- PREFIXO-001 [observado] Regra em uma frase. Evidência: `arquivo:linha`.
## Riscos de segurança
- PREFIXO-SEG-001 [Crítica] [observado] ... (formato completo em docs/specs/README.md)
## Dúvidas
- D1. Fato observado, risco concreto e pergunta a decidir.
## Fora do escopo
```

## Ao terminar

Informe primeiro os riscos Críticos e Altos, depois as dúvidas que exigem decisão, das de maior
risco para as de menor.
