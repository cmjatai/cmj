# Specs do PortalCMJ

Cada arquivo descreve uma capacidade: `docs/specs/<dominio>/<capacidade>.md`. Specs de comportamento
existente nascem com a skill `spec-legado`; specs de funcionalidade nova, com a skill `spec-nova`.
Este arquivo reúne as convenções comuns às duas, inclusive a varredura de segurança.

## Cabeçalho

```markdown
# <Domínio>: <capacidade>

Status: observado | desejado | acordado | implementado (ou combinação, explicada em uma linha)
Última verificação: AAAA-MM-DD (commit `<hash>`)
Código principal: `<caminhos>`
Testes: `<caminhos>` ou nenhum
```

## Marcadores

Regras:

- `[observado]`: veio da leitura do código. Não é regra de negócio aprovada.
- `[desejado]`: ainda não existe no código.
- `[acordado]`: confirmado explicitamente pelo responsável. Só mude para `[acordado]` com essa
  confirmação.
- `[implementado]`: foi acordado e tem teste.
- `[retirada]`: não vale mais. A entrada fica na spec, com uma frase: `Substituída por <ID>.` ou
  `Removida: <motivo>.` Não exige evidência, e nenhum teste ou código aponta para ela.

Uma regra `[observado]` pode ter teste de caracterização. Uma regra `[acordado]` com teste passa a
`[implementado]`.

Riscos de segurança (`-SEG-`):

- `[observado]`: por leitura do código.
- `[confirmado]`: por verificação local sem escrita.
- Não há marcador de corrigido: risco sanado sai da spec, conforme `Publicação`.

## IDs

- Prefixo do domínio e da capacidade, como `LOA-FASE-001`. Riscos usam o mesmo prefixo com `-SEG-`,
  como `PREFIXO-SEG-001`. Cada spec usa um prefixo só, e cada prefixo pertence a uma spec.
- `PREFIXO` é reservado para exemplos neste arquivo e nas skills.
- IDs são estáveis: nunca reutilize nem renumere. Regra que deixa de valer recebe `[retirada]`;
  não a apague. IDs `-SEG-` apagados não são reutilizados no
  mesmo branch.
- Cada regra e cada risco descrevem um comportamento verificável e têm ao menos uma evidência
  `arquivo:linha`.
- Todo risco Crítico ou Alto aponta para uma dúvida `D<n>` que pede a decisão de correção.
- Diga como cada conclusão foi obtida quando não houve execução, por exemplo "por leitura do código".

## Ligação com os testes

Cada teste aponta a regra que cobre com `@pytest.mark.spec("<ID>")` (marcador registrado em
`pyproject.toml`). Para um arquivo inteiro: `pytestmark = [pytest.mark.spec("<ID>")]`.

## Checagem

`python manage.py specs_check` cruza as specs com os testes e com as referências a IDs no
repositório. Use `--spec docs/specs/<dominio>/<capacidade>.md` para ver só os achados de uma spec. O
comando termina com código 1 se houver achado, e uma spec só está pronta sem achados. O CI
(`.github/workflows/ci.yml`) roda a mesma checagem em cada push e PR para o `master`, com
`python cmj/core/services/s_specs_check.py`, sem Django nem dependências.

| Código | Achado |
| --- | --- |
| SPEC-DUP | ID definido mais de uma vez |
| SPEC-FMT | ID fora do formato `PREFIXO-NNN`, ou marcador ausente ou inválido |
| SPEC-PREFIXO | Spec com mais de um prefixo, ou prefixo usado em duas specs |
| SPEC-CAB | Falta uma linha do cabeçalho, ou um caminho de `Código principal:` ou `Testes:` não existe |
| SPEC-EVID | Regra sem `` `arquivo:linha` `` (exceto `[retirada]` e `[desejado]` com "a criar"), ou evidência em arquivo inexistente ou além do fim dele |
| SPEC-SEG | Risco `-SEG-` no `master`, ou risco Crítico ou Alto sem dúvida `D<n>` existente |
| TEST-ORFAO | Teste ligado a ID que não existe |
| TEST-ARG | `pytest.mark.spec` com argumento que não é string literal |
| TEST-FALTA | Regra `[implementado]` sem teste ligado |
| TEST-STATUS | Teste ligado a regra `[acordado]`, `[desejado]`, `[retirada]` ou a risco `-SEG-` |
| TEST-CAB | Arquivo de teste que liga IDs da spec, mas não está em `Testes:` (arquivo ou diretório) |
| REF-ORFA | Referência a ID inexistente em código, comentário, docstring ou documento |
| REF-RETIRADO | Referência a regra `[retirada]` fora de `docs/specs` |

Como a checagem lê:

- Uma regra é a linha `- ID [marcador]` ou `| ID [marcador] |`, mais as linhas indentadas que a
  seguem. Linhas dentro de blocos de código não contam.
- Nos testes Python vale `pytest.mark.spec("ID", ...)`, lido pela árvore sintática. Nos testes do
  v8 e do v2018 (`_frontend/v8/**/*.spec.js` e `_frontend/v2018/**/*.spec.js`) vale o título que
  começa por `'ID: '` ou `'ID, ID: '`.
- Nas referências, as abreviações `LOA-FASE-056, 057 e 064` e `LOA-EMD-070 a 073` contam com o
  prefixo do ID completo. Num intervalo, só as pontas são checadas. IDs de domínios que não têm spec
  são ignorados.

A checagem não diz se a linha citada como evidência ainda mostra o que a regra afirma, nem se o
teste cobre de fato a regra. Isso continua sendo revisão humana.

## Varredura de segurança

Escopo: o código que a capacidade toca e a infraestrutura que esse código alcança (arquivos,
volumes, comandos, cache, filas, índices). Não é auditoria do sistema inteiro. Achado fora do
recorte entra com uma evidência e a marca `fora do recorte`, sem aprofundar.

Para cada ponto de entrada (view, action, endpoint da API, consumer, task, command), responda:

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

Confirme falhas só no ambiente local e sem escrita. Nunca contra produção.

### Severidade

- **Crítica**: anônimo lê ou grava dado pessoal, lê arquivo do servidor ou executa código.
- **Alta**: autenticado ultrapassa seu escopo, ou anônimo provoca custo ou indisponibilidade.
- **Média**: vazamento de metadado, ou proteção que depende só de configuração.
- **Baixa**: falta de defesa em profundidade.

Crítica e Alta têm entrada completa. Média e Baixa cabem em uma linha:

```markdown
- PREFIXO-SEG-001 [Crítica] [observado] Quem alcança o quê, por qual caminho. Evidência:
  `arquivo:linha`. Impacto: o que vaza ou quebra. Mitigação existente: qual, ou nenhuma.
  Como foi obtido: leitura ou verificação local. Decisão: D<n>.
```

Sem achados, escreva em `Riscos de segurança` "Nenhum risco encontrado nos itens 1 a 7", com a data.

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
  `test_anonimo_nao_embute_arquivo_do_servidor`.

Requisitos de segurança de funcionalidade nova, escritos antes do código, não são falha em produção:
são regras comuns, sem `-SEG-`, e vão ao `master` normalmente (veja a skill `spec-nova`).
