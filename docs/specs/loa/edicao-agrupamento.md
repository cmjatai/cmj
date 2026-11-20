# LOA: edição do agrupamento

Status: observado
Última verificação: 2026-11-19 (commit `439b517f8`)
Código principal: `cmj/loa/views/v_agrupamento.py`, `cmj/loa/forms/f_agrupamento.py`,
`cmj/loa/models/m_agrupamento.py`, `cmj/loa/signals.py`, `cmj/api/loa/views/agrupamento.py`,
`cmj/api/loa/views/agrupamentoemendaloa.py`, `cmj/api/loa/views/agrupamentoregistrocontabil.py`,
`_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js`
Testes: nenhum específico. As regras de fase citadas têm testes em `cmj/loa/tests/test_fases_emenda.py`.

Todas as regras foram obtidas por leitura do código, sem executar os fluxos.

## Escopo

A criação e a tela de edição de `Agrupamento` (`/loa/agrupamento/<pk>/edit`) e o que acontece por
trás delas:
- a view e o formulário;
- os endpoints chamados pela tela;
- a sincronização dos registros contábeis entre o agrupamento e suas emendas;
- o comportamento observável do frontend v2018, com o autosave em detalhe.

Outras specs são donas de parte do fluxo, e esta só cita os IDs:
- `docs/specs/loa/fases-emenda.md`: fases, inclusão em agrupamento (LOA-FASE-058 a 060), coletiva
  (LOA-FASE-056, 057, 064 e 017 a 019) e liberação ao salvar (LOA-FASE-016).
- `docs/specs/genia/ementa-emenda-coletiva.md`: a geração da finalidade por I.A. (`GENIA-LOA`).

O agrupamento reúne emendas que recebem os mesmos registros contábeis, definidos em percentual do valor
de cada emenda. Dele podem sair emendas coletivas, uma por conjunto de unidade e entidade.

## Regras

### Acesso

- LOA-AGR-001 [observado] Criar, editar e excluir agrupamento pela interface exige
  `emendaloa_full_editor`, que o editor contábil, o Operador da LOA e o superusuário têm. Listagem e
  detalhe são públicos. Evidência: `cmj/loa/views/v_agrupamento.py:12-56`,
  `cmj/loa/views/v_agrupamento.py:131-132`, `cmj/globalrules/map_rules.py:270-284`.
- LOA-AGR-002 [observado] Na API de `agrupamento`, `agrupamentoemendaloa` e
  `agrupamentoregistrocontabil`, todo POST, PATCH e DELETE exige `emendaloa_full_editor`, inclusive
  as actions. Os GET exigem só as permissões públicas de listagem e detalhe. Evidência:
  `cmj/api/loa/views/agrupamento.py:13-22`, `cmj/api/loa/views/agrupamentoemendaloa.py:15-24`,
  `cmj/api/loa/views/agrupamentoregistrocontabil.py:291-300`, `sapl/api/permissions.py:12-24`,
  `sapl/api/permissions.py:50-56`.

### Criação e cópia

- LOA-AGR-010 [observado] Abrir a tela de criação (GET) já cria o agrupamento, sem formulário, e
  redireciona para a edição. O nome é "Novo Agrupamento". Se já existe um agrupamento da LOA com esse
  prefixo, o nome recebe o número final do último deles (por `id`) mais 1. Evidência:
  `cmj/loa/views/v_agrupamento.py:55-80`.
- LOA-AGR-011 [observado] O botão de cópia (`POST /api/loa/agrupamento/<pk>/create_copia/`) cria um
  agrupamento com o nome "<nome> (Cópia N)" e a mesma LOA. A cópia leva os registros contábeis
  (despesa, percentual e operação), mas não leva as emendas nem a finalidade. Depois, a tela abre a
  edição da cópia. Evidência: `cmj/loa/models/m_agrupamento.py:90-110`,
  `cmj/api/loa/views/agrupamento.py:41-54`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:29-35`.

### Layout da tela

- LOA-AGR-020 [observado] A tela tem três áreas:
  - **Dados gerais:** nome, área de aplicação (`tipo`, em botões de rádio: não selecionado, Saúde ou
    Áreas Diversas) e finalidade, com os botões de cópia, pré-visualização, cancelar coletivas, gerar
    coletivas, fechar e "Liberar para Protocolo".
  - **Registros contábeis:** "Registrar Deduções e Inserções", com busca de despesa e percentual, e
    "Registros das Despesas Orçamentárias".
  - **Emendas:** "Busca por Emendas" e "Emendas Selecionadas".

  O layout é o mesmo para todos os perfis que acessam a tela. Evidência:
  `cmj/loa/forms/f_agrupamento.py:94-253`.
- LOA-AGR-021 [observado] O percentual da despesa começa em 100,00. Depois de incluir um registro, a
  tela volta o campo para 100,00. Evidência: `cmj/loa/forms/f_agrupamento.py:256`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:179`.

### Registros contábeis do agrupamento

- LOA-AGR-030 [observado] Incluir um registro envia
  `POST /api/loa/agrupamentoregistrocontabil/create_for_agrupamento_update/` com a despesa escolhida
  na busca ou com os dados digitados, e o percentual.
  - O percentual não pode ser zero. Pela mensagem do serializer, valores negativos são deduções
    (Art. 1º) e positivos são inserções (Art. 2º).
  - Sem despesa escolhida, o servidor exige que órgão, unidade, função, subfunção e fonte existam nos
    anexos da LOA, e cria a despesa e, se preciso, programa, ação e natureza.
  - Com `loa.forcar_detalhamento_de_fonte`, uma despesa com fonte terminada em `.000` é trocada por
    outra com a fonte detalhada.
  - Uma mesma despesa não entra duas vezes no agrupamento.

  Evidência: `cmj/api/loa/views/agrupamentoregistrocontabil.py:108-288`,
  `cmj/api/loa/views/agrupamentoregistrocontabil.py:302-334`,
  `cmj/loa/models/m_agrupamento.py:447-452`.
- LOA-AGR-031 [observado] Gravar um registro contábil do agrupamento dispara `Agrupamento.sync()`
  (LOA-AGR-033). Excluir um registro apaga, nas emendas do agrupamento, os registros com a mesma
  despesa. Evidência: `cmj/loa/signals.py:41-70`.
- LOA-AGR-032 [observado] A busca e a exclusão de registros funcionam como na edição da emenda
  (LOA-EMD-060 e LOA-EMD-062), com duas diferenças:
  - destaca qualquer termo da busca, sem o mínimo de 3 letras;
  - não avisa quando há mais de 10 resultados.

  O rodapé de totais não é preenchido. Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:84-261`.
- LOA-AGR-033 [observado] `Agrupamento.sync()` refaz os registros contábeis de cada emenda do
  agrupamento, exceto as da fase -10, que o manager padrão oculta:
  - apaga os registros da emenda;
  - cria um registro por registro do agrupamento, no valor de valor da emenda × percentual ÷ 100;
  - quando os percentuais somam zero, joga a diferença de arredondamento na última dedução e na
    última inserção, para que cada lado feche com o valor da emenda.

  Evidência: `cmj/loa/models/m_agrupamento.py:112-147`.

### Emendas do agrupamento

- LOA-AGR-040 [observado] "Emendas Selecionadas" lista todas as emendas do agrupamento, inclusive as da
  fase -10 (`GET /api/loa/agrupamento/<pk>/emendas/`). Cada item mostra:
  - tipo e se a emenda permite junção em coletiva;
  - valor, indicação e finalidade, com link para a edição da emenda;
  - parlamentares;
  - fase: vermelha na 10, amarela na 12 e verde nas demais.

  Evidência: `cmj/api/loa/views/agrupamento.py:24-39`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:271-313`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:400-431`.
- LOA-AGR-041 [observado] A busca de emendas exige ao menos 3 letras e consulta
  `/api/loa/emendaloa/search/`.
  - O resultado traz emendas do ano da LOA com fase menor que 17, filtradas pelo tipo do agrupamento
    quando ele não é "Não selecionado".
  - Ficam de fora as que já estão na lista de selecionadas. As que estão em outro agrupamento aparecem.
  - Emendas na fase 10 aparecem sem o botão de incluir.

  Evidência: `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:315-391`,
  `cmj/api/loa/views/emendaloa.py:371-401`.
- LOA-AGR-042 [observado] Incluir uma emenda envia `POST /api/loa/agrupamentoemendaloa/`. Fases aceitas,
  ano e fase resultante seguem LOA-FASE-058 a LOA-FASE-060.
  - Uma emenda só pertence a um agrupamento; a tentativa de incluí-la em outro dá erro.
  - Gravar o vínculo dispara `Agrupamento.sync()`, que **substitui** os registros contábeis da emenda
    pelos do agrupamento.
  - Por fim, a finalidade é gerada por I.A. (LOA-AGR-050).

  Evidência: `cmj/api/loa/views/agrupamentoemendaloa.py:84-134`, `cmj/loa/signals.py:50-56`,
  `cmj/loa/models/m_agrupamento.py:369-374`.
- LOA-AGR-043 [observado] Remover uma emenda envia `POST /api/loa/agrupamentoemendaloa/delete/`. A
  emenda da fase -10 não pode ser removida (LOA-FASE-042). Antes de desfazer o vínculo, o servidor
  sincroniza o agrupamento e a emenda, e ignora erros nesses passos (só os registra no log). Ao
  desfazer o vínculo, um signal apaga **todos** os registros contábeis da emenda. Ela sai do
  agrupamento sem registros e na mesma fase. Depois, a finalidade é gerada de novo por I.A. Evidência:
  `cmj/api/loa/views/agrupamentoemendaloa.py:26-70`, `cmj/loa/signals.py:72-78`.
- LOA-AGR-044 [observado] Os erros de inclusão e de remoção aparecem em um alerta na própria lista.
  Evidência: `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:306-309`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:383-387`.

### Finalidade

- LOA-AGR-050 [observado] Depois de cada inclusão ou remoção de emenda, o servidor tenta gerar a
  finalidade por I.A.:
  - **Unidade e entidade iguais em todas as emendas:** grava a finalidade gerada.
  - **Unidades ou entidades diferentes:** apaga a finalidade, sem aviso na tela.
  - **Falha da I.A.:** apaga a finalidade e devolve o aviso, que a tela mostra em `alert`.

  Em todos os casos, a finalidade digitada antes é substituída (ver D3). Evidência:
  `cmj/loa/models/m_agrupamento.py:149-177`, `cmj/api/loa/views/agrupamentoemendaloa.py:72-82`,
  GENIA-LOA-004, GENIA-LOA-006.
- LOA-AGR-051 [observado] Ctrl+clique na finalidade pede a geração por I.A.
  (`PATCH /api/loa/agrupamento/<pk>/generate_finalidade_global/`). Enquanto espera, o campo fica
  somente leitura com "Atualizando com I.A...". Se a geração falha, o campo mostra o erro e volta a
  ser editável depois de 5 segundos. Evidência: `cmj/api/loa/views/agrupamento.py:56-73`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:451-470`.
- LOA-AGR-052 [observado] Ao abrir a tela e depois de cada inclusão ou remoção, o campo de finalidade
  mostra "Atualizando..." até receber o valor do servidor. Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:275-279`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:374`.

### Autosave

- LOA-AGR-060 [observado] O autosave reage ao evento `change` de qualquer campo com `name`. Cada
  mudança envia `PATCH /api/loa/agrupamento/<pk>/` com `{campo: valor}`. É assim que nome, tipo e
  finalidade são gravados. Se dá certo, a tela recarrega os registros contábeis. Se falha, não
  mostra nada (ver D4). Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:472-492`.
- LOA-AGR-061 [observado] Campos que não são do model também geram PATCH: as buscas, os campos
  `despesa_*` e `perc_despesa`. O serializer os ignora, e o `save()` de `Agrupamento` não dispara
  `sync()`. Evidência: `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:475-485`,
  `cmj/loa/signals.py:41-56`.
- LOA-AGR-062 [observado] Enter não envia o formulário. No campo de busca de despesa, Enter seleciona o
  resultado quando há só um. Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:437-449`.

### Emendas coletivas

- LOA-AGR-070 [observado] O botão de pré-visualização abre
  `GET /api/loa/agrupamento/<pk>/view/?model=1` em nova aba.
  - O PDF tem uma emenda coletiva por conjunto de unidade e entidade, montada pelas regras de
    LOA-FASE-021. A prévia inclui as emendas da fase -10.
  - Sem coletiva possível, o PDF tem uma página "Nenhuma Emenda gerada", com o total de emendas e de
    conjuntos.
  - Se o agrupamento não tem finalidade, a prévia pede a finalidade automática à I.A. (GENIA-LOA-005).

  Evidência: `cmj/api/loa/views/agrupamento.py:120-226`, `cmj/loa/models/m_agrupamento.py:179-271`,
  `cmj/loa/forms/f_agrupamento.py:112-116`.
- LOA-AGR-071 [observado] "Gerar Emendas Coletivas"
  (`POST /api/loa/agrupamento/<pk>/gerar_emenda_coletiva/`) cria uma coletiva por conjunto com mais
  de uma emenda. Cada coletiva recebe:
  - como valor, a soma dos valores por parlamentar;
  - os parlamentares com os valores somados;
  - as inserções e deduções somadas por despesa;
  - a finalidade do agrupamento ou, sem ela, a automática.

  Fases e dono seguem LOA-FASE-017, LOA-FASE-018 e LOA-FASE-064. A tela mostra em `alert` quantas
  coletivas foram criadas, ou que nenhuma foi, e em seguida vai para o detalhe do agrupamento.
  Evidência: `cmj/loa/models/m_agrupamento.py:290-358`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:36-59`.
- LOA-AGR-072 [observado] "Cancelar Emendas Coletivas" pede confirmação e chama
  `POST /api/loa/agrupamento/<pk>/cancelar_emendas_coletivas/`. O servidor faz o efeito de
  LOA-FASE-019, LOA-FASE-056 e LOA-FASE-057 e exclui as coletivas geradas. Depois, a tela recarrega.
  Evidência: `cmj/loa/models/m_agrupamento.py:273-288`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:60-81`.

### Liberar para protocolo

- LOA-AGR-080 [observado] O botão "Liberar para Protocolo" envia o formulário por POST. Antes de
  qualquer outra coisa, o `clean()` exige:
  - ao menos um registro contábil no agrupamento;
  - percentuais que somem zero.

  Evidência: `cmj/loa/forms/f_agrupamento.py:135-137`, `cmj/loa/forms/f_agrupamento.py:258-277`.
- LOA-AGR-081 [observado] Com o formulário válido, as emendas do agrupamento e as coletivas geradas
  passam para a fase 17, conforme LOA-FASE-016. Todas são salvas, mesmo as que já estavam na 17 ou
  acima. O `save()` do formulário não grava os campos do próprio agrupamento, que dependem só do
  autosave. Depois, a tela vai para o detalhe. Evidência: `cmj/loa/forms/f_agrupamento.py:279-305`,
  `cmj/loa/views/v_agrupamento.py:150-154`.

## Dúvidas

Ordenadas por risco.

- D1. **"Liberar para Protocolo" pula a correção do autor.** O formulário leva para 17 toda emenda do
  agrupamento entre as fases 1 e 16 (LOA-AGR-081), inclusive a que o editor devolveu para a fase 10
  pela tela da emenda depois de incluí-la. A emenda devolvida ao autor deve bloquear a liberação, ou
  ficar de fora dela?
- D2. **Liberar sem gerar as coletivas.** A liberação não confere se as emendas que permitem junção já
  viraram coletiva. Elas vão para a 17 individualmente (LOA-AGR-081). Gerar as coletivas antes de
  liberar deve ser obrigatório?
- D3. **A finalidade digitada se perde.** Cada inclusão ou remoção de emenda regrava a finalidade pela
  I.A., ou a apaga quando as unidades diferem (LOA-AGR-050). O texto de ajuda avisa disso, mas a
  finalidade manual some sem confirmação. A edição manual deve ser preservada?
- D5. **A pré-visualização pública chama a I.A.** O GET de `/view/` é público (LOA-AGR-002). Sem
  finalidade no agrupamento, cada acesso chama o modelo de I.A. (LOA-AGR-070), o que gera custo sem
  autenticação e sem cota (D1 de `ementa-emenda-coletiva.md`). A prévia deve exigir permissão de
  edição?
- D6. **A inclusão substitui os registros contábeis da emenda.** Os registros que o editor fez na tela
  da emenda são trocados pelos percentuais do agrupamento (LOA-AGR-042). Na remoção, a emenda fica
  sem nenhum registro (LOA-AGR-043). É o comportamento desejado, ou a emenda deveria guardar os
  próprios registros?
- D4. **O erro do autosave some.** A falha do PATCH do agrupamento não aparece na tela
  (LOA-AGR-060). Ao contrário da emenda, a tela nem recarrega. A tela deve mostrar o erro?
- D7. **GET que cria registro.** Cada acesso à URL de criação cria um agrupamento (LOA-AGR-010).
  Recarregar a página ou abrir o link duas vezes deixa agrupamentos vazios. A criação deve passar a
  ser por POST?

## Fora do escopo

- Regras de fase, inclusão em agrupamento e coletiva: `docs/specs/loa/fases-emenda.md`.
- Prompt, modelo e tratamento de erro da I.A.: `docs/specs/genia/ementa-emenda-coletiva.md`.
- Listagem, detalhe e exclusão do agrupamento.
- Conteúdo dos modelos de PDF da coletiva (`loa/pdf/agrupamento_preview.html`).
- Edição da emenda: `docs/specs/loa/edicao-emenda.md`.
