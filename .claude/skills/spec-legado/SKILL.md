---
name: spec-legado
description: Extrai do código legado uma spec do comportamento atual de uma capacidade, com regras identificadas, evidências em arquivo e linha, riscos de segurança e dúvidas para decisão humana. Use ao documentar um domínio existente em docs/specs ou antes de alterar um comportamento que ainda não tem spec.
---

# Extrair spec do legado

Produza `docs/specs/<dominio>/<capacidade>.md` descrevendo o que o sistema faz hoje. O código prova
o comportamento, não a intenção: nunca apresente um comportamento observado como regra de negócio
aprovada.

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
   `_templates/v2018/` e os dois frontends.
3. Procure quem lê o estado e toma decisões com ele: permissões, filtros, relatórios e cálculos.
4. Aplique a varredura de segurança abaixo aos pontos encontrados nos passos 2 e 3.
5. Leia cada trecho com a indentação original antes de concluir. `return`, `else` e blocos aninhados
   mudam a regra.
6. Quando a leitura for ambígua, confirme com uma verificação sem escrita, como inspecionar o SQL de
   um queryset ou os campos de um serializer.
7. Procure testes existentes e registre se a regra está coberta.
8. Escreva a spec e confira se todo `arquivo:linha` citado continua correto.

## Varredura de segurança

Escopo: o código que a capacidade toca e a infraestrutura que esse código alcança (arquivos,
volumes, comandos, cache, filas, índices). Não é auditoria do sistema inteiro. Achado fora do
recorte entra com uma evidência e a marca `fora do recorte`, sem aprofundar.

Para cada ponto de entrada (view, action, endpoint da API, consumer, task), responda:

1. **Acesso**: o que anônimo, autenticado sem vínculo, usuário de outro autor e operador conseguem
   ler ou gravar? Confira `public = [RP_LIST, RP_DETAIL]`, `permission_classes`, `@action` sem
   permissão própria, GET que altera estado e queryset sem filtro por dono (IDOR).
2. **Dados pela API**: o `drfautoapi` serializa todos os campos. Há CPF, e-mail, telefone,
   endereço, `owner`, tokens ou campos internos expostos? Algum filtro permite enumerar dados
   pessoais?
3. **Arquivos e volumes**: caminho montado com entrada do usuário, arquivo de mídia servido sem
   checagem, PDF ou relatório que embute arquivo local do servidor, upload sem validar tipo,
   temporário com nome previsível.
4. **Execução no servidor**: `subprocess`, `shell=True`, `os.system`, `eval`, template renderizado
   a partir de texto do usuário, SQL cru com interpolação, `extra()`, `RawSQL`.
5. **Saídas indiretas**: Solr, embeddings ou chat RAG com conteúdo não público, cache com chave que
   não inclui o usuário, consumer WebSocket sem checar `scope["user"]`, signal de rede social
   publicando conteúdo restrito, logs com dados pessoais.
6. **Configuração alcançada**: `config(...)` com default inseguro, `csrf_exempt`, CORS, task Celery
   que recebe caminho ou id e não revalida permissão, volume do compose em que a capacidade grava.
7. **Custo sem limite**: requisição anônima que dispara PDF, IA, OCR ou task cara.

Severidade:

- **Crítica**: anônimo lê ou grava dado pessoal, lê arquivo do servidor ou executa código.
- **Alta**: autenticado ultrapassa seu escopo, ou anônimo provoca custo ou indisponibilidade.
- **Média**: vazamento de metadado, ou proteção que depende só de configuração.
- **Baixa**: falta de defesa em profundidade.

Crítica e Alta têm entrada completa. Média e Baixa cabem em uma linha.

### Publicação

O repositório é público. Uma spec com risco Crítico ou Alto em aberto é, ela mesma, uma exposição:

- Escreva-a num branch local `<dominio>-<capacidade>`, faça commits só nele e nunca faça push nem
  merge. Avise o usuário de que a spec só pode ir para o `master` junto com a correção.
- Não transcreva valores de segredo, tokens, dados pessoais reais nem payload pronto. Descreva o
  vetor em uma frase.
- Ao confirmar um risco Crítico, avise o usuário imediatamente, sem esperar o fim da spec.
- O registro do risco não chega ao `master`, nem depois de sanado. Antes do squash do branch, apague
  a entrada `-SEG-` e a dúvida ligada a ela, e descreva o comportamento corrigido como regra comum
  `[implementado]`, sem citar a falha anterior. A mensagem do squash também descreve a regra nova,
  não a falha.
- O teste que cobre a correção também vai para o `master`. Dê a ele nome, docstring, comentários e
  mensagens de assert neutros, que descrevam o comportamento esperado e não o ataque. Por exemplo,
  `test_pdf_usa_apenas_arquivos_de_midia_permitidos`, e não
  `test_anonimo_nao_embute_arquivo_do_servidor`. Isso vale para quem escrever o teste da correção:
  esta skill não altera testes.

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
## Riscos de segurança
- PREFIXO-SEG-001 [Crítica] [observado] Quem alcança o quê, por qual caminho. Evidência:
  `arquivo:linha`. Impacto: o que vaza ou quebra. Mitigação existente: qual, ou nenhuma.
  Como foi obtido: leitura ou verificação local. Decisão: D<n>.
## Dúvidas
- D1. Fato observado, risco concreto e pergunta a decidir.
## Fora do escopo
```

Sem achados, escreva em `Riscos de segurança` "Nenhum risco encontrado nos itens 1 a 7", com a data.

## Regras de escrita

- IDs são estáveis: nunca reutilize nem renumere. Use o prefixo do domínio, como `LOA-FASE-001`;
  riscos usam o mesmo prefixo com `-SEG-`, como `LOA-FASE-SEG-001`.
- Cada regra e cada risco descrevem um comportamento verificável e têm ao menos uma evidência.
- Marcadores: `[observado]` veio do código, `[acordado]` foi confirmado por uma pessoa,
  `[desejado]` ainda não existe, `[implementado]` foi acordado e tem teste.
- Riscos usam `[observado]` (por leitura) e `[confirmado]` (verificação local sem escrita). Não há
  marcador de corrigido: risco sanado sai da spec, conforme `Publicação`. IDs `-SEG-` apagados não
  são reutilizados no mesmo branch.
- Todo risco Crítico ou Alto aponta para uma dúvida `D<n>` que pede a decisão de correção.
- Só mude uma regra para `[acordado]` com confirmação explícita do responsável.
- Diga como cada conclusão foi obtida quando não houve execução, por exemplo "por leitura do código".
- Ao terminar, informe primeiro os riscos Críticos e Altos, depois as dúvidas que exigem decisão,
  das de maior risco para as de menor.
