# LOA: listagem, filtragem e PDF das emendas

Status: observado
Última verificação: 2026-11-20 (sobre o commit `cb6ff902e`, com as mudanças descritas aqui)
Código principal: `cmj/loa/views/v_emendaloa.py` (`EmendaLoaCrud.ListView`),
`cmj/loa/forms/f_emendaloa.py` (`EmendaLoaFilterSet`), `cmj/loa/forms/f_mixins.py`,
`cmj/loa/signals.py`, `_templates/v2018/loa/emendaloa_filter.html`,
`_templates/v2018/loa/emendaloa_filter_cache.html`, `_templates/v2018/loa/pdf/emendaloa_list.html`,
`_templates/v2018/css/emendaloa-list.css`, `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaList.js`,
`_frontend/v2018/src/__apps/loa/scss/loa.scss`
Testes: `cmj/loa/tests/test_listagem_emendas.py` e `cmj/utils/tests/test_utils_report.py`, para as
regras `[implementado]`. As demais regras não têm teste.

As regras `[observado]` descrevem o que o código faz hoje e nenhuma foi confirmada como
regra de negócio. Foram obtidas por leitura do código. As marcadas com "(executado)" também foram
conferidas em 2026-11-20 no banco de desenvolvimento, chamando a view pela rota real com
`RequestFactory`, sem gravar nada, como anônimo, como usuário comum e como operador de autor. Os PDFs
foram gerados de verdade para a LOA 2026 (385 emendas), sempre com filtro, e para a LOA 2023 no caso
das emendas sem unidade.

Não foi executado:

- O JavaScript do v2018 (regras LOA-LST-066 a 074): não havia navegador. Só o HTML recebido por ele
  foi conferido.
- O cache do cartão no servidor de desenvolvimento, que usa `DummyCache`. LOA-LST-040 e 041 foram
  conferidas por testes, com cache em memória, e por script, no Redis do compose (banco 15).
- `?zip` e o registro de emendas: o primeiro não aceita filtro e o segundo grava dados.
- O acesso anônimo a LOA não publicada: não há LOA não publicada na base de desenvolvimento.

## Escopo

Tela aberta em `/loa/<pk da LOA>/emendaloa` (rota `cmj.loa:emendaloa_list`): quem acessa, o que é
listado, filtros, paginação, cartão de cada emenda e seu cache, geração do PDF da listagem
(`?pdf`) e o que a tela depende do `_frontend/v2018`. As ações `?zip` e de registro, atendidas pela
mesma view, entram só no que afeta esta tela.

## Regras

### Acesso e conjunto listado

- LOA-LST-001 [observado] A rota é `/loa/<pk>/emendaloa`, sem barra final, e `<pk>` é o id da LOA.
  Evidência: `cmj/loa/urls.py:12-19`, `sapl/crud/base.py:1382-1384`; URL resolvida como
  `/loa/1/emendaloa` (executado).
- LOA-LST-002 [observado] A tela não exige permissão nem login: `RP_LIST` está em `public` e é
  retirado de `permission_required`. Evidência: `cmj/loa/views/v_emendaloa.py:91`,
  `sapl/crud/base.py:295-302`, `sapl/crud/base.py:206-218`.
- LOA-LST-003 [implementado] A LOA da URL só é carregada entre as que o usuário pode ver
  (`EmendaLoa.service.loas_visiveis`, mesma regra da LOA-LST-006). Id inexistente ou LOA que o
  usuário não pode ver respondem 404 na lista, no PDF, no ZIP e no registro, antes até da verificação
  reCAPTCHA do PDF (LOA-LST-085). Assim, o formulário não mostra parlamentares, entidades e unidades
  de LOA que o usuário não pode ver. Evidência: `cmj/loa/views/v_emendaloa.py:243-252`,
  `cmj/loa/services/s_emendaloa.py:250-284`. Testes: `test_loa_inexistente_responde_404`,
  `test_anonimo_recebe_404_em_loa_nao_publicada`; na base de desenvolvimento,
  `/loa/999999/emendaloa` respondeu 404 na lista e com `?pdf` (executado).
- LOA-LST-004 [observado] São listadas as emendas da LOA da URL com `fase > 0`: o manager padrão
  esconde as transformadas em coletiva (fase -10). Evidência: `sapl/crud/base.py:1429-1438`,
  `cmj/loa/models/m_emendaloa.py:35-39`; SQL com `"fase" > 0 AND "loa_id" = 1` (executado).
- LOA-LST-005 [implementado] Para usuário anônimo, LOA não publicada responde 404 (LOA-LST-003), e a
  lista só traz emendas de LOA com `publicado=True`. Evidência: `cmj/loa/views/v_emendaloa.py:243-252`,
  `cmj/loa/views/v_emendaloa.py:941-943`, `cmj/loa/services/s_emendaloa.py:250-284`. Teste:
  `test_anonimo_recebe_404_em_loa_nao_publicada`, para a lista, `?pdf`, `?zip` e `?registrar`.
- LOA-LST-006 [implementado] Em LOA publicada, qualquer usuário vê as emendas de todas as fases e de
  todos os autores. Em LOA não publicada, a conta comum recebe 404; o operador de autor vê todas se
  a matéria da LOA ainda não virou norma, e recebe 404 se já virou; quem tem
  `loa.emendaloa_full_editor`, e portanto o superusuário, vê todas. É a mesma regra da lista de
  LOAs, concentrada em `EmendaLoa.service.loas_visiveis`. Evidência:
  `cmj/loa/views/v_emendaloa.py:941-943`, `cmj/loa/services/s_emendaloa.py:250-284`,
  `cmj/loa/views/v_loa.py:124-141`. Testes: `test_conta_comum_recebe_404_em_loa_nao_publicada`,
  `test_operador_e_contabilidade_veem_loa_nao_publicada`,
  `test_operador_recebe_404_em_loa_nao_publicada_cuja_materia_virou_norma`,
  `test_qualquer_um_ve_todas_as_fases_de_loa_publicada`.
- LOA-LST-083 [implementado] A consulta pela API (`/api/loa/emendaloa/`, inclusive detalhe,
  `view`, `search` e `totais`) segue a LOA-LST-005 e a LOA-LST-006; emenda fora dela responde 404.
  Escrita pela API não muda: continua decidida pelas permissões de edição. Evidência:
  `cmj/api/loa/views/emendaloa.py:61-67`. Testes:
  `test_api_anonimo_nao_consulta_emenda_de_loa_nao_publicada`,
  `test_api_operador_consulta_emenda_de_loa_nao_publicada`.
- LOA-LST-091 [implementado] A API de emendas (detalhe, lista e `search`) só devolve `metadata` e
  `search` a quem pode editar a emenda em alguma fase: `change_emendaloa`,
  `emendaloa_full_editor` (e portanto o superusuário) ou o autor do dono. Para os demais, inclusive o
  anônimo e o operador de outro autor, esses campos não aparecem. O `owner` exige, além disso, a
  permissão de listagem do model (`list_emendaloa`), pela regra geral da API para relação com
  usuário (API-SER-032): o operador do autor não o recebe. A tela de edição continua
  recebendo `metadata.style`. Evidência: `cmj/api/loa/serializers/__init__.py:20-44`,
  `cmj/loa/services/s_emendaloa.py:156-169`. Testes:
  `test_api_oculta_campos_internos_de_quem_nao_edita`,
  `test_api_mostra_campos_internos_a_quem_edita`,
  `test_busca_da_api_oculta_campos_internos_do_anonimo`; na LOA 2026, o detalhe de uma emenda pela
  API veio sem os três campos para o anônimo e com eles para o superusuário (executado).
- LOA-LST-007 [observado] A ordem da tela é `tipo` decrescente (Áreas Diversas 99, Saúde 10,
  Modificativa 0), depois `fase` crescente, número da matéria crescente e `id` decrescente. Não há
  ordenação pelo usuário (`ordered_list` é `False`). Evidência:
  `cmj/loa/views/v_emendaloa.py:943`, `cmj/loa/views/v_emendaloa.py:97-99`,
  `cmj/loa/models/m_emendaloa.py:62-69`.
- LOA-LST-008 [observado] A lista é paginada de 10 em 10 e os links de página repetem os parâmetros
  de filtro da URL. Evidência: `sapl/crud/base.py:441`, `sapl/crud/base.py:595-598`,
  `_templates/v2018/paginacao.html:6`, `_templates/v2018/crud/list.html:92`; 385 emendas, 10 por
  página (executado).
- LOA-LST-079 [observado] Página além da última responde 404 ("Página inválida"). Evidência:
  `?page=9999` na LOA 2026 (executado).
  Evidência: `cmj/loa/views/v_emendaloa.py:162`, `sapl/crud/base.py:441`.
- LOA-LST-009 [observado] Acima da lista aparece "Foi encontrada uma Emenda Parlamentar" ou "Foram
  encontradas N Emendas Parlamentares", com o total filtrado. Sem resultado aparece "Nenhuma Emenda
  Parlamentar encontrada com os critérios de busca acima!". Evidência:
  `_templates/v2018/loa/emendaloa_filter.html:43-54`.
- LOA-LST-010 [observado] O título da tela é "Emendas Impositivas/Modificativas à LOA <ano>" seguido
  da epígrafe curta da matéria da LOA, quando existe. O título padrão do CRUD é removido do contexto.
  Evidência: `cmj/loa/views/v_emendaloa.py:238-241`, `cmj/loa/views/v_emendaloa.py:950`,
  `_templates/v2018/base.html:75-77`.
- LOA-LST-011 [observado] O template usado é `loa/emendaloa_filter.html`, pelo sufixo `_filter` do
  `FilterView`, que vem antes do CRUD na herança. Evidência: `cmj/loa/views/v_emendaloa.py:162`;
  `template_name_suffix == "_filter"`, ordem de herança e template da resposta (executado).
- LOA-LST-012 [observado] A tela chega pelo menu da LOA ("Emendas Impositivas/Modificativas" ou
  "Emendas em Elaboração", conforme a LOA tenha ou não norma) e por links do resumo da LOA que já
  trazem `?unidade=`, `?entidade=` e `?parlamentares=`. Evidência: `_templates/v2018/loa/subnav.yaml:8-9`,
  `_templates/v2018/loa/subnav_loa_em_tramitacao.yaml:4-5`, `cmj/loa/views/v_mixins.py:23-35`,
  `_templates/v2018/loa/emendaloa_totalize_unidade.html:22`,
  `_templates/v2018/loa/emendaloa_totalize_unidade.html:39`,
  `_templates/v2018/loa/emendaloa_totalize_entidade.html:23`,
  `_templates/v2018/loa/emendaloa_totalize_entidade.html:40`.

### Botões da tela

- LOA-LST-013 [observado] O botão "OpenAPI" leva à listagem da API `/api/loa/emendaloa/`, que usa
  outro filterset (`cmj/api/forms.py`), não o desta tela. Evidência:
  `_templates/v2018/loa/emendaloa_filter.html:5-12`, `cmj/api/loa/views/emendaloa.py:14`,
  `cmj/api/forms.py:58`.
- LOA-LST-014 [observado] O botão "Adicionar" aparece para quem tem a permissão de inclusão e também
  para superusuário ou operador de autor sem ela. Evidência: `cmj/loa/views/v_emendaloa.py:101-113`,
  `_templates/v2018/crud/list.html:31-35`; ausente para anônimo e usuário comum, presente para
  operador (executado).
- LOA-LST-015 [implementado] Os botões "Baixar Emendas Liberadas" (`?zip`) e "Registrar Emendas
  Liberadas" (formulário POST, LOA-LST-016) só aparecem para operador de autor quando existe, na LOA, emenda em fase
  `LIBERACAO_CONTABIL` (17) ou posterior cujo dono seja operador do mesmo autor que ele. Cada usuário
  opera um único autor (o cadastro de usuário não permite mais de um), e botões, ZIP e registro usam
  esse autor. Essa checagem ignora os filtros da tela. Evidência:
  `cmj/loa/views/v_emendaloa.py:186-219`, `cmj/loa/views/v_emendaloa.py:221-236`,
  `_templates/v2018/loa/emendaloa_filter.html:14-36`. Teste:
  `test_botoes_de_registro_consideram_as_emendas_dos_operadores_do_autor`; presentes para um
  operador e ausentes para anônimo e usuário comum (executado).
- LOA-LST-016 [implementado] "Registrar Emendas Liberadas" é um formulário POST para a própria
  listagem, com token CSRF e o campo `registrar`, e pede confirmação em JavaScript antes do envio. O
  registro só é aceito por POST com CSRF válido: POST sem token responde 403, GET com `?registrar`
  responde 405 sem registrar nada, e POST sem o campo `registrar` responde 405. Evidência:
  `cmj/loa/views/v_emendaloa.py:254-271`, `_templates/v2018/loa/emendaloa_filter.html:23-32`,
  `_templates/v2018/loa/emendaloa_filter.html:79-84`. Testes:
  `test_botao_de_registro_e_formulario_post_com_csrf`,
  `test_registro_por_get_responde_405_sem_registrar`, `test_registro_por_post_sem_csrf_e_recusado`,
  `test_post_sem_registrar_responde_405`; na LOA 2026, a listagem de um operador trouxe o formulário
  POST com o token e nenhum link `?registrar`, e o GET com `?registrar` respondeu 405 sem disparar o
  registro (executado).
- LOA-LST-017 [implementado] No registro (LOA-LST-016), o pedido recusado volta para a listagem da LOA com
  o aviso: ao anônimo, "Ação não permitida para usuários anônimos.", e a quem não opera nenhum autor,
  "Ação não permitida. Usuário não é operador de nenhum autor parlamentar.". Com registro já em
  andamento, ou depois de iniciado o registro, o usuário vai para a lista de proposições, onde
  acompanha o progresso. Evidência: `cmj/loa/views/v_emendaloa.py:260-271`,
  `cmj/loa/views/v_emendaloa.py:273-333`. Testes:
  `test_registro_recusado_volta_para_a_listagem_com_aviso`,
  `test_registro_do_operador_vai_para_a_lista_de_proposicoes`; na LOA 2026, anônimo e conta comum
  voltaram para `/loa/2026/emendaloa` com o aviso, sem disparar o registro (executado). O registro
  gera o PDF de cada emenda no processo, por `EmendaLoa.service.documento_pdf`, sem requisição HTTP, e
  funciona também em LOA não publicada (`cmj/loa/models/m_emendaloa.py:868-890`, teste
  `test_registro_pela_listagem_gera_pdf_sem_http_em_loa_nao_publicada`).
- LOA-LST-084 [retirada] Substituída por LOA-EMD-086 de `docs/specs/loa/edicao-emenda.md`: o registro de
  proposição pelo detalhe da emenda foi removido em 2026-11-20.
- LOA-LST-018 [observado] Com `?zip`, usuário anônimo ou que não seja superusuário nem operador de
  autor recebe `PermissionDenied`. Sem emenda disponível, a tela é exibida com a mensagem "Nenhuma
  Emenda Impositiva/Modificativa disponível para download.". Evidência:
  `cmj/loa/views/v_emendaloa.py:351-372`.
- LOA-LST-019 [implementado] O ZIP reúne as emendas da LOA-LST-015 e ignora os filtros da tela. Cada
  PDF é gerado no próprio processo por `EmendaLoa.service.documento_pdf`, o mesmo usado pela action
  `view` da API, com o estilo gravado na emenda e `settings.BASE_URL` como base dos endereços
  relativos. A geração é feita dentro da requisição: na LOA 2026, o maior ZIP (77 emendas) levaria perto
  de 30 s, estimados por 0,36 s por PDF medidos em dev, abaixo do limite de 300 s do gunicorn e do nginx em produção. Erro ao gerar um PDF é
  registrado no log e deixa a emenda fora do arquivo; o ZIP leva então o arquivo
  `LEIA-ME_emendas_nao_incluidas.txt`, que lista as emendas omitidas (id e epígrafe da matéria) e
  orienta a baixar de novo ou procurar o suporte. Sem falha, esse arquivo não existe. Evidência:
  `cmj/loa/views/v_emendaloa.py:58-72`, `cmj/loa/views/v_emendaloa.py:359-423`,
  `cmj/loa/services/s_emendaloa.py:308-348`, `cmj/api/loa/views/emendaloa.py:297`. Testes:
  `test_zip_gera_os_pdfs_no_processo_sem_usar_o_host`,
  `test_zip_omite_emenda_cujo_pdf_falha_e_lista_no_leia_me`, `test_zip_sem_falha_nao_tem_leia_me`,
  `test_documento_pdf_numera_artigos_a_partir_de_1_em_cada_documento`; na LOA 2026, o ZIP do autor
  com 23 emendas, com falha simulada numa delas, saiu em 6,7 s com 22 PDFs e o arquivo listando a
  emenda 444 (executado).

### Filtros

- LOA-LST-020 [observado] O formulário usa GET e tem dois blocos: "Pesquisa de Emendas Parlamentares"
  (parlamentares, entidade, unidade, fase, tipo, autoria e busca por termos) e "Listagem em PDF"
  (totalização, via de totalização, quebra de página e botão "Gerar PDF"). Evidência:
  `cmj/loa/forms/f_emendaloa.py:999-1078`.
- LOA-LST-021 [observado] Filtros diferentes se combinam com E. Dentro de `tipo`, de `fase` e de
  `parlamentares`, os valores marcados se combinam com OU. Evidência:
  `cmj/loa/forms/f_emendaloa.py:708-720`, `cmj/loa/forms/f_emendaloa.py:942-952`; SQL com `AND` entre
  os filtros (executado).
- LOA-LST-022 [observado] `parlamentares` oferece os parlamentares da LOA; quando a matéria da LOA já
  virou norma, só os que têm emenda. O filtro mantém a emenda que tenha ao menos um dos marcados.
  Evidência: `cmj/loa/forms/f_mixins.py:12-20`, `cmj/loa/forms/f_emendaloa.py:771-776`,
  `cmj/loa/forms/f_emendaloa.py:942-952`.
- LOA-LST-023 [observado] Cada parlamentar aparece como foto: o HTML do formulário é reescrito por
  expressão regular depois de renderizado, com uma consulta por parlamentar. Evidência:
  `cmj/loa/forms/f_emendaloa.py:887-940`.
- LOA-LST-024 [implementado] `fase` oferece 25, 30, 40, 50, 60 e 99 quando a matéria da LOA já tem
  norma jurídica, e 10, 12, 15, 17 e 20 quando ainda não tem. A fase -10 nunca é oferecida. É o mesmo
  critério da visibilidade (LOA-LST-006). Evidência: `cmj/loa/forms/f_emendaloa.py:1083-1089`,
  `cmj/loa/models/m_emendaloa.py:89-105`. Testes: `test_loa_com_norma_oferece_fases_de_25_em_diante`,
  `test_loa_sem_norma_oferece_fases_ate_20`; a LOA 2026, com norma, ofereceu 25 a 99, e a LOA 2027,
  sem norma, 10 a 20 (executado).
- LOA-LST-025 [implementado] Valor fora das opções num filtro (por exemplo, uma fase não oferecida) é
  ignorado: os demais filtros valem e o campo mostra o erro. Com `?pdf`, o PDF não é gerado e a tela
  aparece com os filtros, o erro no campo e o aviso "Há filtros inválidos, indicados no formulário.
  Corrija-os para gerar o PDF.". Evidência: `cmj/loa/views/v_emendaloa.py:164-165`,
  `cmj/loa/views/v_emendaloa.py:335-345`. Testes: `test_filtro_invalido_e_ignorado_com_aviso_no_campo`,
  `test_pdf_com_filtro_invalido_mostra_a_tela_com_aviso`; na LOA 2026, `?fase=10&tipo=10` trouxe as
  45 emendas de saúde com erro no campo fase, e o mesmo com `?pdf` devolveu a tela HTML (executado).
- LOA-LST-087 [implementado] LOA sem matéria legislativa não abre a tela: a lista, o PDF, o ZIP e o
  registro respondem 404, porque sem matéria não há emenda a listar. Evidência:
  `cmj/loa/views/v_emendaloa.py:243-252`. Teste: `test_loa_sem_materia_nao_abre_a_listagem`; na base
  de desenvolvimento não há LOA sem matéria.
- LOA-LST-026 [observado] `tipo` oferece Em.Imp. Saúde, Em.Imp. Áreas Diversas e Emenda Modificativa.
  Evidência: `cmj/loa/forms/f_emendaloa.py:708-713`, `cmj/loa/forms/f_emendaloa.py:1090`.
- LOA-LST-027 [observado] `autoria` tem "Ambas" (padrão, sem filtro), "Individual" (exatamente um
  parlamentar na emenda) e "Coletiva" (mais de um). A contagem considera todos os parlamentares da
  emenda, independentemente do filtro `parlamentares`. Evidência:
  `cmj/loa/forms/f_emendaloa.py:722-734`, `cmj/loa/forms/f_emendaloa.py:974-992`.
- LOA-LST-028 [acordado] "Busca por termos" (parâmetro `finalidade`) separa o texto por espaços e
  exige que todos os termos apareçam no campo `search` da emenda, sem diferenciar acentos nem
  maiúsculas. Não pesquisa a coluna `finalidade` diretamente. Evidência:
  `cmj/loa/forms/f_emendaloa.py:778-782`, `cmj/loa/forms/f_emendaloa.py:963-972`; SQL com
  `UPPER(UNACCENT("search")) LIKE` por termo; `saude` e `saúde` devolveram as mesmas 56 emendas
  (executado).
- LOA-LST-029 [acordado] O campo `search` é montado no `save()` da emenda com a epígrafe curta da
  matéria, o texto dos artigos e os nomes dos parlamentares, sem acentos, e não é regerado de outra
  forma. Mudanças que não passam pelo `save()` da emenda só entram na busca no próximo `save()`; na
  base de desenvolvimento, 316 das 385 emendas da LOA 2026 têm `search` diferente do que o código
  atual geraria (por exemplo, sem "acrescenta-se" e "caput" na emenda 366). Mantido assim por
  decisão em 2026-11-20. Evidência: `cmj/loa/models/m_emendaloa.py:375-399`,
  `cmj/mixins.py:406-442`.
- LOA-LST-030 [observado] `entidade` oferece as entidades ativas usadas em emendas da LOA e `unidade`
  as unidades orçamentárias usadas em emendas da LOA; cada um filtra por igualdade. Evidência:
  `cmj/loa/forms/f_emendaloa.py:790-815`, `cmj/loa/forms/f_emendaloa.py:1092-1103`.
- LOA-LST-031 [observado] Existe o filtro `indicacao`, por igualdade exata, que não aparece no
  formulário e só é alcançado pela URL. Evidência: `cmj/loa/forms/f_emendaloa.py:872-884`,
  `cmj/loa/forms/f_emendaloa.py:1006-1068`; `indicacao: CharFilter:exact` (executado).
- LOA-LST-032 [observado] `agrupamento`, `tipo_agrupamento` e `quebrar_pagina` não filtram: só
  configuram o PDF. Evidência: `cmj/loa/forms/f_emendaloa.py:954-961`.

### Cartão da emenda


- LOA-LST-033 [observado] Cada emenda é um cartão com: fotos dos parlamentares (cada foto é um link
  para a listagem filtrada por ele), título com link para o detalhe (sigla, número e ano da matéria,
  ou o tipo quando não há matéria), selos de tipo e de fase, valor original e, se houver ajustes,
  valor final. Evidência: `_templates/v2018/loa/emendaloa_filter_cache.html:8-76`.
- LOA-LST-034 [observado] O ícone de PDF da emenda (`/api/loa/emendaloa/<id>/view/`) aparece para
  qualquer visitante quando a fase é `LIBERACAO_CONTABIL` e a emenda não permite junção em coletiva.
  Evidência: `_templates/v2018/loa/emendaloa_filter_cache.html:32-36`.
- LOA-LST-035 [observado] Os selos "Emenda Coletiva", "Disponível para Junção em Emenda Coletiva" e
  "Emenda Individual" só aparecem para usuário autenticado e emenda com fase menor que 20. Evidência:
  `_templates/v2018/loa/emendaloa_filter_cache.html:45-51`.
- LOA-LST-036 [observado] O corpo do cartão mostra unidade orçamentária, entidade (com CNES ou, na
  falta dele, CNPJ, LOA-LST-090), a LOA e a matéria legislativa quando há matéria, e o "OBJETO"
  (`ementa_format`), com aviso quando há ajuste técnico. Evidência:
  `_templates/v2018/loa/emendaloa_filter_cache.html:80-121`.
- LOA-LST-090 [implementado] A entidade beneficiária é pessoa jurídica: o campo `cpfcnpj` da
  entidade só aceita CNPJ com dígitos verificadores válidos, com ou sem máscara e com zeros à
  esquerda, ou vazio (só zeros conta como vazio). CPF e CNPJ inválido são recusados com "Informe um
  CNPJ válido. A entidade beneficiária é pessoa jurídica." no formulário do cadastro de entidades e
  na API. O cartão rotula o número como "CNPJ". A importação do CNES grava sem passar pelo
  validador. Evidência: `cmj/loa/models/m_entidade.py:12-36`,
  `cmj/loa/models/m_entidade.py:119-126`, `cmj/loa/migrations/0028_alter_entidade_cpfcnpj.py`
  (sem SQL), `_templates/v2018/loa/emendaloa_filter_cache.html:87-93`. Testes:
  `test_entidade_aceita_cnpj_valido_ou_vazio`, `test_entidade_recusa_cpf_e_cnpj_invalido`,
  `test_formulario_da_entidade_recusa_cpf`, `test_api_recusa_entidade_com_cpf`,
  `test_cartao_rotula_o_numero_como_cnpj`; na base de desenvolvimento, das 353 entidades, 352
  passam no validador e só a 350, com número inválido e sem emenda, é recusada; nenhuma tem CPF
  (executado).
- LOA-LST-037 [observado] O cartão tem abas, cada uma só quando há dados: Prestação de Contas,
  Empenhos (com totais empenhado, liquidado, pago e anulado), Ajustes Técnicos, Registros Contábeis
  e, quando há matéria, Tramitações e Documentos Acessórios. Nenhuma aba abre selecionada.
  Evidência: `_templates/v2018/loa/emendaloa_filter_cache.html:123-393`.
- LOA-LST-038 [observado] Cada cartão tem um botão que o exibe em tela cheia pela API de fullscreen
  do navegador. Evidência: `_templates/v2018/loa/emendaloa_filter.html:59-61`,
  `_templates/v2018/loa/emendaloa_filter.html:86-110`.
- LOA-LST-039 [acordado] A listagem não usa a tabela padrão do CRUD: `list_field_names` só tem `id`,
  a `ListView` não tem métodos `hook_*` de coluna, e o template mostra os cartões no lugar da
  tabela. Os `hook_*` antigos, a lista comentada de colunas, o template
  `emendaloa_filter copy.html` e o include comentado do cartão foram removidos em 2026-11-20, sem
  mudança no HTML da tela. Evidência: `cmj/loa/views/v_emendaloa.py:95`,
  `_templates/v2018/loa/emendaloa_filter.html:42-74`; na LOA 2026, o HTML da listagem, para anônimo
  e superusuário, na página inicial e em `?fase=50&page=2`, saiu idêntico ao de antes da remoção,
  exceto pelo token CSRF e por linhas em branco (executado).

### Cache do cartão

- LOA-LST-040 [implementado] O cartão é guardado em cache por 1 dia, com chave `l.el.l` mais o id da
  emenda e se o usuário está logado: há uma versão para anônimo e outra para usuário logado, porque
  os selos de coletiva e individual (LOA-LST-035) só aparecem para quem está logado. O cache é
  ignorado, na leitura e na gravação, quando `DEBUG` está ligado ou quando o usuário está
  autenticado e a emenda não tem matéria. Evidência:
  `_templates/v2018/loa/emendaloa_filter.html:62-68`, `cmj/context_processors.py:13-14`. Testes:
  `test_cartao_fica_em_cache_por_um_dia`, `test_anonimo_nao_ve_selo_guardado_por_usuario_logado`; com `DEBUG` desligado
  e o Redis do compose, a listagem da LOA 2026 na fase 50 guardou os 10 cartões da página com prazo
  de 86.399 segundos (executado).
- LOA-LST-041 [implementado] Todo `post_save` e `post_delete` de model dos apps `loa`, `materia` e
  `parlamentares` apaga o cartão das emendas que mostram dados dele: a própria emenda; as emendas da
  matéria, quando muda a matéria, uma tramitação ou um documento acessório; as emendas ligadas ao
  empenho; as emendas da entidade, da unidade, do parlamentar ou da LOA; e as emendas apontadas pelo
  campo `emendaloa` (FK ou M2M) dos demais models. As duas versões do cartão são apagadas juntas.
  Model fora desse mapa não apaga nada. Mudanças
  feitas por `QuerySet.update()` e `bulk_*` não disparam signal e só aparecem quando o cache expira.
  Evidência: `cmj/loa/signals.py:76-161`. Testes: `test_cartao_e_renovado_por_tramitacao_da_materia`,
  `test_cartao_e_renovado_por_empenho_entidade_e_parlamentar`,
  `test_model_sem_relacao_nao_apaga_cartao_de_emenda_com_o_mesmo_id`; no Redis do compose, o
  signal de uma tramitação da matéria da emenda 435 apagou só o cartão dela, e os outros 9 da
  página ficaram; depois de a listagem ser aberta por anônimo e por usuário logado, o signal da
  emenda 435 apagou as duas versões do cartão (executado, sem gravar no banco).
- LOA-LST-042 [observado] Em desenvolvimento o cache é `DummyCache` e nada disso é exercitado.
  Evidência: `CACHES["default"]["BACKEND"]` e `DEBUG == True` (executado no ambiente local).
  Evidência: `cmj/settings/project.py:160-167`.

### PDF da listagem

- LOA-LST-043 [observado] "Gerar PDF" envia o formulário com `pdf` na query; a view responde com
  `application/pdf`, `Content-Disposition: inline`, nome `emendaloa_<ano>.pdf` e cabeçalhos contra
  cache. Evidência: `cmj/loa/forms/f_emendaloa.py:1051-1060`,
  `cmj/loa/views/v_emendaloa.py:335-349`, `cmj/loa/views/v_emendaloa.py:458-465`; resposta
  `application/pdf`, `inline; filename="emendaloa_2026.pdf"` (executado).
- LOA-LST-044 [observado] O PDF está disponível a qualquer visitante, com as mesmas regras de
  visibilidade da lista (LOA-LST-002, 005 e 006), e traz todas as emendas filtradas, sem paginação.
  O anônimo passa antes pela verificação da LOA-LST-085. Evidência:
  `cmj/loa/views/v_emendaloa.py:335-346`, `cmj/loa/views/v_emendaloa.py:581`.
- LOA-LST-085 [implementado] Para o anônimo, `?pdf` devolve a página de verificação reCAPTCHA
  (`crud/gate.html`) em vez do PDF. Ela envia um POST ao mesmo endereço, com os filtros na query
  string; com a verificação aceita, o PDF é gerado com esses filtros, e com a verificação recusada a
  página volta com a mensagem de erro. Usuário logado recebe o PDF direto. O botão "Gerar PDF" do
  v2018 envia o formulário por GET, então o anônimo abre essa página na nova aba (LOA-LST-071). Evidência:
  `cmj/loa/views/v_emendaloa.py:162-184`, `cmj/mixins.py:517-615`. Testes:
  `test_anonimo_recebe_gate_em_vez_do_pdf`, `test_anonimo_com_recaptcha_invalido_volta_ao_gate`,
  `test_anonimo_com_recaptcha_valido_recebe_pdf_com_os_filtros`,
  `test_usuario_logado_gera_pdf_sem_gate`; no banco de dev, `?pdf&fase=40` na LOA 2026 deu a página
  de verificação ao anônimo e o PDF ao usuário logado (executado).
- LOA-LST-086 [implementado] Os PDFs da LOA (listagem, emenda e agrupamento na API) e os demais PDFs
  do projeto resolvem os endereços relativos do HTML com o caminho da página no domínio de
  `settings.BASE_URL`, nunca com o `Host` da requisição. A exceção são os três relatórios de
  `sapl/relatorios/views_old.py`, que em DEBUG usam `MEDIA_ROOT`. Evidência:
  `cmj/utils/utils_report.py:21-27`, `cmj/loa/views/v_emendaloa.py:427`,
  `cmj/api/loa/views/emendaloa.py:254`, `cmj/api/loa/views/agrupamento.py:149`; fora da LOA,
  `cmj/utils/utils_report.py:33` (`render_pdf_to_response`), `cmj/mixins.py:690`, `cmj/mixins.py:988`,
  `sapl/relatorios/view_reports/mixins.py:22`, `sapl/relatorios/views_old.py:1379`,
  `sapl/relatorios/views_old.py:1410`, `sapl/relatorios/views_old.py:1498`, `cmj/core/views.py:792`.
  Testes: `test_pdf_base_url_usa_base_url_e_mantem_o_caminho`,
  `test_pdf_da_listagem_ignora_o_host_da_requisicao`,
  `test_pdf_da_emenda_na_api_ignora_o_host_da_requisicao`,
  `test_pdf_do_agrupamento_na_api_ignora_o_host_da_requisicao`; no banco de dev, o PDF de
  `?pdf&fase=40` da LOA 2026 com `Host` forjado saiu com a imagem do cabeçalho (executado). Fora da
  LOA, `cmj/utils/tests/test_utils_report.py` cobre `render_pdf_to_response`, `PdfOutputMixin`,
  `MultiFormatOutputMixin` e `RelatorioMixin`; a certidão de publicação e os relatórios de
  `views_old` não têm teste.
- LOA-LST-045 [observado] O PDF é feito com WeasyPrint a partir de `loa/pdf/emendaloa_list.html`. A
  imagem de cabeçalho vem de `webpack_static '/img/pdf_cabec.jpg'` e o estilo de três arquivos de
  `_templates/v2018/css/` incluídos no HTML. Evidência: `cmj/loa/views/v_emendaloa.py:448-456`,
  `cmj/utils/utils_report.py:33-49`, `_templates/v2018/loa/pdf/emendaloa_list.html:9-30`; PDF gerado
  com a imagem de cabeçalho e com o CSS aninhado de `emendaloa-list.css` aplicado (executado).
- LOA-LST-046 [implementado] Qualquer erro ao gerar o PDF, da montagem dos dados ao WeasyPrint, vai
  para o log com a causa, a LOA e a query string, e o usuário volta para a tela da listagem com os
  filtros e a mensagem "Não foi possível gerar o PDF com esses filtros e totalizações.". Evidência:
  `cmj/loa/views/v_emendaloa.py:425-456`. Teste:
  `test_erro_no_pdf_volta_para_a_tela_com_aviso_e_registra_a_causa`; na LOA 2026, um `FieldError`
  voltou para a tela com a mensagem e registrou a causa (executado, com uma combinação que hoje a
  LOA-LST-088 recusa antes).
- LOA-LST-047 [implementado] O título é "Listagem Geral das Emendas". Abaixo dele, "FILTROS
  APLICADOS" lista todo filtro que muda o conteúdo: parlamentares, busca por termos, tipos, fases,
  entidade (pelo nome fantasia), unidade orçamentária ("código - especificação"), autoria (só quando
  é "Individual" ou "Coletiva") e `indicacao` (quando vem pela URL). Os textos entram escapados
  (LOA-LST-049). Evidência: `cmj/loa/views/v_emendaloa.py:471-517`. Testes:
  `test_pdf_informa_entidade_unidade_autoria_e_indicacao`, `test_pdf_nao_informa_autoria_ambas`; com
  `fase=40&autoria=individual`, entidade e unidade na LOA 2026, o PDF informou os quatro filtros
  (executado).
- LOA-LST-048 [observado] Cada linha de emenda mostra: epígrafe curta da matéria ou "Emenda em
  Elaboração", com link para o detalhe; tipo; autoria; indicação; e a finalidade formatada. O valor é
  o valor original da emenda (`str_valor`). O rodapé informa que o relatório não contempla os
  Registros de Ajuste Técnico. Evidência: `cmj/loa/views/v_emendaloa.py:529-578`,
  `cmj/loa/views/v_emendaloa.py:613`, `cmj/loa/views/v_emendaloa.py:836`,
  `_templates/v2018/loa/pdf/emendaloa_list.html:122-131`.
- LOA-LST-089 [implementado] O PDF mostra o valor original mesmo da emenda cujo valor final é zero
  (LOA-FASE-061 e LOA-FASE-044), mas sinaliza a linha dela, logo abaixo da autoria: "Possui ajuste
  técnico, não contemplado neste relatório." quando há ajuste técnico, ou "Em impedimento técnico."
  na fase 40 sem ajuste. Os totais não mudam. Vale com e sem totalização. Evidência:
  `cmj/loa/views/v_emendaloa.py:555-563`, `cmj/loa/views/v_emendaloa.py:581-585`,
  `_templates/v2018/css/emendaloa-list.css:65-69`. Teste:
  `test_pdf_sinaliza_ajuste_e_impedimento_tecnico_e_mantem_valor_original`; na LOA 2026, as 9
  emendas com ajuste de um parlamentar nas fases 40 e 50 saíram com o aviso de ajuste e total de
  688.738,50, igual à soma no banco, e as 7 da fase 40 com o de impedimento (executado).
- LOA-LST-049 [implementado] Todo texto que vem da URL ou do banco entra escapado no HTML do PDF:
  filtros aplicados, epígrafe, tipo, autoria, indicação, finalidade, títulos dos grupos e registros
  contábeis. Marcação HTML nesses textos sai como texto no PDF. Evidência:
  `cmj/loa/views/v_emendaloa.py:473-514`, `cmj/loa/views/v_emendaloa.py:529-578`,
  `cmj/loa/views/v_emendaloa.py:779-791`, `cmj/loa/views/v_emendaloa.py:843`. Testes:
  `test_pdf_anonimo_escapa_a_busca_por_termos`, `test_pdf_escapa_indicacao_e_finalidade_da_emenda`,
  `test_pdf_agrupado_escapa_titulo_do_grupo`.
- LOA-LST-082 [implementado] O HTML de todo PDF gerado pelo projeto com WeasyPrint só busca
  recursos por `http`, `https` e `data:`; recurso com outro protocolo, como `file:`, é ignorado.
  Vale para `make_pdf`, `render_pdf_to_response` (PDFs de matéria, norma, protocolo e cerimonial) e a
  certidão de publicação. A geração do PDF de texto articulado em `sapl/materia/models.py` também tem
  a restrição, mas fica num trecho que hoje não executa (depois de um `continue`). Evidência:
  `cmj/utils/utils_report.py:14-18`, `cmj/utils/utils_report.py:30-36`,
  `cmj/utils/utils_report.py:55-78`, `cmj/core/views.py:796-801`,
  `sapl/materia/models.py:1150-1156`. Testes: `test_make_pdf_nao_busca_arquivo_local`,
  `test_make_pdf_continua_aceitando_data_uri`,
  `test_render_pdf_to_response_nao_busca_arquivo_local`,
  `test_certidao_de_publicacao_nao_busca_arquivo_local`.
- LOA-LST-050 [observado] Sem emenda no resultado e sem totalização, o PDF mostra "Nenhuma Emenda
  encontrada a partir dos filtros aplicados.". Evidência: `cmj/loa/views/v_emendaloa.py:591-592`,
  `_templates/v2018/loa/pdf/emendaloa_list.html:139-143`; PDF de
  `?fase=25&finalidade=termoinexistentexyz` na LOA 2026 (executado).
- LOA-LST-080 [implementado] Nesse caso o título sai "Listagem Geral das Emendas", sem marcador: o
  `{}` do título é limpo antes do retorno do resultado vazio. Evidência:
  `cmj/loa/views/v_emendaloa.py:471`, `cmj/loa/views/v_emendaloa.py:587-592`. Teste:
  `test_pdf_sem_resultado_tem_titulo_sem_marcador`; texto extraído do PDF de
  `?fase=25&finalidade=termoinexistentexyz` na LOA 2026 (executado).
- LOA-LST-081 [implementado] Na finalidade exibida no cartão, no PDF e na API, os marcadores
  `{bairro}`, `{entidade}` e `{entidade__nome_fantasia}` são trocados pelo valor correspondente da
  emenda, em maiúsculas; qualquer outro marcador sai vazio. São os marcadores do texto de ajuda do
  campo. Evidência: `cmj/loa/models/m_emendaloa.py:71-73`, `cmj/loa/models/m_emendaloa.py:567-625`,
  `cmj/loa/forms/f_emendaloa.py:131`. Testes: `test_finalidade_ignora_marcador_fora_da_lista`,
  `test_finalidade_substitui_marcadores_permitidos`.

#### Sem totalização

- LOA-LST-051 [observado] Sem `agrupamento`, o PDF tem uma tabela única com as colunas "Emendas" e
  "Valores", ordenada pelo número da matéria, com "Soma das Emendas" e "Total" iguais à soma de
  `valor` das emendas filtradas. Evidência: `cmj/loa/views/v_emendaloa.py:581-628`,
  `cmj/loa/views/v_emendaloa.py:932`, `_templates/v2018/loa/pdf/emendaloa_list.html:66-81`,
  `_templates/v2018/loa/pdf/emendaloa_list.html:104-108`; 7 emendas da fase 40, total 108.369,25,
  igual à soma no banco (executado).

#### Com totalização

- LOA-LST-052 [observado] "Totalizar listagem por" aceita órgão, unidade orçamentária, função,
  subfunção, programa, ação, natureza, fonte e entidade, em qualquer combinação. "Via de
  Totalização" aceita dotações de inserção, dotações de dedução e valor da emenda (`sem_registro`).
  Evidência: `cmj/loa/forms/f_emendaloa.py:736-769`.
- LOA-LST-088 [implementado] O servidor recusa as combinações que a tela não permite (LOA-LST-070):
  totalização sem via ("Escolha a via de totalização.", no campo da via), entidade na via de
  inserção ou de dedução ("Entidades só podem ser totalizadas na via do valor da emenda.") e, na via
  do valor da emenda, dimensão diferente de unidade e entidade ("Na via do valor da emenda só é
  possível totalizar por unidades orçamentárias e por entidades."), as duas no campo de
  totalização. Como na LOA-LST-025, o erro aparece no campo, a lista segue com os demais filtros e,
  com `?pdf`, o PDF não é gerado e a tela mostra o aviso de filtros inválidos. Via sem totalização
  não é erro. Evidência: `cmj/loa/forms/f_emendaloa.py:832-869`,
  `cmj/loa/views/v_emendaloa.py:335-345`. Testes:
  `test_pdf_com_totalizacao_invalida_mostra_a_tela_com_erro_no_campo`,
  `test_totalizacao_valida_nao_tem_erro`; na LOA 2026, com `?pdf&fase=40`, as três combinações
  voltaram para a tela com o erro no campo e as 7 emendas, e unidade na via de inserção gerou o PDF
  (executado).
- LOA-LST-053 [observado] O subtítulo do PDF diz "Via dotações de inserção", "Via dotações de
  dedução" ou, na via do valor da emenda, "Via Entidades / Unidade Orçamentária". Evidência:
  `cmj/loa/views/v_emendaloa.py:663-671`.
- LOA-LST-054 [observado] Nas vias de inserção e de dedução, os grupos vêm dos registros contábeis
  das emendas filtradas com valor positivo (inserção) ou negativo (dedução), agrupados por código e
  especificação de cada dimensão escolhida. A emenda aparece em todos os grupos em que tem registro.
  Evidência: `cmj/loa/views/v_emendaloa.py:631-646`, `cmj/loa/views/v_emendaloa.py:675-713`.
- LOA-LST-055 [implementado] Nessas vias, cada registro contábil soma o seu valor em "Soma do
  Agrupamento", e cada emenda listada no grupo soma o seu valor uma única vez em "Soma das Emendas do
  Agrupamento", mesmo que tenha mais de um registro nele. Evidência:
  `cmj/loa/views/v_emendaloa.py:704-713`, `cmj/loa/models/m_registrocontabil.py:70-75`. Teste:
  `test_emenda_com_dois_registros_no_grupo_entra_uma_vez_na_soma_das_emendas`; LOA 2026,
  `fase=50&parlamentares=177&tipo=10`, inserção por unidade: as três emendas, uma delas (368) com
  dois registros na unidade 23, saíram com "Soma das Emendas do Agrupamento" de 582.869,25, igual à
  soma dos valores delas (executado).
- LOA-LST-056 [observado] Na via `sem_registro` só unidade orçamentária e entidade são consideradas:
  a chave do grupo usa código e especificação da unidade da emenda e, para entidade, CNPJ (ou
  CNES quando o CNPJ é vazio ou só zeros) e nome fantasia. As demais dimensões são recusadas
  antes (LOA-LST-088). Evidência: `cmj/loa/views/v_emendaloa.py:715-757`.
- LOA-LST-057 [implementado] Na via `sem_registro`, a emenda sem unidade ou sem entidade entra num
  grupo em que essa dimensão fica vazia, e o título mostra "Sem unidade orçamentária" ou "Sem
  entidade" no lugar dela. Nenhuma emenda fica fora do PDF nem do total. Nas outras vias, registro
  sem o código de uma dimensão também aparece como "Sem <dimensão>". Evidência:
  `cmj/loa/views/v_emendaloa.py:75-86`, `cmj/loa/views/v_emendaloa.py:715-757`,
  `cmj/loa/views/v_emendaloa.py:768-777`. Testes:
  `test_emenda_sem_unidade_vai_para_grupo_sem_unidade_no_fim`,
  `test_emenda_sem_entidade_aparece_no_pdf_totalizado_so_por_entidade`; na LOA 2023, fase 99 por
  unidade, o PDF saiu com as 58 emendas e o grupo "Sem unidade orçamentária" no fim; na LOA 2026,
  fase 40 só por entidade, com as 7 emendas, total de 108.369,25 e o grupo "Sem entidade" no fim
  (executado).
- LOA-LST-058 [implementado] Os grupos com alguma dimensão vazia vão para o fim. Dentro de cada
  bloco, a ordem é pela chave invertida (do último elemento para o primeiro), ou seja, pela
  especificação da última dimensão e não pelo código. Evidência: `cmj/loa/views/v_emendaloa.py:759-766`;
  unidades saíram na ordem 15, 03, 16 (executado). Teste: `test_grupo_com_dimensao_vazia_vai_para_o_fim`.
- LOA-LST-059 [observado] O título do grupo tem uma linha por dimensão, "código - especificação", com
  os códigos alinhados à direita. Dentro do grupo as emendas são ordenadas pelo número da matéria, e
  as sem matéria vêm primeiro. Evidência: `cmj/loa/views/v_emendaloa.py:769-793`,
  `cmj/loa/views/v_emendaloa.py:807-816`.
- LOA-LST-060 [implementado] Em toda listagem totalizada, cada emenda traz abaixo da descrição todos
  os seus registros contábeis ("DOTAÇÕES ORÇAMENTÁRIAS DE ORIGEM(-) E DESTINO(+)"), ordenados por
  valor e com sinal `+` nos positivos, e não só os do grupo: quem lê vê de onde sai e para onde vai o
  recurso. Os valores são alinhados à direita pela largura do maior valor da emenda, com espaços
  depois de `R$`; texto sem espaço é alinhado inteiro, sem depender do formato do `__str__` do
  registro. Evidência: `cmj/loa/views/v_emendaloa.py:49-56`, `cmj/loa/views/v_emendaloa.py:838-861`.
  Testes: `test_emenda_lista_todos_os_seus_registros_nao_so_os_do_grupo`,
  `test_alinhar_valor_da_o_mesmo_texto_do_alinhamento_antigo`,
  `test_alinhar_valor_sem_espaco_alinha_o_texto_inteiro`; na LOA 2026, o HTML de três PDFs
  totalizados (inserção, dedução e valor da emenda, 47 registros) saiu idêntico ao do alinhamento
  anterior (executado).
- LOA-LST-061 [implementado] Nas vias de inserção e de dedução, cada grupo mostra "Orçamento
  Original" (soma de `valor_materia` das despesas da LOA no grupo), "Movimentação Geral" (soma dos
  registros contábeis de todas as emendas da LOA no grupo, sem os filtros da tela) e "Saldo" (a soma
  dos dois), com nota de rodapé explicando que não seguem os filtros. Na via do valor da emenda esses
  valores não são exibidos nem calculados. Evidência: `cmj/loa/views/v_emendaloa.py:863-905`,
  `_templates/v2018/loa/pdf/emendaloa_list.html:44-48`,
  `_templates/v2018/loa/pdf/emendaloa_list.html:90-103`. Teste:
  `test_orcamento_do_grupo_so_e_calculado_nas_vias_com_registro`; na LOA 2026, fase 40 por unidade,
  a via do valor da emenda não fez nenhuma dessas consultas e a de inserção fez 6, duas por grupo,
  com o mesmo total de 108.369,25 (executado).
- LOA-LST-062 [implementado] Com totalização, o "Total" final é a soma dos valores das emendas
  listadas no PDF, cada uma uma única vez, mesmo que apareça em mais de um grupo, e é positivo em
  todas as vias. É o que diz o texto do PDF: "a soma das emendas listadas acima uma única vez, mesmo
  que apareça em mais de um agrupamento". Emendas sem registro contábil não aparecem nas vias de
  inserção e de dedução, e por isso também não entram no total delas. Evidência:
  `cmj/loa/views/v_emendaloa.py:768`, `cmj/loa/views/v_emendaloa.py:817-823`,
  `cmj/loa/views/v_emendaloa.py:932`, `_templates/v2018/loa/pdf/emendaloa_list.html:107-120`. Teste:
  `test_total_soma_cada_emenda_uma_vez_e_e_positivo`; fase 40 da LOA 2026 por unidade: total de
  108.369,25 nas três vias, igual à soma das emendas (executado). Na base de dev, em todas as emendas
  com registro, as inserções somam o valor da emenda e as deduções somam o valor negativo.
- LOA-LST-063 [observado] Com "Quebrar página a cada mudança de agrupamento", cada grupo começa em
  página nova. Evidência: `cmj/loa/views/v_emendaloa.py:526`,
  `_templates/v2018/loa/pdf/emendaloa_list.html:133-137`, `_templates/v2018/css/emendaloa-list.css:33-35`;
  três grupos em três páginas (executado).

### Dependências do `_frontend/v2018`

- LOA-LST-064 [observado] A tela carrega o bundle `loa` (CSS e JS) porque `EmendaLoaCrud.frontend` é
  `"loa"`. O bundle tem entrada em `src/__apps/loa/main.js`. Evidência:
  `cmj/loa/views/v_emendaloa.py:92`, `_templates/v2018/crud/list.html:5-16`,
  `_frontend/v2018/vue.config.js:67-68`.
- LOA-LST-065 [observado] O JavaScript da listagem só é ativado se o contêiner da página tiver as
  classes `container-loa` e `emendaloa-list`, que vêm da variável de contexto `path`. Evidência:
  `cmj/loa/views/v_mixins.py:8-9`, `cmj/loa/views/v_emendaloa.py:947-948`,
  `_templates/v2018/base.html:67`, `_frontend/v2018/src/__apps/loa/main.js:13-17`,
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaCRUD.js:7-14`; a página veio com
  `class="container emendaloa-list container container-loa container-box"` (executado).
- LOA-LST-066 [implementado] O botão de envio padrão do formulário (`salvar`, rótulo "Filtrar") é
  escondido por CSS, e a tecla Enter não envia o formulário. O filtro é aplicado pelo botão
  "Filtrar" ao lado da busca por termos, que é `type="button"` com a classe `btn-filtrar`: o script
  liga o clique só a ele, e os botões criados pelo `bootstrap-select` não interferem. Enter no campo
  "Busca por termos" também aplica o filtro; nos demais campos, não faz nada. Marcar ou desmarcar
  opções não reenvia a tela. Evidência: `_frontend/v2018/src/__apps/loa/scss/loa.scss:97-99`,
  `sapl/crispy_layout_mixin.py:51-74`, `cmj/loa/forms/f_emendaloa.py:999-1005`,
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaList.js:15-18`, `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaList.js:65-79`. Teste:
  `test_formulario_tem_um_unico_botao_filtrar_para_o_script`, que cobre só a marcação do servidor; o
  script não foi executado (sem navegador) e só chega à produção com o rebuild do `dist/`
  (LOA-LST-078). Na LOA 2026, o HTML tem um único `button.btn-filtrar` e os submits `pdf` e
  `salvar` (executado).
- LOA-LST-067 [acordado] O filtro não é lembrado entre visitas: fica só na URL, e a tela aberta sem
  parâmetros mostra todas as emendas. Ao abrir a tela, o script apaga do `localStorage` a chave
  `portalcmj_emendaloa_filter`, usada por versões anteriores para guardar e reaplicar o filtro.
  Substitui as antigas LOA-LST-068 e 069. Evidência:
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaList.js:8-13`. Sem teste automatizado: o v2018
  não tem testes, e o script não foi executado (sem navegador); a mudança só chega à produção com o
  rebuild do `dist/` (LOA-LST-078).
- LOA-LST-068 [retirada] Substituída por LOA-LST-067.
- LOA-LST-069 [retirada] Substituída por LOA-LST-067.
- LOA-LST-070 [observado] As opções do PDF são ajustadas no navegador; o servidor só recusa as
  combinações inválidas, sem ajustá-las (LOA-LST-088). Sem nenhuma
  totalização marcada, a via passa a `sem_registro`. Na via `sem_registro` só unidade e entidade
  ficam visíveis e habilitadas, e unidade é marcada. Nas outras vias, entidade é escondida,
  desabilitada e desmarcada e, se nada estiver marcado, a segunda opção (unidade) é marcada. Como
  isso roda na abertura, a tela sempre parte de `sem_registro` com unidade marcada. Evidência:
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaList.js:20-48`; o servidor só envia marcado
  `autoria=ambas` (executado).
- LOA-LST-071 [implementado] "Gerar PDF" abre em nova aba (`formtarget="_blank"`) e envia o estado
  atual de todos os campos, inclusive filtros alterados e ainda não aplicados com "Filtrar": o PDF
  reflete o que está marcado no formulário no momento do clique. A listagem fica como estava, sem
  mensagem de carregamento. O que a view devolver no lugar do PDF (verificação reCAPTCHA, tela com
  filtro inválido ou com erro na geração) também aparece na nova aba. Evidência:
  `cmj/loa/forms/f_emendaloa.py:1051-1060`. Teste: `test_gerar_pdf_abre_em_nova_aba`, que cobre a
  marcação do servidor; na LOA 2026, o botão saiu com `formtarget="_blank"` (executado). O script
  não foi executado (sem navegador), e a remoção da mensagem só chega à produção com o rebuild do
  `dist/` (LOA-LST-078).
- LOA-LST-072 [observado] A seleção de parlamentar é visual: o script alterna a classe `active` na
  foto ao marcar o checkbox, que fica escondido. Evidência:
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaList.js:50-62`,
  `_frontend/v2018/src/__apps/loa/scss/loa.scss:97-99`. A foto do parlamentar que já vem marcado
  na URL é destacada pelo servidor (`cmj/loa/forms/f_emendaloa.py:887-940`).
- LOA-LST-073 [observado] O script depende de nomes e marcação gerados pelo backend: `name` dos
  campos `agrupamento`, `tipo_agrupamento` e `finalidade`, os valores `sem_registro`,
  `despesa__unidade` e `entidade`, o id `div_id_parlamentares`, a classe `btn-filtrar` dentro do
  formulário e a ordem das opções de `agrupamento` (a segunda é unidade). Evidência:
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaList.js:20-79`,
  `cmj/loa/forms/f_emendaloa.py:739-751`.
- LOA-LST-074 [observado] Os seletores de entidade e unidade usam `bootstrap-select`, iniciado pelo
  bundle global 500 ms depois do carregamento. Como o clique de "Filtrar" é ligado pela classe
  `btn-filtrar` (LOA-LST-066), a ordem entre essa inicialização e o script da listagem não importa.
  Evidência: `_frontend/v2018/src/__globals/js/index.js:17-23`,
  `_frontend/v2018/src/__globals/js/functions.js:20-30`, `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaList.js:65-69`.
- LOA-LST-075 [observado] O estilo da tela está em `loa.scss`, sob `.container-loa.emendaloa-list`:
  formulário, bloco do PDF (`.relatorio-select`), fotos (`.container-avatar`, `.avatar`), cartão
  (`.emendaloa-item`, `.btn-expand`, `.emenda-card`) e ajustes para telas estreitas. Evidência:
  `_frontend/v2018/src/__apps/loa/scss/loa.scss:68-305`,
  `_frontend/v2018/src/__apps/loa/scss/loa.scss:565-607`.
- LOA-LST-076 [observado] As abas do cartão usam `data-toggle="tab"` do Bootstrap carregado pelo
  bundle global; a confirmação do registro e a tela cheia são scripts do próprio template, que usam
  o `$` global. Evidência: `_templates/v2018/loa/emendaloa_filter_cache.html:125-178`,
  `_templates/v2018/loa/emendaloa_filter.html:76-113`.
- LOA-LST-077 [observado] A imagem de cabeçalho do PDF é um arquivo do v2018
  (`src/assets/img/pdf_cabec.jpg`), resolvido por `webpack_static` e buscado por HTTP pelo WeasyPrint.
  O CSS do PDF não vem do bundle. Evidência: `_templates/v2018/loa/pdf/emendaloa_list.html:10-12`,
  `_templates/v2018/loa/pdf/emendaloa_list.html:29`.
- LOA-LST-078 [observado] Mudanças no JavaScript ou no SCSS da listagem só chegam à produção depois do
  rebuild do `dist/` do v2018, que é versionado e feito à parte. Evidência: `CLAUDE.md` (seção
  "Armadilhas do legado").
  Evidência: `CLAUDE.md:170-171`, `_frontend/v2018/vue.config.js:22-23`,
  `cmj/settings/frontend.py:111-117`.

## Riscos de segurança

Varredura dos itens 1 a 7 da skill `spec-legado` em 2026-11-20, sobre as rotas desta tela (lista,
`?pdf`, `?zip` e registro), o cartão em cache e o que elas alcançam. Nada foi gravado nem enviado
para fora da máquina.

Nenhum risco aberto. Item 2: a tela não chama a API (o v2018 não guarda dados da tela). Item 4: os
parâmetros de agrupamento passam por `choices` antes de chegar ao ORM
(`cmj/loa/forms/f_emendaloa.py:736-769`) e não há SQL cru, `subprocess` nem template montado com
texto do usuário.

## Dúvidas

D21 é pendência adiada, que envolve mais do que esta tela; as demais estão resolvidas.

- D2. Resolvida em 2026-11-20: LOA-LST-005, LOA-LST-006 e LOA-LST-083.
- D3. Resolvida em 2026-11-20: LOA-LST-055.
- D4. Resolvida em 2026-11-20: LOA-LST-062.
- D5. Resolvida em 2026-11-20: LOA-LST-047.
- D6. Resolvida em 2026-11-20: LOA-LST-057 e LOA-LST-058.
- D7. Resolvida em 2026-11-20: LOA-LST-040 e LOA-LST-041.
- D8. Resolvida em 2026-11-20: LOA-LST-040.
- D9. Resolvida em 2026-11-20: LOA-LST-024, LOA-LST-025 e LOA-LST-087.
- D10. Resolvida em 2026-11-20: LOA-LST-046.
- D11. Resolvida em 2026-11-20: LOA-LST-085.
- D12. Resolvida em 2026-11-20: LOA-LST-088.
- D13. Resolvida em 2026-11-20: LOA-LST-060 e LOA-LST-061.
- D14. Resolvida em 2026-11-20: LOA-LST-089.
- D15. Resolvida em 2026-11-20: LOA-LST-015 e LOA-LST-017.
- D16. Resolvida em 2026-11-20: LOA-LST-019.
- D17. Resolvida em 2026-11-20: LOA-LST-067.
- D18. Resolvida em 2026-11-20: LOA-LST-066 e LOA-LST-074.
- D19. Resolvida em 2026-11-20: LOA-LST-071.
- D20. Resolvida em 2026-11-20: mantido como está (LOA-LST-028 e LOA-LST-029).
- D21. Pendência, adiada em 2026-11-20: envolve mais do que esta tela e não será resolvida agora.
  O filtro `indicacao` existe só pela URL e exige texto idêntico (LOA-LST-031). Deve ser
  removido ou ganhar campo na tela? Se for removido, sai também da LOA-LST-047.
- D22. Resolvida em 2026-11-20: LOA-LST-039.
- D23. Resolvida em 2026-11-20: LOA-LST-003, LOA-LST-005 e LOA-LST-006.
- D24. Resolvida por verificação em 2026-11-20: o CSS aninhado de `emendaloa-list.css` é aplicado pelo
  WeasyPrint 70 (as epígrafes saíram em Courier New negrito no PDF gerado). Nada a decidir.
- D25. Resolvida em 2026-11-20: LOA-LST-080.
- D32. Resolvida em 2026-11-20: LOA-LST-060.

## Fora do escopo

- Criação, edição e detalhe da emenda: `docs/specs/loa/edicao-emenda.md`.
- Fases, transições e permissões por fase: `docs/specs/loa/fases-emenda.md`.
- Agrupamentos e emendas coletivas: `docs/specs/loa/edicao-agrupamento.md`.
- O que a task de registro de proposições faz depois de disparada pelo registro, e o conteúdo do
  PDF individual da emenda (`/api/loa/emendaloa/<id>/view/`).
- A API `/api/loa/emendaloa/` e seu filterset (`cmj/api/forms.py`).
- As telas de totalização por unidade e por entidade do resumo da LOA (`cmj/loa/views/v_loa.py`), que
  só entram aqui como origem de links.
- O frontend v6, que não participa desta tela.
