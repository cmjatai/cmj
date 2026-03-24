import logging

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import DetailView

from cmj.mixins import PdfOutputMixin
from cmj.utils_report import make_pdf
from sapl.base.models import AppConfig as AppsAppConfig
from sapl.materia.models import Autoria, Tramitacao
from sapl.parlamentares.models import Filiacao, Parlamentar
from sapl.sessao.models import (
    AbstractOrdemDia,
    ExpedienteMateria,
    ExpedienteSessao,
    IntegranteMesa,
    JustificativaAusencia,
    OcorrenciaSessao,
    Orador,
    OradorExpediente,
    OradorOrdemDia,
    OrdemDia,
    PresencaOrdemDia,
    RegistroVotacao,
    ResumoOrdenacao,
    SessaoPlenaria,
    SessaoPlenariaPresenca,
    TipoExpediente,
    VotoParlamentar,
)

logger = logging.getLogger(__name__)


class ResumoMixin:

    @classmethod
    def get_identificacao_basica(cls, sessao_plenaria):
        # =====================================================================
        # Identificação Básica
        data_inicio = sessao_plenaria.data_inicio
        abertura = data_inicio.strftime("%d/%m/%Y") if data_inicio else ""
        data_fim = sessao_plenaria.data_fim
        encerramento = data_fim.strftime("%d/%m/%Y") + " -" if data_fim else ""
        tema_solene = sessao_plenaria.tema_solene
        context = {
            "basica": [
                _("Abertura: %(abertura)s - %(hora_inicio)s")
                % {"abertura": abertura, "hora_inicio": sessao_plenaria.hora_inicio},
                _("Encerramento: %(encerramento)s %(hora_fim)s")
                % {"encerramento": encerramento, "hora_fim": sessao_plenaria.hora_fim},
                _("Tipo de Sessão: %(tipo)s") % {"tipo": sessao_plenaria.tipo},
            ],
            "sessaoplenaria": sessao_plenaria,
        }
        if sessao_plenaria.tipo.nome == "Solene" and tema_solene:
            context.update({"tema_solene": "Tema da Sessão Solene: %s" % tema_solene})
        return context

    @classmethod
    def get_conteudo_multimidia(cls, sessao_plenaria):
        context = {}
        if sessao_plenaria.url_audio:
            context["multimidia_audio"] = _("Audio: ") + str(sessao_plenaria.url_audio)
        else:
            context["multimidia_audio"] = _("Audio: Indisponível")
        if sessao_plenaria.url_video:
            context["multimidia_video"] = _("Video: ") + str(sessao_plenaria.url_video)
        else:
            context["multimidia_video"] = _("Video: Indisponível")
        return context

    @classmethod
    def get_mesa_diretora(cls, sessao_plenaria):
        mesa = IntegranteMesa.objects.filter(sessao_plenaria=sessao_plenaria).order_by(
            "cargo_id"
        )
        integrantes = [
            {"parlamentar": m.parlamentar, "cargo": m.cargo, "assina_ata": m.assina_ata}
            for m in mesa
        ]
        return {"mesa": integrantes}

    @classmethod
    def get_presenca_sessao(cls, sessao_plenaria):

        parlamentares_sessao = [
            p.parlamentar
            for p in SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=sessao_plenaria.id
            )
            .order_by("parlamentar__nome_parlamentar")
            .distinct()
        ]

        ausentes_sessao = (
            JustificativaAusencia.objects.filter(sessao_plenaria_id=sessao_plenaria.id)
            .distinct()
            .order_by("parlamentar__nome_parlamentar")
        )

        return {
            "presenca_sessao": parlamentares_sessao,
            "justificativa_ausencia": ausentes_sessao,
        }

    @classmethod
    def get_expedientes(cls, sessao_plenaria):
        expediente = ExpedienteSessao.objects.filter(
            sessao_plenaria_id=sessao_plenaria.id
        ).order_by("tipo__nome")
        expedientes = []
        for e in expediente:
            tipo = TipoExpediente.objects.get(id=e.tipo_id)
            conteudo = e.conteudo
            ex = {"tipo": tipo, "conteudo": conteudo}
            expedientes.append(ex)
        return {"expedientes": expedientes}

    @classmethod
    def get_materias_expediente(cls, sessao_plenaria):
        materias_do_expediente = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=sessao_plenaria.id
        ).order_by("numero_ordem")

        materias_expediente = []
        for mat_exp in materias_do_expediente:

            ementa = mat_exp.materia.ementa
            titulo = mat_exp.materia.epigrafe_short
            numero = mat_exp.numero_ordem

            if mat_exp.tramitacao:
                tramitacao = mat_exp.tramitacao
            else:
                tramitacao = ""
                tramitacoes = Tramitacao.objects.filter(
                    materia=mat_exp.materia
                ).order_by("-pk")
                for aux_tramitacao in tramitacoes:
                    if aux_tramitacao.turno:
                        tramitacao = aux_tramitacao
                        break

            turno = tramitacao.get_turno_display() if tramitacao else ""

            # Ocorrências da Sessão Ligadas ao expendiente
            ocorrencias_exp = OcorrenciaSessao.objects.filter(
                expediente=mat_exp
            ).order_by("numero_ordem")
            ocorrencias_exp = [(e.titulo, e.conteudo) for e in ocorrencias_exp]

            if mat_exp.tipo_votacao == AbstractOrdemDia.LEITURA:
                rv = mat_exp.registroleitura_set.first()
                rp = mat_exp.retiradapauta_set.filter(materia=mat_exp.materia).first()
                if rv:
                    resultado = "Matéria Lida."
                    resultado_observacao = rv.observacao
                elif rp:
                    resultado = rp.tipo_de_retirada.descricao
                    resultado_observacao = rp.observacao
                else:
                    resultado = _("Matéria não lida.")
                    resultado_observacao = _(" ")
            else:
                rv = mat_exp.registrovotacao_set.first()
                rp = mat_exp.retiradapauta_set.filter(materia=mat_exp.materia).first()
                if rv:
                    resultado = rv.tipo_resultado_votacao.nome
                    resultado_observacao = rv.observacao
                elif rp:
                    resultado = rp.tipo_de_retirada.descricao
                    resultado_observacao = rp.observacao
                else:
                    resultado = _("Matéria não votada.")
                    resultado_observacao = _(" ")

            autoria = Autoria.objects.filter(materia_id=mat_exp.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {
                "ementa": ementa,
                "titulo": titulo,
                "numero": numero,
                "turno": turno,
                "resultado": resultado,
                "resultado_observacao": resultado_observacao,
                "autor": autor,
                "numero_protocolo": mat_exp.materia.numero_protocolo,
                "numero_processo": mat_exp.materia.numeracao_set.last(),
                "observacao": mat_exp.observacao,
                "ocorrencias_exp": ocorrencias_exp,
            }
            materias_expediente.append(mat)

        context = {"materia_expediente": materias_expediente}
        return context

    @classmethod
    def get_oradores_expediente(cls, sessao_plenaria):
        oradores = []
        for orador in OradorExpediente.objects.filter(
            sessao_plenaria_id=sessao_plenaria.id
        ).order_by("numero_ordem"):
            numero_ordem = orador.numero_ordem
            url_discurso = orador.url_discurso
            observacao = orador.observacao
            parlamentar = Parlamentar.objects.get(id=orador.parlamentar_id)
            ora = {
                "numero_ordem": numero_ordem,
                "url_discurso": url_discurso,
                "parlamentar": parlamentar,
                "observacao": observacao,
            }
            oradores.append(ora)
        return {"oradores": oradores}

    @classmethod
    def get_presenca_ordem_do_dia(cls, sessao_plenaria):
        parlamentares_ordem = [
            p.parlamentar
            for p in PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=sessao_plenaria.id
            )
            .distinct()
            .order_by("parlamentar__nome_parlamentar")
        ]

        return {"presenca_ordem": parlamentares_ordem}

    @classmethod
    def get_assinaturas(cls, sessao_plenaria):
        mesa_dia = cls.get_mesa_diretora(sessao_plenaria)["mesa"]

        presidente_dia = [
            next(
                iter(
                    [
                        m["parlamentar"]
                        for m in mesa_dia
                        if m["cargo"].descricao.startswith("Presidente")
                    ]
                ),
                "",
            )
        ]

        parlamentares_ordem = [
            p.parlamentar
            for p in PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=sessao_plenaria.id
            ).order_by("parlamentar__nome_parlamentar")
        ]

        parlamentares_mesa = [m["parlamentar"] for m in mesa_dia]

        # filtra parlamentares retirando os que sao da mesa
        parlamentares_ordem = [
            p for p in parlamentares_ordem if p not in parlamentares_mesa
        ]

        context = {}
        if any([m["assina_ata"] for m in mesa_dia]):
            # join dos cargos que assinam a ata
            cargos_dos_assinantes = [
                m["cargo"].descricao for m in mesa_dia if m["assina_ata"]
            ]
            # join com ", " e " e " para o ultimo item
            if len(cargos_dos_assinantes) > 1:
                texto_assinatura = (
                    ", ".join(cargos_dos_assinantes[:-1])
                    + " e "
                    + cargos_dos_assinantes[-1]
                )
            else:
                texto_assinatura = cargos_dos_assinantes[0]

            # filtra mesa dia para conter apenas os cargos que assinam a ata
            mesa_dia = [m for m in mesa_dia if m["assina_ata"]]
            context.update(
                {
                    "texto_assinatura": f"Assina{'m' if len(mesa_dia) > 1 else ''} %s"
                    % texto_assinatura
                }
            )
            context.update({"assinatura_mesa": mesa_dia})
            pass
        else:
            config_assinatura_ata = AppsAppConfig.attr("assinatura_ata")
            if config_assinatura_ata == "T" and parlamentares_ordem:
                context.update(
                    {
                        "texto_assinatura": "Assinatura de Todos os Parlamentares Presentes na Sessão"
                    }
                )
                context.update(
                    {
                        "assinatura_mesa": mesa_dia,
                        "assinatura_presentes": parlamentares_ordem,
                    }
                )
            elif config_assinatura_ata == "M" and mesa_dia:
                context.update(
                    {"texto_assinatura": "Assinatura da Mesa Diretora da Sessão"}
                )
                context.update({"assinatura_mesa": mesa_dia})
            elif config_assinatura_ata == "P" and presidente_dia and presidente_dia[0]:
                context.update(
                    {"texto_assinatura": "Assinatura do Presidente da Sessão"}
                )
                assinatura_presidente = [
                    {"parlamentar": presidente_dia[0], "cargo": "Presidente"}
                ]
                context.update({"assinatura_mesa": assinatura_presidente})

        return context

    @classmethod
    def get_materias_ordem_do_dia(cls, sessao_plenaria):
        ordem = OrdemDia.objects.filter(sessao_plenaria_id=sessao_plenaria.id).order_by(
            "parent__numero_ordem", "numero_ordem"
        )
        materias_ordem = []
        emendas_ordem = []
        for o in ordem:
            ementa = o.materia.ementa
            ementa_observacao = o.observacao
            titulo = o.materia.epigrafe_short
            numero = o.numero_ordem

            if o.tramitacao:
                tramitacao = o.tramitacao
            else:
                tramitacao = ""
                tramitacoes = Tramitacao.objects.filter(materia=o.materia).order_by(
                    "-pk"
                )
                for aux_tramitacao in tramitacoes:
                    if aux_tramitacao.turno:
                        tramitacao = aux_tramitacao
                        break

            turno = tramitacao.get_turno_display() if tramitacao else ""

            # Ocorrências da Sessão Ligadas a ordemdia (o)
            ocorrencias_ordem = OcorrenciaSessao.objects.filter(ordemdia=o).order_by(
                "numero_ordem"
            )
            ocorrencias_ordem = [(oo.titulo, oo.conteudo) for oo in ocorrencias_ordem]

            # Verificar resultado
            rv = o.registrovotacao_set.filter(materia=o.materia).first()
            rp = o.retiradapauta_set.filter(materia=o.materia).first()
            if rv:
                resultado = rv.tipo_resultado_votacao.nome
                resultado_observacao = rv.observacao

            elif rp:
                resultado = rp.tipo_de_retirada.descricao
                resultado_observacao = rp.observacao

            else:
                resultado = _("Matéria não votada")
                resultado_observacao = ""

            voto_sim = ""
            voto_nao = ""
            voto_abstencoes = ""
            voto_nominal = []

            if o.tipo_votacao == 2:
                votos = VotoParlamentar.objects.filter(ordem=o.id)
                for voto in votos:
                    aux_voto = (voto.parlamentar.nome_completo, voto.voto)
                    voto_nominal.append(aux_voto)
            try:
                voto = RegistroVotacao.objects.filter(ordem=o.id).last()
                voto_sim = voto.numero_votos_sim
                voto_nao = voto.numero_votos_nao
                voto_abstencoes = voto.numero_abstencoes
            except AttributeError:
                voto_sim = " Não Informado"
                voto_nao = " Não Informado"
                voto_abstencoes = " Não Informado"

            autoria = Autoria.objects.filter(materia_id=o.materia_id)
            autor = [str(x.autor) for x in autoria]
            mat = {
                "ementa": ementa,
                "ementa_observacao": ementa_observacao,
                "titulo": titulo,
                "numero": numero,
                "turno": turno,
                "resultado": resultado,
                "resultado_observacao": resultado_observacao,
                "autor": autor,
                "ocorrencias_ordem": ocorrencias_ordem,
                "numero_protocolo": o.materia.numero_protocolo,
                "numero_processo": o.materia.numeracao_set.last(),
                "tipo_votacao": o.TIPO_VOTACAO_CHOICES[o.tipo_votacao],
                "voto_sim": voto_sim,
                "voto_nao": voto_nao,
                "voto_abstencoes": voto_abstencoes,
                "voto_nominal": voto_nominal,
                "materia": o.materia,
                "tramitacao": tramitacao,
                "object": o,
            }
            if o.parent:
                emendas_ordem.append(mat)
            else:
                materias_ordem.append(mat)

        while emendas_ordem:
            eo = emendas_ordem.pop(0)
            for idx, mo in enumerate(materias_ordem):
                if eo["object"].parent == mo["object"]:
                    eo["numero"] = f'{mo["numero"]}-{eo["numero"]}'
                    materias_ordem.insert(idx + 1, eo)
                    break

        context = {"materias_ordem": materias_ordem}
        return context

    @classmethod
    def get_oradores_ordemdia(cls, sessao_plenaria):
        oradores = []

        oradores_ordem_dia = OradorOrdemDia.objects.filter(
            sessao_plenaria_id=sessao_plenaria.id
        ).order_by("numero_ordem")

        for orador in oradores_ordem_dia:
            numero_ordem = orador.numero_ordem
            url_discurso = orador.url_discurso
            observacao = orador.observacao
            parlamentar = Parlamentar.objects.get(id=orador.parlamentar_id)
            o = {
                "numero_ordem": numero_ordem,
                "url_discurso": url_discurso,
                "parlamentar": parlamentar,
                "observacao": observacao,
            }
            oradores.append(o)

        context = {"oradores_ordemdia": oradores}
        return context

    @classmethod
    def get_oradores_explicacoes_pessoais(cls, sessao_plenaria):
        oradores_explicacoes = []
        for orador in Orador.objects.filter(
            sessao_plenaria_id=sessao_plenaria.id
        ).order_by("numero_ordem"):
            for parlamentar in Parlamentar.objects.filter(id=orador.parlamentar.id):
                partido_sigla = Filiacao.objects.filter(parlamentar=parlamentar).last()
                if not partido_sigla:
                    sigla = ""
                else:
                    sigla = partido_sigla.partido.sigla
                oradores = {
                    "numero_ordem": orador.numero_ordem,
                    "parlamentar": parlamentar,
                    "sgl_partido": sigla,
                }
                oradores_explicacoes.append(oradores)
        context = {"oradores_explicacoes": oradores_explicacoes}
        return context

    @classmethod
    def get_ocorrencias_da_sessao(cls, sessao_plenaria):
        context = {}
        for local in OcorrenciaSessao.LocalChoices.values:
            context[f"ocorrencias_da_sessao_{local}"] = OcorrenciaSessao.objects.filter(
                sessao_plenaria_id=sessao_plenaria.id,
                expediente__isnull=True,
                ordemdia__isnull=True,
                local=local,
            ).order_by("numero_ordem")

        return context

    @classmethod
    def get_votos_nominais_materia_expediente(cls, sessao_plenaria):
        materias_expediente_votacao_nominal = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=sessao_plenaria.id, tipo_votacao=2
        ).order_by("-materia")

        votacoes = []
        for mevn in materias_expediente_votacao_nominal:
            votos_materia = []
            titulo_materia = mevn.materia
            registro = RegistroVotacao.objects.filter(expediente=mevn)
            if registro:
                for vp in VotoParlamentar.objects.filter(votacao=registro).order_by(
                    "parlamentar"
                ):
                    votos_materia.append(vp)

            dados_votacao = {"titulo": titulo_materia, "votos": votos_materia}
            votacoes.append(dados_votacao)

        return {"votos_nominais_materia_expediente": votacoes}

    @classmethod
    def get_votos_nominais_materia_ordem_dia(cls, sessao_plenaria):
        materias_ordem_dia_votacao_nominal = OrdemDia.objects.filter(
            sessao_plenaria_id=sessao_plenaria.id, tipo_votacao=AbstractOrdemDia.NOMINAL
        ).order_by("-materia")

        votacoes_od = []
        for modvn in materias_ordem_dia_votacao_nominal:
            votos_materia_od = []
            t_materia = modvn.materia
            registro_od = RegistroVotacao.objects.filter(ordem=modvn)
            if registro_od:
                for vp_od in VotoParlamentar.objects.filter(
                    votacao__in=registro_od
                ).order_by("parlamentar"):
                    votos_materia_od.append(vp_od)

            dados_votacao_od = {"titulo": t_materia, "votos": votos_materia_od}
            votacoes_od.append(dados_votacao_od)

        return {"votos_nominais_materia_ordem_dia": votacoes_od}


class ResumoView(ResumoMixin, DetailView):
    template_name = "sessao/resumos/index.html"
    model = SessaoPlenaria

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        if "check" in self.request.GET and self.request.user.is_authenticated:
            context.update({"check": True})

        # Votos de Votação Nominal de Matérias Expediente
        context.update(self.get_votos_nominais_materia_expediente(self.object))

        # =====================================================================
        # Identificação Básica
        context.update(self.get_identificacao_basica(self.object))
        # =====================================================================
        # Conteúdo Multimídia
        context.update(self.get_conteudo_multimidia(self.object))
        # =====================================================================
        # Mesa Diretora
        context.update(self.get_mesa_diretora(self.object))
        # =====================================================================
        # Presença Sessão
        context.update(self.get_presenca_sessao(self.object))
        # =====================================================================
        # Expedientes
        context.update(self.get_expedientes(self.object))
        # =====================================================================
        # Matérias Expediente
        context.update(self.get_materias_expediente(self.object))
        # =====================================================================
        # Oradores Expediente
        context.update(self.get_oradores_expediente(self.object))
        # =====================================================================
        # Presença Ordem do Dia
        context.update(self.get_presenca_ordem_do_dia(self.object))
        # =====================================================================
        # Assinaturas
        context.update(self.get_assinaturas(self.object))

        # =====================================================================
        # Matérias Ordem do Dia
        # Votos de Votação Nominal de Matérias Ordem do Dia
        context.update(self.get_votos_nominais_materia_ordem_dia(self.object))

        context.update(self.get_materias_ordem_do_dia(self.object))
        # =====================================================================
        # Oradores Ordem do Dia
        context.update(self.get_oradores_ordemdia(self.object))
        # =====================================================================
        # Oradores nas Explicações Pessoais
        context.update(self.get_oradores_explicacoes_pessoais(self.object))
        # =====================================================================
        # Ocorrẽncias da Sessão
        context.update(self.get_ocorrencias_da_sessao(self.object))
        # =====================================================================
        # Indica a ordem com a qual o template será renderizado
        dict_ord_template = {
            "cont_mult": "conteudo_multimidia.html",
            "exp": "expedientes.html",
            "id_basica": "identificacao_basica.html",
            "lista_p": "lista_presenca_sessao.html",
            "lista_p_o_d": "lista_presenca_ordem_dia.html",
            "mat_exp": "materias_expediente.html",
            "v_n_mat_exp": "votos_nominais_materias_expediente.html",
            "mat_o_d": "materias_ordem_dia.html",
            "v_n_mat_o_d": "votos_nominais_materias_ordem_dia.html",
            "mesa_d": "mesa_diretora.html",
            "oradores_exped": "oradores_expediente.html",
            "oradores_o_d": "oradores_ordemdia.html",
            "oradores_expli": "oradores_explicacoes.html",
            "ocorr_sessao": "ocorrencias_da_sessao.html",
        }

        ordenacao = ResumoOrdenacao.objects.get_or_create()[0]
        try:
            context.update(
                {
                    "primeiro_ordenacao": dict_ord_template[ordenacao.primeiro],
                    "segundo_ordenacao": dict_ord_template[ordenacao.segundo],
                    "terceiro_ordenacao": dict_ord_template[ordenacao.terceiro],
                    "quarto_ordenacao": dict_ord_template[ordenacao.quarto],
                    "quinto_ordenacao": dict_ord_template[ordenacao.quinto],
                    "sexto_ordenacao": dict_ord_template[ordenacao.sexto],
                    "setimo_ordenacao": dict_ord_template[ordenacao.setimo],
                    "oitavo_ordenacao": dict_ord_template[ordenacao.oitavo],
                    "nono_ordenacao": dict_ord_template[ordenacao.nono],
                    "decimo_ordenacao": dict_ord_template[ordenacao.decimo],
                    "decimo_primeiro_ordenacao": dict_ord_template[
                        ordenacao.decimo_primeiro
                    ],
                    "decimo_segundo_ordenacao": dict_ord_template[
                        ordenacao.decimo_segundo
                    ],
                    "decimo_terceiro_ordenacao": dict_ord_template[
                        ordenacao.decimo_terceiro
                    ],
                    "decimo_quarto_ordenacao": dict_ord_template[
                        ordenacao.decimo_quarto
                    ],
                }
            )
        except KeyError as e:
            self.logger.error(
                "KeyError: " + str(e) + ". Erro ao tentar utilizar "
                "configuração de ordenação. Utilizando ordenação padrão."
            )
            context.update(
                {
                    "primeiro_ordenacao": "identificacao_basica.html",
                    "segundo_ordenacao": "conteudo_multimidia.html",
                    "terceiro_ordenacao": "mesa_diretora.html",
                    "quarto_ordenacao": "lista_presenca_sessao.html",
                    "quinto_ordenacao": "expedientes.html",
                    "sexto_ordenacao": "materias_expediente.html",
                    "setimo_ordenacao": "votos_nominais_materias_expediente.html",
                    "oitavo_ordenacao": "oradores_expediente.html",
                    "nono_ordenacao": "lista_presenca_ordem_dia.html",
                    "decimo_ordenacao": "materias_ordem_dia.html",
                    "decimo_primeiro_ordenacao": "votos_nominais_materias_ordem_dia.html",
                    "decimo_segundo_ordenacao": "oradores_ordemdia.html",
                    "decimo_terceiro_ordenacao": "oradores_explicacoes.html",
                    "decimo_quarto_ordenacao": "ocorrencias_da_sessao.html",
                }
            )

        sessao = context["object"]
        tipo_sessao = sessao.tipo
        if tipo_sessao.nome == "Solene":
            context.update({"subnav_template_name": "sessao/subnav-solene.yaml"})
        return context


class ResumoAtaView(ResumoView):
    template_name = "sessao/resumos/ata.html"


class ResumoAtaPdfView(PdfOutputMixin, ResumoView):
    template_name = "sessao/resumos/pdf/ata_eletronica.html"
