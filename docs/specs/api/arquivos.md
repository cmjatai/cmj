# API: arquivos servidos pelas actions e formatos de resposta

Status: observado, com API-ARQ-020, 021, 022, 024, 025, 027, 029, 031 e 032 implementadas
(acordadas em 2026-11-22, com teste) e API-ARQ-012, 026 e 028 acordadas
Última verificação: 2026-11-21 (commit `2452ae3d8`)
Código principal: `sapl/api/mixins.py` (`ResponseFileMixin`,
`ControlAccessFileForContainerMixin`), `drfautoapi/__init__.py` (negociação e renderers),
`cmj/settings/drf.py`, `sapl/api/views_protocoloadm.py`, `docker/nginx/cmj_docker.conf`
Testes: `sapl/api/tests/test_api_arquivos.py`

Como a API entrega os arquivos dos models (PDF, imagem), as conversões que faz a pedido do cliente
(página de PDF em imagem, texto do PDF, miniatura) e como o formato da resposta é escolhido.

As regras `[observado]` descrevem o que o código faz hoje e não foram confirmadas como regra
desejada; as `[implementado]` foram acordadas e têm teste. As marcadas com "(executado)" foram conferidas em 2026-11-21 no ambiente de
desenvolvimento, como anônimo, com `django.test.Client` nas rotas reais e a sessão do banco em
somente leitura. Os caminhos que gravam no disco não foram executados: a conversão de página com
cache, o parâmetro `nocache`, as miniaturas e a anonimização foram só lidos. O custo de renderizar
uma página foi medido chamando a mesma função da biblioteca fora da rota, sem gravar.

## Escopo

`ResponseFileMixin.response_file` e seus auxiliares, as 21 actions que o usam, os renderers extras
e a negociação de formato. O controle de acesso por área de trabalho está em
[acesso.md](./acesso.md) (`API-ACS`), e aqui entra só no que decide a entrega de um arquivo.

## Regras

### Formato da resposta

- API-ARQ-001 [observado] As settings declaram cinco renderers: JSON e quatro de arquivo (PDF,
  PNG, JPG e JPEG). Os de arquivo não renderizam dado nenhum: uma resposta de dados pedida com
  sufixo de arquivo responde 404, e só a resposta de erro passa por eles (API-ARQ-031). Não há
  renderer de API navegável. Evidência: `cmj/settings/drf.py:9-15`, `drfautoapi/__init__.py:21-47`.
- API-ARQ-002 [retirada] Substituída por API-ARQ-032.
- API-ARQ-032 [implementado] O formato pedido (sufixo `.<formato>` na URL ou parâmetro `format`)
  tem de casar por inteiro com o do renderer; sem renderer compatível, a resposta é 404. Numa rota
  de dados, `json` devolve JSON, e `jsonx`, `js`, `yaml` e `xml` respondem 404. Evidência:
  `drfautoapi/__init__.py:8-18`.
- API-ARQ-003 [observado] (executado) Numa rota de dados, `format=pdf` e `format=png` respondem
  404, assim como `Accept: image/png` e `Accept: application/x-yaml`. Evidência:
  `drfautoapi/__init__.py:13-17`, `drfautoapi/__init__.py:26-31`.
- API-ARQ-004 [observado] Os renderers de imagem aceitam um prefixo alfanumérico antes da
  extensão (`c128.png`, `300.jpg`); é esse prefixo que pede a miniatura (API-ARQ-016). Evidência:
  `drfautoapi/__init__.py:34-46`.
- API-ARQ-005 [observado] As actions de arquivo devolvem um `HttpResponse` pronto, que não passa
  pelos renderers: os renderers de arquivo existem para a URL com sufixo ser aceita. (executado) Um
  PDF pedido com sufixo `.abc.png` é entregue como `application/pdf`. Evidência:
  `sapl/api/mixins.py:394-418`.
- API-ARQ-030 [retirada] Substituída por API-ARQ-031.
- API-ARQ-031 [implementado] Numa URL com sufixo de arquivo, a resposta de erro de uma action chega
  em JSON, com o status dela: 401 para a página além da primeira sem autenticação (API-ARQ-027),
  403 para o arquivo original pedido por quem não é superusuário (API-ARQ-011), 400 para valor
  inválido (API-ARQ-029) e 404 para registro que não existe. Evidência:
  `drfautoapi/__init__.py:21-31`, `sapl/api/mixins.py:280-286`.

### Entrega do arquivo

- API-ARQ-006 [observado] Uma action de arquivo tem o nome do campo do model e só chama
  `response_file`, que lê o campo com esse nome. (executado, inventário) São 21 actions: 16 em
  rotas que anônimo alcança (texto de matéria, proposição e norma; anexos de norma; documentos
  acessórios; ata, pauta e anexo de sessão; diário oficial; três da LOA; documentos
  administrativos; fotografia de parlamentar e de indivíduo de painel) e 5 em rotas restritas.
  Evidência: `sapl/api/mixins.py:333-340`, `sapl/api/views_materia.py:149-151`.
- API-ARQ-007 [observado] O registro é buscado em `get_queryset()` filtrado pelo id, sem
  `get_object` e sem os filtros da requisição. O mixin não confere permissão: quem decide o acesso
  é a permissão e o `get_queryset` do viewset. Evidência: `sapl/api/mixins.py:33-37`,
  `sapl/api/mixins.py:290`.
- API-ARQ-008 [observado] Sem registro, sem o campo ou com o campo vazio, a resposta é 404.
  Evidência: `sapl/api/mixins.py:329-340`.
- API-ARQ-009 [observado] Em produção a resposta não leva o conteúdo: leva o cabeçalho
  `X-Accel-Redirect` para `/mediaredirect/<caminho do arquivo>`, e o nginx entrega o arquivo por
  uma localização interna. Com `DEBUG`, o Django lê e devolve o arquivo. Nos dois casos vai
  `Cache-Control: no-cache`. Evidência: `sapl/api/mixins.py:388-414`,
  `docker/nginx/cmj_docker.conf:73-80`.
- API-ARQ-010 [observado] O nome do arquivo na resposta vem de `custom_filename` do viewset,
  quando existe, ou do nome gravado. Evidência: `sapl/api/mixins.py:372-374`,
  `sapl/api/views_materia.py:139-147`.
- API-ARQ-011 [observado] O parâmetro `original` pede o arquivo original guardado ao lado
  (`original__`); só superusuário recebe, e os demais recebem 403 (executado). Evidência:
  `sapl/api/mixins.py:380-386`.
- API-ARQ-012 [acordado] Cada entrega é registrada no log `XAccelRedirect` com o IP, o id do
  usuário, o arquivo, o navegador e a página de origem. O log vai para a saída do processo e para
  `logs/x_accel_redirect.log`, com guarda por tamanho (15 MB por arquivo e dez cópias antigas),
  no volume de logs do servidor, junto dos logs de acesso; quem o lê é quem administra o
  servidor. Mantido assim por decisão de 2026-11-22. Evidência: `sapl/api/mixins.py:433-441`,
  `cmj/settings/logs.py:79-87`, `cmj/settings/logs.py:119-123`, `docker/docker-compose.yaml:72`.

### Conversões a pedido do cliente

- API-ARQ-013 [retirada] Substituída por API-ARQ-022.
- API-ARQ-014 [observado] Em arquivo PDF, o parâmetro `page` devolve a página como PNG, na
  resolução `dpi`, ajustada a uma de cinco opções entre 72 e 300. A imagem é gravada ao lado do
  arquivo, com o nome `<arquivo>-p<página>-d<dpi>.png`. Renderizar a primeira página de um PDF de
  13 MB levou de 0,3 a 3,4 s (medido fora da rota). Evidência: `sapl/api/mixins.py:81-117`,
  `sapl/api/mixins.py:315-327`, `sapl/api/mixins.py:355-361`.
- API-ARQ-015 [retirada] Substituída por API-ARQ-021.
- API-ARQ-027 [implementado] Sem autenticação, só a primeira página de um PDF é entregue como
  imagem. Pedir outra página responde 401, sem renderizar nem gravar nada; quem está autenticado
  recebe qualquer página. Evidência: `sapl/api/mixins.py:355-361`.
- API-ARQ-028 [acordado] As imagens de página e as miniaturas são geradas a pedido de quem alcança
  o arquivo, inclusive anônimo, e ficam gravadas ao lado do arquivo original, no volume de mídia.
  O texto extraído fica no cache da aplicação (API-ARQ-022). Decisão de 2026-11-22, a rever (D4).
  Evidência: `sapl/api/mixins.py:81-117`, `sapl/api/mixins.py:443-483`.
- API-ARQ-020 [implementado] A imagem de página gravada só é reaproveitada enquanto for mais nova
  que o arquivo PDF. Se o arquivo mudou depois dela, a página é renderizada de novo e a imagem
  gravada é substituída. Evidência: `sapl/api/mixins.py:81-95`.
- API-ARQ-021 [implementado] `nocache` (renderizar de novo e apagar a imagem gravada) e `grade`
  (desenhar uma grade sobre a página, sem gravar) só valem para superusuário. Para os demais,
  inclusive anônimo, são ignorados, e a resposta vem pelo caminho normal do cache. Evidência:
  `sapl/api/mixins.py:41-44`, `sapl/api/mixins.py:304-306`.
- API-ARQ-022 [implementado] Em arquivo PDF, o parâmetro `text` devolve o texto extraído do
  documento inteiro. O texto fica no cache da aplicação por sete dias, por versão do arquivo
  (caminho, data de modificação e tamanho): só a primeira requisição de cada versão extrai.
  Evidência: `sapl/api/mixins.py:243-259`, `sapl/api/mixins.py:352-353`.
- API-ARQ-023 [observado] (executado) Num PDF de 13 MB e 33 páginas, `text` levou 14 s na primeira
  requisição e de 0,03 a 0,12 s nas seguintes, com cache em memória. Em `DEBUG` o cache é
  `DummyCache`, e o texto é extraído a cada requisição. Evidência: `sapl/api/mixins.py:254-259`.
- API-ARQ-016 [observado] Em arquivo de imagem, o sufixo `<n>.<ext>` devolve uma miniatura de até
  `n` pixels, e `c<n>.<ext>` uma miniatura recortada conforme o recorte salvo no registro. O
  tamanho é qualquer inteiro de 1 a 99.999 informado na URL, e cada tamanho novo gera um arquivo.
  O sufixo só com a extensão (`.png`) entrega o arquivo como está. Evidência:
  `sapl/api/mixins.py:376-378`, `sapl/api/mixins.py:443-483`.
- API-ARQ-017 [observado] O parâmetro `anon`, só para superusuário e só em PDF, cobre com tarjas
  os trechos de texto informados e as imagens da área indicada, e grava o resultado no lugar do
  arquivo. A alteração acontece numa requisição `GET`, nas condições de API-ARQ-025. Para quem não
  é superusuário o parâmetro é ignorado. Evidência: `sapl/api/mixins.py:121-237`,
  `sapl/api/mixins.py:344-350`.
- API-ARQ-025 [implementado] A anonimização só é executada quando a requisição é uma navegação
  direta do navegador, isto é, URL digitada ou aberta de favorito: `Sec-Fetch-Site: none`,
  `Sec-Fetch-Mode: navigate` e `Sec-Fetch-Dest: document`. Vinda de link de outra página, de imagem
  embutida, de script ou sem esses cabeçalhos, a requisição de superusuário com `anon` recebe 403 e
  o arquivo não muda. A alteração continua numa requisição `GET`, sem etapa de confirmação, e a
  proteção depende desses cabeçalhos do navegador do superusuário: aceito na decisão de
  2026-11-22. Evidência: `sapl/api/mixins.py:344-350`, `sapl/api/mixins.py:420-431`.
- API-ARQ-026 [acordado] Um erro durante a anonimização vai só para o log `XAccelRedirect`: a
  requisição segue e devolve o arquivo como se nada tivesse falhado, e o superusuário confere o
  resultado no PDF devolvido. Mantido assim por decisão de 2026-11-22, até existir uma tela de
  gerenciamento da anonimização (D9). Evidência: `sapl/api/mixins.py:239-241`.
- API-ARQ-029 [implementado] Valor inválido num pedido de conversão responde 400, em JSON com a
  mensagem em `detail`, antes de renderizar, gerar ou gravar qualquer coisa, com ou sem sufixo de
  arquivo na URL. Vale para: `page` que não é um inteiro sem sinal, em qualquer tipo de arquivo;
  `grade` de superusuário que não é um inteiro nem quatro inteiros separados por vírgula; sufixo
  de miniatura fora das formas `<n>.<ext>` e `c<n>.<ext>` com `n` de 1 a 99.999; e miniatura
  recortada (`c<n>`) de arquivo cujo registro não tem recorte. `page` e `grade` vazios contam como
  não informados, `dpi` inválido continua valendo 72 e página que o documento não tem continua
  respondendo 404. Evidência: `sapl/api/mixins.py:266-313`, `sapl/api/mixins.py:453-474`.

### Documentos administrativos

- API-ARQ-018 [observado] `protocoloadm/documentoadministrativo/<pk>/texto_integral/` entrega o
  arquivo em três situações: o documento está no queryset do usuário (área pública ou em que
  opera); o parâmetro `hash` confere com o código de compartilhamento do documento ou de um
  documento ao qual ele está anexado, e a visibilidade é "Público"; ou o documento está vinculado a
  uma matéria e sua área de trabalho é pública ou a da Procuradoria. Evidência:
  `sapl/api/views_protocoloadm.py:45-87`.
- API-ARQ-019 [retirada] Substituída por API-ARQ-024.
- API-ARQ-024 [implementado] O arquivo de um documento administrativo da área de trabalho da
  Procuradoria é público quando o documento está vinculado a uma matéria, diretamente ou por
  vínculo: é o parecer que a página pública da matéria também oferece em link. Documento da
  Procuradoria sem vínculo com matéria, e documento de outra área de trabalho não pública mesmo
  que vinculado, não são entregues por essa regra. (executado) Na base local são 1.412
  documentos, todos do tipo "Parecer de Proposições Legislativas"; o detalhe em JSON deles
  continua respondendo 404 a anônimo. Evidência: `sapl/api/views_protocoloadm.py:75-86`,
  `_templates/v2018/materia/materialegislativa_detail.html:185-195`.

## Riscos de segurança

Varredura de 2026-11-21, itens 1, 3, 5 e 7 de `docs/specs/README.md`, sobre a entrega de arquivos
pela API. Não é auditoria do controle de acesso a mídia fora da API.

Nenhum risco encontrado nos itens 1, 3, 5 e 7 (2026-11-22).

Itens sem achado: 4 (não há `subprocess` nem comando montado com entrada do usuário; o caminho do
arquivo vem do campo do model, nunca da requisição).

## Dúvidas

- D4. As imagens de página e as miniaturas continuam sendo geradas a pedido e gravadas ao lado dos
  originais (API-ARQ-028). Rever no futuro como melhorar isso: lista fechada de tamanhos de
  miniatura, cache fora do volume de mídia ou outra forma de limitar o que é gerado.
- D9. Demanda futura, registrada em 2026-11-22: criar uma interface de usuário para gerenciar a
  anonimização de PDF, no lugar dos parâmetros na URL (API-ARQ-017, 025, 026).

## Fora do escopo

- Upload de arquivos pela API e as actions de `arq/draft` e `arq/draftmidia` que convertem,
  giram e unem PDFs: são restritas e do app `arq`.
- Extração de assinaturas, OCR e os campos de arquivo dos models (`cmj/core/signals_functions.py`).
- Acesso direto a `/media/` fora da API.
