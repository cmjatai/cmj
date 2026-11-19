from types import SimpleNamespace
from unittest import mock

import pytest

from cmj.core.models import IAQuota, IAQuotasLog
from cmj.utils.genia import (
    IAChatService,
    IAEmbeddingService,
    IAGenaiBase,
    IAQuotaUnavailableError,
)
from cmj.utils.genia.classificacao import IAClassificacaoMateriaService
from cmj.utils.genia.genia_system_instruction_v3 import rag_system_instruction
from cmj.utils.genia.loa_agrupamento import IAEmentaEmendaColetiva
from cmj.utils.genia.similaridade import IAAnaliseSimilaridadeService

pytestmark = pytest.mark.django_db

SERVICO = IAQuota.ServicosAutorizados.IA_CLASSIFICACAO_MATERIA_SERVICE


class ServicoComCota(IAGenaiBase):
    quota_service_name = SERVICO


@pytest.fixture(autouse=True)
def client(settings):
    settings.GEMINI_API_KEY = "chave-de-teste"
    with mock.patch("cmj.utils.genia.base.genai.Client") as client_cls:
        yield client_cls.return_value


def _quota(modelo, quota_diaria=10, servicos=(SERVICO,), ativo=True):
    return IAQuota.objects.create(
        modelo=modelo,
        quota_diaria=quota_diaria,
        ativo=ativo,
        servicos_autorizados=[str(s) for s in servicos],
    )


# ----------------------------------------------------------------------
# Conexão e cotas
# ----------------------------------------------------------------------


@pytest.mark.spec("GENIA-BASE-001")
def test_sem_api_key_nao_instancia(settings):
    settings.GEMINI_API_KEY = ""
    with pytest.raises(ValueError):
        IAGenaiBase()


@pytest.mark.spec("GENIA-BASE-002")
def test_base_nao_carrega_configuracao_de_chat():
    config = IAGenaiBase().build_generation_config()

    assert config.system_instruction is None
    assert config.tools is None
    assert config.response_mime_type == "application/json"
    assert (config.temperature, config.top_k, config.top_p) == (0.1, 40, 0.95)


@pytest.mark.spec("GENIA-BASE-003")
def test_servico_sem_chave_nao_obtem_cota():
    _quota("modelo-a")
    with pytest.raises(IAQuotaUnavailableError):
        IAGenaiBase().retrieve_quota_if_available()


@pytest.mark.spec("GENIA-BASE-004")
def test_cota_exige_autorizacao_ativo_e_margem():
    _quota("outro-servico", servicos=[IAQuota.ServicosAutorizados.IA_GENAI_BASE])
    _quota("inativa", ativo=False)
    esgotada = _quota("esgotada", quota_diaria=1)
    esgotada.create_log()

    ia = ServicoComCota()
    with pytest.raises(IAQuotaUnavailableError):
        ia.retrieve_quota_if_available()

    disponivel = _quota("disponivel")
    assert ia.retrieve_quota_if_available() == disponivel


@pytest.mark.spec("GENIA-BASE-005")
def test_ordem_de_escolha_da_cota_e_modelo_em_uso():
    _quota("menor", quota_diaria=5)
    _quota("maior", quota_diaria=50)
    ia = ServicoComCota()

    assert ia.retrieve_quota_if_available(ascending=True).modelo == "menor"
    assert ia.ia_model_name == "menor"
    assert ia.retrieve_quota_if_available(ascending=False).modelo == "maior"
    assert ia.ia_model_name == "maior"


@pytest.mark.spec("GENIA-BASE-006")
def test_cota_de_modelo_especifico():
    _quota("menor", quota_diaria=5)
    _quota("maior", quota_diaria=50)
    ia = ServicoComCota()

    assert ia.retrieve_quota_if_available(ia_model_name="maior").modelo == "maior"
    with pytest.raises(IAQuotaUnavailableError):
        ia.retrieve_quota_if_available(ia_model_name="inexistente")


@pytest.mark.spec("GENIA-BASE-007")
def test_generate_content_usa_modelo_da_cota_e_registra_consumo(client):
    quota = _quota("modelo-da-cota")

    ServicoComCota().generate_content("prompt")

    assert client.models.generate_content.call_args.kwargs["model"] == "modelo-da-cota"
    assert IAQuotasLog.objects.filter(quota=quota, peso=1).count() == 1


@pytest.mark.spec("GENIA-BASE-008")
def test_falha_da_api_nao_consome_cota(client):
    _quota("modelo-da-cota")
    client.models.generate_content.side_effect = RuntimeError("falha")

    with pytest.raises(RuntimeError):
        ServicoComCota().generate_content("prompt")

    assert IAQuotasLog.objects.count() == 0


@pytest.mark.spec("GENIA-BASE-009")
def test_sem_cota_nao_chama_a_api(client):
    with pytest.raises(IAQuotaUnavailableError):
        ServicoComCota().generate_content("prompt")

    client.models.generate_content.assert_not_called()


@pytest.mark.spec("GENIA-BASE-010")
def test_servico_isento_nao_consulta_nem_registra_cota(client):
    class Isento(IAGenaiBase):
        quota_exempt = True
        ia_model_name = "modelo-fixo"

    Isento().generate_content("prompt")

    assert client.models.generate_content.call_args.kwargs["model"] == "modelo-fixo"
    assert IAQuotasLog.objects.count() == 0


@pytest.mark.spec("GENIA-BASE-011")
def test_tools_ativam_function_calling_limitado():
    config = IAGenaiBase().build_generation_config(tools=[lambda query: query])

    assert len(config.tools) == 1
    assert config.automatic_function_calling.maximum_remote_calls == 10


@pytest.mark.spec("GENIA-BASE-012")
def test_sincroniza_modelos_sem_alterar_configuracao_existente(client):
    existente = _quota("modelo-a", quota_diaria=7)
    client.models.list.return_value = SimpleNamespace(
        page=[
            SimpleNamespace(name="models/modelo-a"),
            SimpleNamespace(name="models/modelo-b"),
        ]
    )

    IAGenaiBase().update_or_create_llm_models_in_quotamodel()

    existente.refresh_from_db()
    assert (existente.quota_diaria, existente.ativo) == (7, True)
    assert existente.servicos_autorizados == [str(SERVICO)]
    assert existente.descricao

    novo = IAQuota.objects.get(modelo="modelo-b")
    assert (novo.quota_diaria, novo.ativo, novo.servicos_autorizados) == (0, False, [])


@pytest.mark.spec("GENIA-BASE-013")
def test_count_tokens_devolve_zero_em_erro(client):
    client.models.count_tokens.side_effect = RuntimeError("falha")
    assert IAGenaiBase().count_tokens_in_text("texto") == 0


# ----------------------------------------------------------------------
# Serviços
# ----------------------------------------------------------------------


@pytest.mark.spec("GENIA-BASE-014")
def test_chave_de_cota_de_cada_servico():
    servicos = IAQuota.ServicosAutorizados
    assert IAChatService.quota_service_name == servicos.IA_GENAI_BASE
    assert (
        IAClassificacaoMateriaService.quota_service_name
        == servicos.IA_CLASSIFICACAO_MATERIA_SERVICE
    )
    assert (
        IAAnaliseSimilaridadeService.quota_service_name
        == servicos.IA_ANALISE_SIMILARIDADE_SERVICE
    )
    assert IAEmbeddingService.quota_exempt
    assert IAEmentaEmendaColetiva.quota_exempt


@pytest.mark.spec("GENIA-CHAT-001")
def test_chat_usa_system_instruction_do_rag_e_texto_puro():
    config = IAChatService().build_generation_config(tools=[lambda query: query])

    assert config.system_instruction == rag_system_instruction
    assert config.response_mime_type == "text/plain"


@pytest.mark.spec("GENIA-CHAT-002")
def test_chat_consome_cota_do_servico_e_registra_modelo(client):
    _quota("so-classificacao")
    quota = _quota("modelo-chat", servicos=[IAQuota.ServicosAutorizados.IA_GENAI_BASE])
    ia = IAChatService()

    ia.chat_send_message("oi", [], tools=[lambda query: query])

    assert client.chats.create.call_args.kwargs["model"] == "modelo-chat"
    assert ia.ia_model_name == "modelo-chat"
    assert IAQuotasLog.objects.filter(quota=quota).count() == 1


@pytest.mark.spec("GENIA-CHAT-003")
def test_chat_sem_cota_nao_abre_conversa(client):
    with pytest.raises(IAQuotaUnavailableError):
        IAChatService().chat_send_message("oi", [])

    client.chats.create.assert_not_called()


@pytest.mark.spec("GENIA-EMB-001")
def test_embedding_de_consulta_formata_tarefa_e_dimensao(client):
    ia = IAEmbeddingService()

    ia.get_query_embedding("iptu")
    kwargs = client.models.embed_content.call_args.kwargs
    assert kwargs["contents"] == ["task: question answering | query: iptu"]
    assert kwargs["config"].output_dimensionality == 1536
    assert kwargs["model"] == "gemini-embedding-2"

    ia.get_query_embedding("iptu", is_qa_mode=False)
    kwargs = client.models.embed_content.call_args.kwargs
    assert kwargs["contents"] == ["task: search result | query: iptu"]


@pytest.mark.spec("GENIA-EMB-002")
def test_documento_formatado_com_titulo():
    ia = IAEmbeddingService()
    assert ia.prepare_document("corpo", " Lei 1 ") == "title: Lei 1 | text: corpo"
    assert ia.prepare_document("corpo") == "title: none | text: corpo"


@pytest.mark.spec("GENIA-LOA-001")
def test_ementa_coletiva_usa_modelo_fixo_sem_cota(client):
    client.models.generate_content.return_value = SimpleNamespace(text="destinado a")

    ia = IAEmentaEmendaColetiva(["reforma da escola", "compra de livros"])
    assert ia.gerar_finalidade_global() == "destinado a"

    kwargs = client.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "gemini-3.1-flash-lite"
    assert "- reforma da escola\n- compra de livros" in kwargs["contents"][0]
    config = kwargs["config"]
    assert config.temperature == 0
    assert (config.top_k, config.top_p) == (None, None)
    assert (config.response_mime_type, config.system_instruction) == (None, None)
    assert IAQuotasLog.objects.count() == 0


@pytest.mark.spec("GENIA-LOA-002")
def test_ementa_coletiva_devolve_vazio_sem_ementas_ou_com_erro(client):
    assert IAEmentaEmendaColetiva().gerar_finalidade_global() == ""
    client.models.generate_content.assert_not_called()

    client.models.generate_content.side_effect = RuntimeError("falha")
    assert IAEmentaEmendaColetiva().gerar_finalidade_global(["a"]) == ""


@pytest.mark.spec("GENIA-SIM-001")
def test_similaridade_extrai_percentual_da_resposta():
    ia = IAAnaliseSimilaridadeService()
    ia.ia_model_name = "modelo-x"

    analise = ia.apply_answer(SimpleNamespace(), "Similaridade: [[ 85% ]]")
    assert (analise.similaridade, analise.ia_name) == (85, "modelo-x")
    assert analise.analise == "Similaridade: [[ 85% ]]"
    assert analise.data_analise

    assert ia.apply_answer(SimpleNamespace(), "[[90%]]").similaridade == 90
    assert ia.apply_answer(SimpleNamespace(), "sem marcação").similaridade == 0


@pytest.mark.spec("GENIA-SIM-002")
def test_similaridade_monta_prompt_com_textos_e_epigrafes():
    prompt = IAAnaliseSimilaridadeService().make_prompt(
        "texto {um}", "texto dois", "REQ 1/2025", "REQ 2/2025"
    )

    assert "<ORIGINAL>texto {um}</ORIGINAL>" in prompt
    assert "<ANALISADO>texto dois</ANALISADO>" in prompt
    assert '"REQ 1/2025" e "REQ 2/2025"' in prompt
    assert "[[ XX% ]]" in prompt


@pytest.mark.spec("GENIA-SIM-003")
def test_similaridade_sincrona_usa_maior_cota_e_salva(client):
    _quota(
        "menor",
        5,
        servicos=[IAQuota.ServicosAutorizados.IA_ANALISE_SIMILARIDADE_SERVICE],
    )
    maior = _quota(
        "maior",
        50,
        servicos=[IAQuota.ServicosAutorizados.IA_ANALISE_SIMILARIDADE_SERVICE],
    )
    client.models.generate_content.return_value = SimpleNamespace(text="[[ 70% ]]")
    analise = mock.Mock()

    ia = IAAnaliseSimilaridadeService()
    with mock.patch.object(ia, "make_prompt_from_similaridade", return_value="p"):
        ia.run(analise)

    kwargs = client.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "maior"
    assert kwargs["config"].response_mime_type == "text/plain"
    assert (analise.similaridade, analise.ia_name) == (70, "maior")
    analise.save.assert_called_once()
    assert IAQuotasLog.objects.filter(quota=maior).count() == 1
