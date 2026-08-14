# Command `ocrmypdf`

Localização: [`cmj/core/management/commands/ocrmypdf.py`](../cmj/core/management/commands/ocrmypdf.py)

Management command Django que varre um conjunto de modelos do sistema em
busca de arquivos PDF (e alguns JPEG) que ainda não passaram por
reconhecimento óptico de caracteres (OCR) e conversão para PDF/A, executa o
binário externo `ocrmypdf` sobre eles e registra o resultado. Também faz
limpeza periódica de metadados antigos e de arquivos temporários, e dispara
reindexação no Solr para os anos afetados.

Pensado para ser agendado via cron do host (não versionado neste repositório)
e rodar repetidamente ao longo do dia e da noite, processando um pouco de
cada vez a cada execução.

## Classes e entidades envolvidas (apenas citação)

- `Command` — a própria classe do command.
- [`OcrMyPDF`](../cmj/core/models.py) — modelo que registra cada tentativa de
  OCR (via `GenericForeignKey` para o objeto alvo + campo de arquivo), com
  `created`, `concluido` (auto atualizado a cada save) e `sucesso`.
- [`ProcessoExterno`](../cmj/utils.py) — utilitário que roda um comando
  externo em thread separada com timeout, usado para invocar o `ocrmypdf`.
- Modelos alvo, cada um com seu(s) campo(s) de arquivo:
  - `DocumentoAdministrativo` (`texto_integral`)
  - `MateriaLegislativa` (`texto_original`)
  - `NormaJuridica` (`texto_integral`)
  - `DocumentoAcessorioAdministrativo` (`arquivo`)
  - `DocumentoAcessorio` (`arquivo`)
  - `SessaoPlenaria` (`upload_pauta`, `upload_ata`, `upload_anexo`)
  - `DiarioOficial` (`arquivo`)
- `SessaoPlenaria` também é usada como **gatilho de interrupção**
  (`tem_sessaoplenaria_aberta`).

## Guardas de execução

Podem interromper o command inteiro antes ou durante o processamento:

1. **Sessão plenária aberta** (`tem_sessaoplenaria_aberta`): se há uma sessão
   iniciada e não finalizada hoje, o command aborta imediatamente (evita
   competir por I/O/CPU durante sessão ao vivo). Verificado antes de começar
   e a cada item processado.
2. **Já em execução**: lock exclusivo via `fcntl.flock` em
   `/tmp/cmj_ocrmypdf.lock`; se outra instância já detém o lock, a execução
   atual aborta. O lock é liberado automaticamente pelo SO mesmo se o
   processo morrer.
3. `post_save.disconnect(...)` — desliga signals de refresh antes de
   processar em massa, evitando efeitos colaterais de save.

## Caminho comum a toda execução

1. Limpeza de arquivos/pastas temporários em `/tmp` com mais de 1 dia,
   pertencentes a usuários e prefixos conhecidos.
2. Determina se a execução é noturna (janela `[22h, 6h)`).
3. Percorre os modelos configurados, decide quais itens processar, executa
   OCR item a item, e ao final remove da lista os modelos que não tiveram
   nenhum item processado na rodada — repetindo até esvaziar a lista ou até
   estourar o corte de tempo de execução.
4. Ao final, para cada `(ano, modelo)` afetado, dispara `update_index`
   (Haystack/Solr) restrito ao ano e ao modelo.

## Caminho exclusivo da execução noturna (`hour < 6` ou `>= 22`)

- Faz manutenção do histórico: apaga registros `OcrMyPDF` com mais de 360
  dias, e registros com mais de 90 dias que falharam — permitindo
  reprocessamento.
- Ignora o limite `count_base` por modelo (processa quantos itens couberem
  no tempo disponível, não só os primeiros N).
- Aceita páginas maiores: até `max_paginas_noturno = 100`.
- Aceita arquivos maiores quando não há contagem de páginas: até
  `max_size_noturno = 40MB` (limite deliberadamente alinhado a um comentário
  em [`cmj/search/search_indexes.py`](../cmj/search/search_indexes.py)).
- Roda o `ocrmypdf` com mais paralelismo (`-j 12`).

## Caminho exclusivo da execução diurna (`6h`–`22h`)

- Não faz limpeza de `OcrMyPDF` antigos.
- Respeita `count_base` por modelo (número pequeno de itens por modelo antes
  de parar naquele modelo na rodada).
- Descarta itens sem contagem de páginas resolvível.
- Descarta itens com páginas acima de `max_paginas_diurno = 50` e arquivos
  acima de `max_size_diurno = 10MB`.
- Roda o `ocrmypdf` com menos paralelismo (`-j 4`).

## Seleção de item a processar (por campo de arquivo)

Para cada item do modelo e cada campo de arquivo:

- Pula se o documento já está assinado/homologado (não mexe em arquivo já
  assinado digitalmente).
- Pula se o arquivo não é `.pdf`.
- Busca um registro `OcrMyPDF` existente para aquele `content_type/object_id/field`:
  - Se existir e o arquivo em disco for mais novo que o último OCR feito,
    apaga o registro antigo para forçar reprocessamento.
  - Se existir mas o arquivo não existir mais, apaga o registro e pula.
  - Se não existir registro e o arquivo existir, processa: cria um
    `OcrMyPDF(sucesso=False)`, executa o OCR e atualiza `sucesso` com o
    resultado.
- Corte de tempo: se decorridos mais de 2 minutos desde o início do command,
  interrompe a varredura (mas ainda executa a reindexação dos anos já
  processados). Se uma sessão plenária abrir durante o processamento, aborta
  imediatamente **sem** reindexar.

## Execução real do OCR

- Resolve o caminho do arquivo "original" (backup não sinalizado) como
  entrada, e o caminho atual do campo como saída (in-place).
- Roda `ocrmypdf --redo-ocr -l por -q -j N --output-type pdfa-2 <entrada> <saída>`
  (N = 12 à noite, 4 de dia). `--force-ocr` é evitado propositalmente por
  invalidar assinaturas digitais.
- Códigos de retorno `0, 2, 6` são tratados como sucesso; timeout (`None`)
  é tratado como falha.

## Refatoração aplicada (2026-08-14)

O command foi revisado com foco em segurança e manutenibilidade, sem alterar
nenhuma regra de negócio (limites diurno/noturno, seleção de itens, resultado
do OCR):

- **Shell injection (OWASP A03)**: `ProcessoExterno` (em `cmj/utils.py`) e o
  `console()` de `cmj/arq/tasks.py` executavam comandos com
  `subprocess.Popen(cmd, shell=True, ...)` a partir de uma string montada com
  caminhos de arquivo não escapados — um nome de arquivo malicioso poderia
  injetar comandos. Corrigido para `shell=False` com argumentos tokenizados
  (`shlex.split`/lista). O mesmo padrão foi corrigido em `adjusts.py` e
  `ci2tcm.py`.
- **Extração de responsabilidades**: o `handle()` monolítico (5 níveis de
  laços aninhados) foi quebrado em métodos privados (`_executar`,
  `_run_manutencao_noturna`, `_processar_model`, `_processar_campo`,
  `_reindexar_anos`). As flags de controle (`break_while`/`return` direto)
  viraram exceções nomeadas `_TempoLimiteAtingido` e
  `_SessaoAbertaInterrompeu`, preservando a semântica original.
- **Constantes nomeadas**: números mágicos (janela noturna, paralelismo,
  timeouts, retenção de histórico, regras de limpeza de `/tmp`) viraram
  constantes de classe.
- **Lock mais robusto**: `is_running()` (parsing de `ps -eo pid,args`) foi
  substituído por lock exclusivo via `fcntl.flock`.
- **Código morto removido**: classe `CompressPDF` (Ghostscript, não usada) e
  método `run_distibui_ocr_ao_longo_do_ano` (utilitário pontual, chamada já
  comentada) foram removidos.
- **Tratamento de exceções**: `except: print(e)` substituído por
  `self.logger.exception(...)` para manter rastreabilidade em log.
