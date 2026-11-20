# LOA: edição do agrupamento

Status: observado; D1 a D7 implementadas (LOA-AGR-003, 012, 045 a 047, 053, 063, 064, 082, 083 e
090)
Última verificação: 2026-11-20 (commit `69911f2dd`)
Código principal: `cmj/loa/views/v_agrupamento.py`, `cmj/loa/forms/f_agrupamento.py`,
`cmj/loa/models/m_agrupamento.py`, `cmj/loa/signals.py`, `cmj/api/loa/views/agrupamento.py`,
`cmj/api/loa/views/agrupamentoemendaloa.py`, `cmj/api/loa/views/agrupamentoregistrocontabil.py`,
`_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js`
Testes: `cmj/loa/tests/test_edicao_agrupamento.py` (regras acordadas e LOA-AGR-081). As regras de
fase citadas têm testes em `cmj/loa/tests/test_fases_emenda.py`.

As regras `[observado]` foram obtidas por leitura do código, sem executar os fluxos. As decisões
tomadas sobre as dúvidas estão em "Regras acordadas": `[desejado]` indica que o código ainda precisa
mudar e `[implementado]` indica uma regra `[desejado]` já corrigida e coberta por teste. Quando uma
regra `[observado]` conflitar com uma delas, vale a regra acordada.

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

## Regras acordadas

### Criação reaproveita o agrupamento vazio (D7, decidida em 2026-11-20)

- LOA-AGR-012 [implementado] A criação continua pelo GET, sem formulário (LOA-AGR-010), mas não deixa
  agrupamentos vazios para trás. Antes de criar, o GET olha o último agrupamento da LOA (por `id`) com
  o prefixo "Novo Agrupamento". Se ele ainda tem o nome padrão ("Novo Agrupamento" ou "Novo
  Agrupamento N") e está vazio, a tela abre a edição dele em vez de criar outro. Vazio é não ter
  emendas, registros contábeis, coletivas geradas nem finalidade (`Agrupamento.esta_vazio()`). Nome
  alterado ou qualquer conteúdo fazem a criação seguir como antes.

  Consequência aceita: o GET continua tendo efeito colateral, e dois editores que abrem a criação
  ao mesmo tempo recebem o mesmo agrupamento vazio. Evidência:
  `cmj/loa/models/m_agrupamento.py:170-177`, `cmj/loa/views/v_agrupamento.py:62-91`.

### Pré-visualização exige permissão de edição (D5, decidida em 2026-11-20)

- LOA-AGR-003 [implementado] O GET de `/api/loa/agrupamento/<pk>/view/` exige `emendaloa_full_editor`,
  a mesma permissão da tela de edição, a única que tem link para a prévia. Anônimo e usuário sem a
  permissão são recusados antes de montar o PDF, então a I.A. não é chamada (LOA-AGR-070). Listagem e
  detalhe da API continuam públicos (LOA-AGR-002). As coletivas já geradas são emendas e seguem o
  `/view/` da emenda (LOA-EMD-085). Evidência: `cmj/api/loa/views/agrupamento.py:24-27`,
  `cmj/api/loa/views/agrupamento.py:134-141`.

### Emenda devolvida bloqueia a liberação (D1, decidida em 2026-11-20)

- LOA-AGR-082 [implementado] "Liberar para Protocolo" é recusado quando alguma emenda do agrupamento
  ou alguma coletiva gerada por ele está na fase 10, devolvida ao autor para correção (LOA-FASE-063).
  - A recusa vem do `clean()` do formulário, depois das validações de LOA-AGR-080, e nenhuma emenda
    muda de fase.
  - A mensagem diz que não é possível liberar com emendas devolvidas para correção e lista as
    emendas, uma por linha.
  - Para liberar, o editor remove as devolvidas do agrupamento (LOA-AGR-043) ou espera o autor
    devolvê-las à fase 12.
  - As emendas na fase -10, já transformadas em coletiva, não contam.

  Evidência: `cmj/loa/forms/f_agrupamento.py:279-296`.

### Liberação sem gerar as coletivas (D2, decidida em 2026-11-20)

- LOA-AGR-083 [implementado] Gerar as coletivas antes de liberar é opcional: é uma decisão técnica do
  editor contábil, que pode liberar individualmente emendas que permitem junção.
  - A liberação não bloqueia nem pede confirmação.
  - Se alguma emenda liberada agora (fase entre 1 e 16) formaria coletiva, o detalhe do agrupamento
    mostra a mensagem informativa (`alert-info`) "N emenda(s) que permitem junção em emenda coletiva
    foram liberadas individualmente, sem junção.". A mensagem não as chama de pendência.
  - "Formaria coletiva" segue o critério de LOA-AGR-071, sem chamar a I.A.: permite junção, não tem
    matéria, não está na fase -10 e está num conjunto de unidade e entidade com mais de uma emenda.
  - Sem emendas nessa situação, não há mensagem.

  Evidência: `cmj/loa/models/m_agrupamento.py:179-195`, `cmj/loa/forms/f_agrupamento.py:302-308`,
  `cmj/loa/views/v_agrupamento.py:161-174`.

### Autosave: só campos do model e erro na tela (D4, decidida em 2026-11-20)

- LOA-AGR-063 [implementado] O autosave só envia nome, tipo e finalidade. As buscas, os campos
  `despesa_*` e `perc_despesa` não geram requisição. Substitui LOA-AGR-061. Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:6-12`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:569-576`.
- LOA-AGR-064 [implementado] Quando o PATCH do autosave falha, a tela:
  - mostra a mensagem do servidor como erro suspenso (LOA-AGR-090), com o título "Alteração não
    gravada (<rótulo do campo>).". O texto segue LOA-EMD-084: `detail`, lista de erros ou erros por
    campo, página HTML de erro como "O servidor respondeu com erro <status>." e falha de rede como
    aviso de comunicação;
  - devolve só o campo alterado ao valor gravado, lido de novo do servidor, sem recarregar a página.
    O que o editor fez nos outros campos fica. Por exemplo, apagar o nome devolve 400 e o nome
    gravado volta ao campo.

  A função que monta o texto do erro passou a ser comum à emenda e ao agrupamento. Evidência:
  `_frontend/v2018/src/__apps/loa/mensagens.js`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:578-606`.

### Registros contábeis da emenda agrupada (D6, decidida em 2026-11-20)

Enquanto está no agrupamento, a emenda recebe os registros contábeis dele (LOA-AGR-033 e 042): a
inclusão continua substituindo os registros que ela tinha.

- LOA-AGR-045 [implementado] Os registros da emenda agrupada só mudam pelo agrupamento. A API de
  registro da emenda (`/api/loa/emendaloaregistrocontabil/`) recusa incluir, alterar e excluir
  registro de emenda que está num agrupamento, com 400 e a mensagem "Os registros contábeis desta
  emenda vêm do agrupamento "<nome>". Altere-os no agrupamento.". A recusa vem antes da validação
  dos campos, e a tela da emenda mostra a mensagem (LOA-EMD-061 e LOA-EMD-084). Antes, a inclusão
  e a alteração eram desfeitas no próximo `sync()`, e a exclusão tirava a emenda do agrupamento
  (LOA-AGR-047).
  Evidência: `cmj/api/loa/views/emendaloaregistrocontabil.py:304-340`,
  `cmj/api/loa/views/emendaloaregistrocontabil.py:358`.
- LOA-AGR-046 [implementado] Ao sair do agrupamento, a emenda mantém os registros que tinha por ele,
  já sincronizados com o valor dela no momento da remoção, e o editor os ajusta na tela da emenda.
  Não há mais signal que os apague. Substitui o trecho de LOA-AGR-043 que apagava todos os
  registros. Evidência: `cmj/api/loa/views/agrupamentoemendaloa.py:47-59`, `cmj/loa/signals.py:72-73`.
- LOA-AGR-047 [implementado] Excluir um registro contábil da emenda não mexe no agrupamento. Antes,
  `EmendaLoaRegistroContabil.delete()` apagava por SQL direto o vínculo da emenda com o agrupamento,
  sem signals, para que excluir um registro pela tela da emenda a tirasse do agrupamento. Esse papel
  passou para o botão de remover do agrupamento (LOA-AGR-043), e o `delete()` voltou ao padrão do
  Django. Evidência: `cmj/loa/models/m_registrocontabil.py`, sem `delete()` próprio.

### Finalidade digitada é preservada (D3, decidida em 2026-11-20)

- LOA-AGR-053 [implementado] O agrupamento guarda se a finalidade foi digitada
  (`Agrupamento.finalidade_manual`).
  - **Autosave:** o PATCH com `finalidade` marca a finalidade como digitada. Texto vazio ou só com
    espaços volta ao modo automático. PATCH de outro campo não muda a marcação.
  - **Inclusão e remoção de emenda:** a finalidade digitada é mantida, e a I.A. não é chamada.
  - **Unidades ou entidades diferentes:** a finalidade é apagada e volta ao modo automático, como
    antes. Se ela era digitada, a resposta traz o aviso "A finalidade digitada foi apagada porque as
    emendas do agrupamento não têm mais a mesma unidade e entidade...", que a tela mostra
    (LOA-AGR-090). Sem finalidade digitada, não há aviso.
  - **Ctrl+clique (LOA-AGR-051):** gera de novo por I.A. e substitui também a digitada, que volta ao
    modo automático. Se a I.A. falha, a finalidade digitada é mantida. A gerada antes é apagada, como
    antes.
  - O texto de ajuda do campo descreve essas regras.
  - Agrupamentos já existentes começam no modo automático. A coluna tem default no banco, então a
    versão anterior em execução continua criando agrupamentos.

  Substitui, para a finalidade digitada, o "em todos os casos" de LOA-AGR-050. Evidência:
  `cmj/loa/models/m_agrupamento.py:22-34`, `cmj/loa/models/m_agrupamento.py:60-65`,
  `cmj/loa/models/m_agrupamento.py:197-241`, `cmj/api/loa/views/agrupamento.py:29-36`,
  `cmj/api/loa/views/agrupamento.py:82`, `cmj/api/loa/views/agrupamentoemendaloa.py:72-86`,
  `cmj/loa/forms/f_agrupamento.py:69-76`, `cmj/loa/migrations/0027_agrupamento_finalidade_manual.py`.

### Mensagens da tela (D1, decidida em 2026-11-20)

- LOA-AGR-090 [implementado] A tela de edição não usa `alert()`. As mensagens aparecem suspensas no
  canto superior direito, fecham pelo "×" e não se repetem quando iguais.
  - Erros (vermelho) e avisos (amarelo) ficam até serem fechados. Sucesso (verde) some sozinho
    depois de 8 segundos.
  - Os erros do `clean()` do formulário (LOA-AGR-080 e LOA-AGR-082) saem do topo do formulário e
    aparecem como mensagem com o título "Não foi possível liberar para protocolo.".
  - Gerar coletivas (LOA-AGR-071): "Nenhuma emenda coletiva foi criada." é um aviso. Com coletivas
    criadas, a mensagem de sucesso fica 3 segundos na tela antes de ir para o detalhe.
  - Cancelar coletivas (LOA-AGR-072): a mensagem de sucesso aparece depois do recarregamento.
  - Os avisos da finalidade, falha da I.A. (LOA-AGR-050) e finalidade digitada apagada
    (LOA-AGR-053), têm o título "Finalidade do agrupamento.". O erro do Ctrl+clique (LOA-AGR-051) tem
    o título "Erro ao gerar a finalidade com I.A.".
  - Os erros de gerar e cancelar coletivas são mensagens de erro.
  - Os erros de inclusão e remoção de emenda continuam na própria lista (LOA-AGR-044), e a
    confirmação do cancelamento de coletivas continua em `confirm()`.

  Substitui os `alert()` de LOA-AGR-050, 071 e 072. Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:5-109`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:111-169`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:485-490`,
  `_frontend/v2018/src/__apps/loa/scss/loa.scss:608-621`.

## Regras observadas

### Acesso

- LOA-AGR-001 [observado] Criar, editar e excluir agrupamento pela interface exige
  `emendaloa_full_editor`, que o editor contábil, o Operador da LOA e o superusuário têm. Listagem e
  detalhe são públicos. Evidência: `cmj/loa/views/v_agrupamento.py:15-59`,
  `cmj/loa/views/v_agrupamento.py:142-143`, `cmj/globalrules/map_rules.py:270-284`.
- LOA-AGR-002 [observado] Na API de `agrupamento`, `agrupamentoemendaloa` e
  `agrupamentoregistrocontabil`, todo POST, PATCH e DELETE exige `emendaloa_full_editor`, inclusive
  as actions. Os GET exigem só as permissões públicas de listagem e detalhe, salvo a prévia
  (LOA-AGR-003). Evidência:
  `cmj/api/loa/views/agrupamento.py:13-22`, `cmj/api/loa/views/agrupamentoemendaloa.py:15-24`,
  `cmj/api/loa/views/agrupamentoregistrocontabil.py:291-300`, `sapl/api/permissions.py:12-24`,
  `sapl/api/permissions.py:50-56`.

### Criação e cópia

- LOA-AGR-010 [observado] Abrir a tela de criação (GET) já cria o agrupamento, sem formulário, e
  redireciona para a edição, salvo o reaproveitamento de LOA-AGR-012. O nome é "Novo Agrupamento". Se
  já existe um agrupamento da LOA com esse prefixo, o nome recebe o número final do último deles (por
  `id`) mais 1. Evidência:
  `cmj/loa/views/v_agrupamento.py:58-91`.
- LOA-AGR-011 [observado] O botão de cópia (`POST /api/loa/agrupamento/<pk>/create_copia/`) cria um
  agrupamento com o nome "<nome> (Cópia N)" e a mesma LOA. A cópia leva os registros contábeis
  (despesa, percentual e operação), mas não leva as emendas nem a finalidade. Depois, a tela abre a
  edição da cópia. Evidência: `cmj/loa/models/m_agrupamento.py:111-131`,
  `cmj/api/loa/views/agrupamento.py:55-68`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:112-118`.

### Layout da tela

- LOA-AGR-020 [observado] A tela tem três áreas:
  - **Dados gerais:** nome, área de aplicação (`tipo`, em botões de rádio: não selecionado, Saúde ou
    Áreas Diversas) e finalidade, com os botões de cópia, pré-visualização, cancelar coletivas, gerar
    coletivas, fechar e "Liberar para Protocolo".
  - **Registros contábeis:** "Registrar Deduções e Inserções", com busca de despesa e percentual, e
    "Registros das Despesas Orçamentárias".
  - **Emendas:** "Busca por Emendas" e "Emendas Selecionadas".

  O layout é o mesmo para todos os perfis que acessam a tela. Evidência:
  `cmj/loa/forms/f_agrupamento.py:95-254`.
- LOA-AGR-021 [observado] O percentual da despesa começa em 100,00. Depois de incluir um registro, a
  tela volta o campo para 100,00. Evidência: `cmj/loa/forms/f_agrupamento.py:257`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:266`.

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
  `cmj/loa/models/m_agrupamento.py:511-516`.
- LOA-AGR-031 [observado] Gravar um registro contábil do agrupamento dispara `Agrupamento.sync()`
  (LOA-AGR-033). Excluir um registro apaga, nas emendas do agrupamento, os registros com a mesma
  despesa. Evidência: `cmj/loa/signals.py:41-70`.
- LOA-AGR-032 [observado] A busca e a exclusão de registros funcionam como na edição da emenda
  (LOA-EMD-060 e LOA-EMD-062), com duas diferenças:
  - destaca qualquer termo da busca, sem o mínimo de 3 letras;
  - não avisa quando há mais de 10 resultados.

  O rodapé de totais não é preenchido. Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:171-348`.
- LOA-AGR-033 [observado] `Agrupamento.sync()` refaz os registros contábeis de cada emenda do
  agrupamento, exceto as da fase -10, que o manager padrão oculta:
  - apaga os registros da emenda;
  - cria um registro por registro do agrupamento, no valor de valor da emenda × percentual ÷ 100;
  - quando os percentuais somam zero, joga a diferença de arredondamento na última dedução e na
    última inserção, para que cada lado feche com o valor da emenda.

  Evidência: `cmj/loa/models/m_agrupamento.py:133-168`.

### Emendas do agrupamento

- LOA-AGR-040 [observado] "Emendas Selecionadas" lista todas as emendas do agrupamento, inclusive as da
  fase -10 (`GET /api/loa/agrupamento/<pk>/emendas/`). Cada item mostra:
  - tipo e se a emenda permite junção em coletiva;
  - valor, indicação e finalidade, com link para a edição da emenda;
  - parlamentares;
  - fase: vermelha na 10, amarela na 12 e verde nas demais.

  Evidência: `cmj/api/loa/views/agrupamento.py:38-53`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:358-397`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:492-523`.
- LOA-AGR-041 [observado] A busca de emendas exige ao menos 3 letras e consulta
  `/api/loa/emendaloa/search/`.
  - O resultado traz emendas do ano da LOA com fase menor que 17, filtradas pelo tipo do agrupamento
    quando ele não é "Não selecionado".
  - Ficam de fora as que já estão na lista de selecionadas. As que estão em outro agrupamento aparecem.
  - Emendas na fase 10 aparecem sem o botão de incluir.

  Evidência: `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:399-475`,
  `cmj/api/loa/views/emendaloa.py:371-401`.
- LOA-AGR-042 [observado] Incluir uma emenda envia `POST /api/loa/agrupamentoemendaloa/`. Fases aceitas,
  ano e fase resultante seguem LOA-FASE-058 a LOA-FASE-060.
  - Uma emenda só pertence a um agrupamento; a tentativa de incluí-la em outro dá erro.
  - Gravar o vínculo dispara `Agrupamento.sync()`, que **substitui** os registros contábeis da emenda
    pelos do agrupamento.
  - Por fim, a finalidade é gerada por I.A. (LOA-AGR-050).

  Evidência: `cmj/api/loa/views/agrupamentoemendaloa.py:88-138`, `cmj/loa/signals.py:50-56`,
  `cmj/loa/models/m_agrupamento.py:433-438`.
- LOA-AGR-043 [observado] Remover uma emenda envia `POST /api/loa/agrupamentoemendaloa/delete/`. A
  emenda da fase -10 não pode ser removida (LOA-FASE-042). Antes de desfazer o vínculo, o servidor
  sincroniza o agrupamento e a emenda, e ignora erros nesses passos (só os registra no log). A emenda
  sai do agrupamento com os registros que tinha por ele (LOA-AGR-046) e na mesma fase. Depois, a
  finalidade é gerada de novo (LOA-AGR-050 e 053). Evidência:
  `cmj/api/loa/views/agrupamentoemendaloa.py:26-70`.
- LOA-AGR-044 [observado] Os erros de inclusão e de remoção aparecem em um alerta na própria lista.
  Evidência: `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:390-393`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:467-471`.

### Finalidade

- LOA-AGR-050 [observado] Depois de cada inclusão ou remoção de emenda, o servidor tenta gerar a
  finalidade por I.A.:
  - **Unidade e entidade iguais em todas as emendas:** grava a finalidade gerada.
  - **Unidades ou entidades diferentes:** apaga a finalidade, sem aviso na tela.
  - **Falha da I.A.:** apaga a finalidade e devolve o aviso, que a tela mostra (LOA-AGR-090).

  A finalidade digitada é mantida, salvo com unidades ou entidades diferentes (LOA-AGR-053). Evidência:
  `cmj/loa/models/m_agrupamento.py:197-241`, `cmj/api/loa/views/agrupamentoemendaloa.py:72-86`,
  GENIA-LOA-004, GENIA-LOA-006.
- LOA-AGR-051 [observado] Ctrl+clique na finalidade pede a geração por I.A.
  (`PATCH /api/loa/agrupamento/<pk>/generate_finalidade_global/`). Enquanto espera, o campo fica
  somente leitura com "Atualizando com I.A...". Se a geração falha, o erro aparece como mensagem
  (LOA-AGR-090) e o campo volta ao texto gravado no servidor, editável. Substitui a digitada
  (LOA-AGR-053). Evidência: `cmj/api/loa/views/agrupamento.py:70-87`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:543-566`.
- LOA-AGR-052 [observado] Ao abrir a tela e depois de cada inclusão ou remoção, o campo de finalidade
  mostra "Atualizando..." até receber o valor do servidor. Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:362`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:478-483`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:458`.

### Autosave

- LOA-AGR-060 [observado] O autosave reage ao evento `change` dos campos do formulário. Cada mudança
  envia `PATCH /api/loa/agrupamento/<pk>/` com `{campo: valor}`. É assim que nome, tipo e finalidade
  são gravados. Se dá certo, a tela recarrega os registros contábeis. Só os campos do model geram
  PATCH (LOA-AGR-063), e a falha aparece na tela (LOA-AGR-064). Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:566-589`.
- LOA-AGR-061 [observado] Campos que não são do model também geravam PATCH: as buscas, os campos
  `despesa_*` e `perc_despesa`. O serializer os ignorava. Substituída por LOA-AGR-063.
- LOA-AGR-062 [observado] Enter não envia o formulário. No campo de busca de despesa, Enter seleciona o
  resultado quando há só um. Evidência:
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:529-541`.

### Emendas coletivas

- LOA-AGR-070 [observado] O botão de pré-visualização abre
  `GET /api/loa/agrupamento/<pk>/view/?model=1` em nova aba.
  - O PDF tem uma emenda coletiva por conjunto de unidade e entidade, montada pelas regras de
    LOA-FASE-021. A prévia inclui as emendas da fase -10.
  - Sem coletiva possível, o PDF tem uma página "Nenhuma Emenda gerada", com o total de emendas e de
    conjuntos.
  - Se o agrupamento não tem finalidade, a prévia pede a finalidade automática à I.A. (GENIA-LOA-005).
  - Só quem edita o agrupamento abre a prévia (LOA-AGR-003).

  Evidência: `cmj/api/loa/views/agrupamento.py:134-240`, `cmj/loa/models/m_agrupamento.py:243-335`,
  `cmj/loa/forms/f_agrupamento.py:113-117`.
- LOA-AGR-071 [observado] "Gerar Emendas Coletivas"
  (`POST /api/loa/agrupamento/<pk>/gerar_emenda_coletiva/`) cria uma coletiva por conjunto com mais
  de uma emenda. Cada coletiva recebe:
  - como valor, a soma dos valores por parlamentar;
  - os parlamentares com os valores somados;
  - as inserções e deduções somadas por despesa;
  - a finalidade do agrupamento ou, sem ela, a automática.

  Fases e dono seguem LOA-FASE-017, LOA-FASE-018 e LOA-FASE-064. A tela mostra quantas coletivas
  foram criadas e vai para o detalhe do agrupamento, ou avisa que nenhuma foi (LOA-AGR-090).
  Evidência: `cmj/loa/models/m_agrupamento.py:354-422`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:119-147`.
- LOA-AGR-072 [observado] "Cancelar Emendas Coletivas" pede confirmação e chama
  `POST /api/loa/agrupamento/<pk>/cancelar_emendas_coletivas/`. O servidor faz o efeito de
  LOA-FASE-019, LOA-FASE-056 e LOA-FASE-057 e exclui as coletivas geradas. Depois, a tela recarrega
  e mostra o resultado (LOA-AGR-090).
  Evidência: `cmj/loa/models/m_agrupamento.py:337-352`,
  `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:148-168`.

### Liberar para protocolo

- LOA-AGR-080 [observado] O botão "Liberar para Protocolo" envia o formulário por POST. Antes de
  qualquer outra coisa, o `clean()` exige:
  - ao menos um registro contábil no agrupamento;
  - percentuais que somem zero.

  Evidência: `cmj/loa/forms/f_agrupamento.py:136-138`, `cmj/loa/forms/f_agrupamento.py:259-278`.
- LOA-AGR-081 [observado] Com o formulário válido, as emendas do agrupamento e as coletivas geradas
  passam para a fase 17, conforme LOA-FASE-016, salvo o bloqueio de LOA-AGR-082 e com o aviso de
  LOA-AGR-083. Todas são salvas, mesmo as que já estavam na 17 ou acima. O `save()` do formulário não
  grava os campos do próprio agrupamento, que dependem só do autosave. Depois, a tela vai para o
  detalhe. Evidência: `cmj/loa/forms/f_agrupamento.py:298-332`,
  `cmj/loa/views/v_agrupamento.py:176-180`.

## Dúvidas

Nenhuma em aberto. Em 2026-11-20, D1 virou LOA-AGR-082 e LOA-AGR-090, D2 virou LOA-AGR-083, D3 virou
LOA-AGR-053, D4 virou LOA-AGR-063 e LOA-AGR-064, D5 virou LOA-AGR-003, D6 virou LOA-AGR-045 a
LOA-AGR-047 e D7 virou LOA-AGR-012.

## Fora do escopo

- Regras de fase, inclusão em agrupamento e coletiva: `docs/specs/loa/fases-emenda.md`.
- Prompt, modelo e tratamento de erro da I.A.: `docs/specs/genia/ementa-emenda-coletiva.md`.
- Listagem, detalhe e exclusão do agrupamento.
- Conteúdo dos modelos de PDF da coletiva (`loa/pdf/agrupamento_preview.html`).
- Edição da emenda: `docs/specs/loa/edicao-emenda.md`.
