# Genia: conexão e controle de cotas

Status: implementado
Última verificação: 2026-11-19 (branch `refactor/genia`, sobre o commit `d6741e498`)
Código principal: `cmj/utils/genia/base.py`, `cmj/core/models.py` (`IAQuota`, `IAQuotasLog`)
Testes: `cmj/utils/genia/test_genia.py`

As regras `[implementado]` foram pedidas na refatoração de 2026-11-19 e têm teste. As `[observado]`
descrevem comportamento herdado, obtido por leitura do código, sem chamar a API Gemini.

## Escopo

`IAGenaiBase`: cliente da API Gemini, escolha da cota e do modelo, registro de consumo, montagem da
configuração de geração e contagem de tokens. É a classe-base de todos os serviços do pacote.

## Regras

### Responsabilidade

- GENIA-BASE-002 [implementado] A classe-base não conhece nenhuma funcionalidade: a configuração
  padrão não tem system instruction nem tools, e responde em `application/json` com temperatura 0.1,
  `top_k` 40 e `top_p` 0.95. Evidência: `cmj/utils/genia/base.py:38-44`,
  `cmj/utils/genia/base.py:92-107`.
- GENIA-BASE-014 [implementado] Cada serviço declara a própria cota: `quota_service_name` com uma
  chave de `IAQuota.ServicosAutorizados`, ou `quota_exempt = True`. O nome da classe não participa da
  autorização. Evidência: `cmj/utils/genia/chat.py:21`, `cmj/utils/genia/classificacao.py:27`,
  `cmj/utils/genia/similaridade.py:28`, `cmj/utils/genia/embeddings.py:18`,
  `cmj/utils/genia/loa_agrupamento.py:18`.

### Conexão

- GENIA-BASE-001 [implementado] Instanciar qualquer serviço sem `settings.GEMINI_API_KEY` levanta
  `ValueError`. Com a chave, cada instância cria o próprio `genai.Client`. Evidência:
  `cmj/utils/genia/base.py:46-49`.

### Seleção da cota

- GENIA-BASE-003 [implementado] Serviço sem `quota_service_name` não obtém cota:
  `retrieve_quota_if_available` levanta `IAQuotaUnavailableError`. Evidência:
  `cmj/utils/genia/base.py:63-64`.
- GENIA-BASE-004 [implementado] Só serve a cota que está ativa, tem a chave do serviço em
  `servicos_autorizados` e cuja soma de `peso` dos logs da data local de hoje é menor que
  `quota_diaria`. Sem nenhuma, levanta `IAQuotaUnavailableError`. Evidência:
  `cmj/utils/genia/base.py:66-74`, `cmj/core/models.py:1046-1066`.
- GENIA-BASE-005 [implementado] Entre as cotas que servem, `ascending=True` escolhe a de menor
  `quota_diaria` e `ascending=False`, a de maior. A escolhida define `self.ia_model_name`. Evidência:
  `cmj/core/models.py:1064-1066`, `cmj/utils/genia/base.py:76`.
- GENIA-BASE-006 [implementado] Com `ia_model_name` informado, só a cota desse modelo serve. Se ela
  não existir ou não tiver margem, levanta `IAQuotaUnavailableError`, sem recorrer a outro modelo.
  Evidência: `cmj/utils/genia/base.py:69-74`.

### Geração e consumo

- GENIA-BASE-007 [implementado] `generate_content` chama a API com o modelo da cota selecionada e,
  depois da resposta, registra um `IAQuotasLog` de peso 1. Evidência:
  `cmj/utils/genia/base.py:109-133`.
- GENIA-BASE-008 [implementado] Se a chamada à API falhar, a exceção sobe e nenhum consumo é
  registrado. Evidência: `cmj/utils/genia/base.py:125-132`.
- GENIA-BASE-009 [implementado] Sem cota disponível, a API não é chamada. Evidência:
  `cmj/utils/genia/base.py:120-123`.
- GENIA-BASE-010 [implementado] Serviço `quota_exempt` chama o modelo de `ia_model_name` sem
  consultar nem registrar `IAQuota`. Evidência: `cmj/utils/genia/base.py:117-119`.
- GENIA-BASE-011 [implementado] Com `tools`, a configuração ativa o function calling automático,
  limitado a `max_remote_calls` (10) chamadas. Parâmetro de geração com valor `None` não é enviado.
  Evidência: `cmj/utils/genia/base.py:100-107`.

### Utilidades

- GENIA-BASE-012 [implementado] `update_or_create_llm_models_in_quotamodel` cria uma `IAQuota` para
  cada modelo listado pela API (inativa, `quota_diaria` 0, sem serviços) e atualiza só a `descricao`
  das existentes. Lê apenas a primeira página da listagem. Evidência:
  `cmj/utils/genia/base.py:79-86`.
- GENIA-BASE-013 [implementado] `count_tokens_in_text` devolve 0 quando a API falha, e registra o
  erro em log. Não consome cota. Evidência: `cmj/utils/genia/base.py:135-143`.

## Dúvidas

- D1. A margem é verificada antes da chamada e o consumo é gravado depois, sem transação nem lock.
  Chamadas simultâneas podem passar todas pela verificação e ultrapassar `quota_diaria`. Isso é
  aceitável, ou a cota deve ser reservada antes da chamada?
- D2. Todo consumo tem peso 1, seja qual for o tamanho do prompt ou o uso de tools (no chat, uma
  mensagem pode gerar até 10 chamadas ao modelo). A cota deve passar a contar tokens ou chamadas?
- D3. `IAQuota.has_margin` (`cmj/core/models.py:1144`) repete a regra de `quotas_with_margin` e não é
  usado pelo pacote. Pode ser removido?
- D4. A listagem de modelos lê só `models.page`. Se a API paginar, modelos ficam de fora da
  sincronização. Deve percorrer todas as páginas?

## Fora do escopo

Tela de administração de `IAQuota` (`cmj/core/admin.py`) e as regras de cada serviço, descritas nas
demais specs desta pasta.
