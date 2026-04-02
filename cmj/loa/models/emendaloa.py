import re
from decimal import Decimal

from _decimal import ROUND_HALF_DOWN
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.core.files import File
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Max
from django.db.models.aggregates import Sum
from django.db.models.deletion import CASCADE, PROTECT, SET_NULL
from django.db.models.fields.json import JSONField
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _

from cmj.core.models import CmjSearchMixin
from cmj.loa.models.ajusteloa import RegistroAjusteLoa, RegistroAjusteLoaParlamentar
from cmj.loa.models.entidade import TipoEntidade
from cmj.loa.models.financeiro_orcamento import UnidadeOrcamentaria
from cmj.loa.models.loa import Loa
from cmj.loa.models.registrocontabil import EmendaLoaRegistroContabil
from cmj.loa.services.emendaloa import EmendaLoaService
from cmj.utils import get_settings_auth_user_model, quantize, valor_por_extenso
from sapl.materia.models import Proposicao, TipoProposicao
from sapl.parlamentares.models import Parlamentar


class EmendaLoa(CmjSearchMixin):

    service = EmendaLoaService()

    SAUDE = 10
    DIVERSOS = 99
    MODIFICATIVA = 0
    TIPOEMENDALOA_CHOICE = (
        (SAUDE, _("Em.Imp. Saúde")),
        (DIVERSOS, _("Em.Imp. Áreas Diversas")),
        (MODIFICATIVA, _("Emenda Modificativa")),
    )

    PROPOSTA = 10
    PROPOSTA_LIBERADA = 12
    EDICAO_CONTABIL = 15
    LIBERACAO_CONTABIL = 17
    EM_TRAMITACAO = 20
    APROVACAO_LEGISLATIVA = 25
    APROVACAO_LEGAL = 30
    IMPEDIMENTO_TECNICO = 40
    EMENDA_REDEFINIDA = 50

    EMENDA_EM_EXECUCAO = 60
    EMENDA_FINALIZADA = 99

    FASE_CHOICE = (
        (PROPOSTA, _("Proposta Legislativa")),
        (PROPOSTA_LIBERADA, _("Proposta Liberada para Edição Contábil")),
        (EDICAO_CONTABIL, _("Em edição pela Contabilidade")),
        (
            LIBERACAO_CONTABIL,
            _("Liberado pela Contabilidade e/ou Aguardando Protocolo"),
        ),
        (EM_TRAMITACAO, _("Matéria protocolada, em tramitação")),
        (APROVACAO_LEGISLATIVA, _("Aprovada no Processo Legislativo")),
        (APROVACAO_LEGAL, _("Aprovada")),
        (IMPEDIMENTO_TECNICO, _("Impedimento Técnico")),
        (EMENDA_REDEFINIDA, _("Emenda Redefinida/Sanada")),
        (EMENDA_EM_EXECUCAO, _("Em Execução")),
        (EMENDA_FINALIZADA, _("Finalizada")),
    )

    IMPEDIMENTOS_CHOICE = (
        (IMPEDIMENTO_TECNICO, _("Impedimento Técnico")),
        (EMENDA_REDEFINIDA, _("Emenda Redefinida/Sanada")),
    )

    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    tipo = models.PositiveSmallIntegerField(
        choices=TIPOEMENDALOA_CHOICE, default=99, verbose_name=_("Área de aplicação")
    )

    fase = models.PositiveSmallIntegerField(
        choices=FASE_CHOICE, default=10, verbose_name=_("Fase")
    )

    indicacao = models.TextField(
        verbose_name=_("Indicação"), blank=True, null=True, default=None
    )

    entidade = models.ForeignKey(
        "loa.Entidade",
        verbose_name=_("Entidade"),
        related_name="emendaloa_set",
        blank=True,
        null=True,
        default=None,
        on_delete=PROTECT,
    )

    unidade = models.ForeignKey(
        "loa.UnidadeOrcamentaria",
        verbose_name=_("Unidade Orçamentária"),
        related_name="emendaloa_set",
        blank=True,
        null=True,
        default=None,
        on_delete=PROTECT,
    )

    finalidade = models.TextField(verbose_name=_("Finalidade"))

    prefixo_indicacao = models.CharField(
        verbose_name=_("Prefixo da Indicação"),
        max_length=30,
        blank=True,
        default="o(a)",
    )

    prefixo_finalidade = models.CharField(
        verbose_name=_("Prefixo da Finalidade"),
        max_length=30,
        blank=True,
        default="destinado a",
    )

    loa = models.ForeignKey(
        Loa, verbose_name=_("LOA"), related_name="emendaloa_set", on_delete=PROTECT
    )

    materia = models.OneToOneField(
        "materia.MateriaLegislativa",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Matéria Legislativa"),
        related_name="emendaloa",
        on_delete=PROTECT,
    )

    proposicao = models.OneToOneField(
        "materia.Proposicao",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Proposição Legislativa"),
        related_name="emendaloa",
        on_delete=SET_NULL,
    )

    valor = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor Global da Emenda (R$)"),
    )

    parlamentares = models.ManyToManyField(
        Parlamentar,
        through="EmendaLoaParlamentar",
        related_name="emendaloa_set",
        verbose_name=_("Parlamentares"),
        through_fields=("emendaloa", "parlamentar"),
    )

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Cadastrado Por"),
        related_name="+",
        on_delete=PROTECT,
    )

    _syncing = False

    class Meta:
        verbose_name = _("Emenda Impositiva/Modificativa")
        verbose_name_plural = _("Emendas Impositivas/Modificativas")
        ordering = ["id"]

        indexes = [
            GinIndex(
                OpClass("search", name="gin_trgm_ops"),
                name="emendaloa_search_gin_trgm",
            ),
        ]

        permissions = (
            ("emendaloa_full_editor", _("Edição completa de Emendas Impositivas.")),
        )

    @property
    def has_ajustes(self):
        return RegistroAjusteLoaParlamentar.objects.filter(
            registro__emendaloa=self
        ).exists()

    def __str__(self):
        valor_str = formats.number_format(self.valor, force_grouping=True)
        materia = ""
        if self.materia:
            materia = f"{self.materia.epigrafe_short} - "
        return f"{materia}R$ {valor_str} - {self.finalidade_format}"

    @property
    def ementa_format(self):
        if self.tipo:
            ementa = f"""
                Altera destinação de recursos orçamentários, indicando {self.prefixo_indicacao}
                {self.indicacao or "XXXXXXX"}, para a recepção do valor de
                R$ { self.str_valor} ({self.valor_por_extenso}), que será { self.prefixo_finalidade}
                { self.finalidade_format or "XXXXXXX"}.
            """
        else:
            ementa = f"""
                Altera destinação de recursos orçamentários, indicando {self.prefixo_indicacao}
                {self.indicacao or "XXXXXXX"}, para a recepção do valor de
                R$ { self.str_valor} ({self.valor_por_extenso}), que será { self.prefixo_finalidade}
                { self.finalidade_format or "XXXXXXX"}.
            """

        ementa = ementa.strip().replace("\n", " ")
        ementa = re.sub(r"\s+", " ", ementa)
        return ementa

    @property
    def fields_search(self):
        return ["artigos_search"]

    @property
    def artigos_search(self):
        _artigos_search = "\n".join([art[1] for art in self.artigos])
        _artigos_search = (
            f'{self.materia.epigrafe_short if self.materia else ""}\n{_artigos_search}'
        )
        return _artigos_search

    @property
    def artigos(self):
        artigos = []
        art_num = 0
        feminino = self.parlamentares.isonly_sexo_feminino()
        plural = self.parlamentares.count() > 1
        valor_str = self.str_valor
        extenso = self.valor_por_extenso

        # ementa
        ementa = (
            f"Altera destinação de recursos orçamentários, indicando "
            f'{self.prefixo_indicacao} {self.indicacao or "XXXXXXX"}, '
            f"para a recepção do valor de "
            f"R$ {valor_str} ({extenso}), "
            f"que será {self.prefixo_finalidade} "
            f'{self.finalidade_format or "XXXXXXX"}.'
        )
        artigos.append(("ementa", ementa))

        # preâmbulo
        art_def = "A" if feminino else "O"
        if plural:
            art_def += "s"
        subscritor = (
            "subscritora" if feminino else ("subscritores" if plural else "subscritor")
        )
        if feminino and plural:
            subscritor = "subscritoras"
        tipo_emenda = "Impositiva" if self.tipo else "Modificativa"
        preambulo = (
            f"{art_def} {subscritor} da presente Emenda {tipo_emenda}, "
            f"propõem a seguinte modificação no Projeto de Lei "
            f"Orçamentária Anual supracitado:"
        )
        artigos.append(("preambulo", preambulo))

        if self.tipo:
            # Art - Dedução
            art_num += 1
            deducoes = self.registrocontabil_set.all_deducoes()
            partes_deducao = []
            for i, rc in enumerate(deducoes):
                parte = (
                    f"Unidade Orçamentária {rc.despesa.unidade.especificacao} / "
                    f"Código: {rc.despesa.consulta.codigo} - {rc.despesa.consulta.especificacao} / "
                    f"Natureza da Despesa: {rc.despesa.consulta.cod_natureza}"
                )
                if deducoes.count() > 1:
                    parte += f" - Valor: R$ {formats.number_format(rc.valor.copy_abs(), force_grouping=True)}"
                partes_deducao.append(parte)
            texto_deducoes = (
                " // ".join(partes_deducao) if partes_deducao else "XXXXXXXXXX"
            )
            texto = (
                f"Art {art_num}º - Deduz-se da {texto_deducoes}, "
                f"o valor de R$ {valor_str} ({extenso})."
            )
            artigos.append(("artigo", texto))

            # Art - Inserção
            art_num += 1
            insercoes = self.registrocontabil_set.all_insercoes()
            partes_insercao = []
            for i, rc in enumerate(insercoes):
                parte = (
                    f"Unidade Orçamentária {rc.despesa.unidade.especificacao} / "
                    f"Código: {rc.despesa.consulta.codigo} - {rc.despesa.consulta.especificacao} / "
                    f"Natureza da Despesa: {rc.despesa.consulta.cod_natureza}"
                )
                if insercoes.count() > 1:
                    parte += f" - Valor: R$ {formats.number_format(rc.valor, force_grouping=True)}"
                partes_insercao.append(parte)
            texto_insercoes = (
                " // ".join(partes_insercao) if partes_insercao else "XXXXXXXXXX"
            )
            texto = (
                f"Art {art_num}º - O valor deduzido de "
                f"R$ {valor_str} ({extenso}), "
                f"será inserido na {texto_insercoes}, "
                f"{self.prefixo_finalidade} {self.finalidade_format}."
            )
            artigos.append(("artigo", texto))

            # Art - Divisão entre parlamentares (se mais de 1 e impositiva)
            if plural:
                art_num += 1
                art_gen = "as" if feminino else "os"
                vereador_gen = "vereadoras" if feminino else "vereadores"
                subscritor_gen = "subscritoras" if feminino else "subscritores"

                partes_parlamentares = []
                for elp in self.emendaloaparlamentar_set.all():
                    elp_valor_str = formats.number_format(
                        elp.valor, force_grouping=True
                    )
                    elp_extenso = valor_por_extenso(elp.valor)
                    gen_parl = "a" if elp.parlamentar.sexo == "F" else "o"
                    vereador_parl = (
                        "Vereadora" if elp.parlamentar.sexo == "F" else "Vereador"
                    )
                    partes_parlamentares.append(
                        f"R$ {elp_valor_str} ({elp_extenso}), "
                        f"d{gen_parl} {vereador_parl} {elp.parlamentar.nome_parlamentar}"
                    )
                lista_parlamentares = "; ".join(partes_parlamentares[:-1])
                if lista_parlamentares:
                    lista_parlamentares += "; " + partes_parlamentares[-1] + "."
                else:
                    lista_parlamentares = (
                        partes_parlamentares[0] + "." if partes_parlamentares else ""
                    )

                texto = (
                    f"Art {art_num}º - O valor de "
                    f"R$ {valor_str} ({extenso}), "
                    f"será divido entre {art_gen} {vereador_gen} {subscritor_gen}, "
                    f"sendo utilizado: {lista_parlamentares}"
                )
                artigos.append(("artigo", texto))

        else:
            # Emenda Modificativa - artigo único de alteração
            art_num += 1
            texto = (
                f"Art {art_num}º - Altera-se o Orçamento de {self.loa.ano}, "
                f"incluindo o valor de R$ {valor_str} ({extenso}), "
                f"{self.prefixo_finalidade} {self.finalidade_format}."
            )
            artigos.append(("artigo", texto))

        # Art - Demais artigos inalterados
        art_num += 1
        artigos.append(
            (
                "artigo",
                f"Art {art_num}º - Os demais artigos e dispositivos da matéria acima permanecem inalterados.",
            )
        )

        # Art - Parte integrante
        art_num += 1
        artigos.append(
            (
                "artigo",
                f"Art {art_num}º - A presente emenda fará parte integrante do Projeto de Lei em referência.",
            )
        )

        return artigos

    @property
    def finalidade_format(self):
        try:
            finalidade = self.finalidade
            chaves = re.findall(r"\{(.*?)\}", finalidade)

            for chave in chaves:
                chave_strip = chave.strip().lower()
                if "__" in chave_strip:
                    partes = chave_strip.split("__")
                    obj = self
                    for parte in partes:
                        if hasattr(obj, parte):
                            obj = getattr(obj, parte)
                        else:
                            obj = None
                            break
                    valor = str(obj) if obj else ""
                elif hasattr(self, chave_strip):
                    valor = getattr(self, chave_strip) or ""
                    if isinstance(valor, models.Model):
                        valor = str(valor)
                valor = valor.upper() if valor and isinstance(valor, str) else valor
                finalidade = finalidade.replace(f"{{{chave}}}", str(valor))

            finalidade = finalidade if finalidade[-1] != "." else finalidade[:-1]
            return finalidade
        except:
            return self.finalidade

    @property
    def str_valor(self):
        return formats.number_format(self.valor, force_grouping=True)

    @property
    def str_valor_computado(self):
        valor_str = formats.number_format(self.valor_computado, force_grouping=True)
        return valor_str

    @property
    def valor_computado(self):
        valor = Decimal("0.00")
        num_ajustes = RegistroAjusteLoa.objects.filter(emendaloa=self).count()
        if not num_ajustes and self.fase != self.IMPEDIMENTO_TECNICO:
            valor = self.valor
        # _print = f"""{"." * 20} - {self.id} - {self.materia.epigrafe_short if self.materia else ""} - {self.valor} - {self.fase} - {self.tipo} - {valor} """
        # print(_print)
        return valor

        soma_ajustes = RegistroAjusteLoaParlamentar.objects.filter(
            registro__emendaloa=self
        ).aggregate(Sum("valor"))

        valor = (
            soma_ajustes["valor__sum"]
            if soma_ajustes["valor__sum"] is not None
            else self.valor
        )
        return valor

    @property
    def valor_por_extenso(self):
        return valor_por_extenso(self.valor)

    def errors(self):
        erros = []
        if self.tipo in (self.SAUDE, self.DIVERSOS) and not self.unidade:
            erros.append("Emendas Impositivas devem ter Unidade Orçamentária.")

        # if self.tipo in (self.SAUDE, self.DIVERSOS) and not self.entidade:
        #    erros.append('Emendas Impositivas devem ter Entidade.')

        if (
            self.tipo == self.SAUDE
            and self.unidade
            and self.unidade.area != UnidadeOrcamentaria.SAUDE_CHOICE
        ):
            erros.append(
                "Emendas Impositivas da Saúde devem ter Unidade Orçamentária classificadas como sendo da Área da Saúde."
            )
            # existe registro com fonte diferente de 102?

        if (
            self.tipo == self.SAUDE
            and self.unidade
            and self.unidade.area == UnidadeOrcamentaria.SAUDE_CHOICE
        ):

            if (
                self.entidade
                and self.entidade.tipo_entidade
                and self.entidade.tipo_entidade.tipo_geral != TipoEntidade.SAUDE_CHOICE
            ):
                erros.append(
                    "Emendas Impositivas da Saúde devem ter Entidade do Tipo Saúde."
                )

            registros = self.registrocontabil_set.all()
            fontes_invalidas = registros.exclude(despesa__fonte__codigo="102")
            if fontes_invalidas.exists():
                erros.append(
                    "Emendas Impositivas da Saúde não podem ter registros com fonte diferente de 102."
                )

        # if self.tipo == self.DIVERSOS and self.unidade and self.unidade.area == UnidadeOrcamentaria.SAUDE_CHOICE:
        #    erros.append('Emendas Impositivas de Áreas Diversas não podem ter Unidade Orçamentária classificadas como sendo da Área da Saúde.')

        if (
            self.tipo == self.DIVERSOS
            and self.unidade
            and self.unidade.area == UnidadeOrcamentaria.EDUCACAO_CHOICE
        ):
            # existe registro com fonte diferente de 101?
            registros = self.registrocontabil_set.all()
            fontes_invalidas = registros.exclude(despesa__fonte__codigo="101")
            if fontes_invalidas.exists():
                erros.append(
                    "Emendas Impositivas da Educação não podem ter registros com fonte diferente de 101."
                )

        return erros

    def sync(self):
        registros = self.registrocontabil_set.all().order_by("valor")
        old_self = EmendaLoa.objects.filter(pk=self.pk).first()
        if self.tipo:
            soma_dict = self.emendaloaparlamentar_set.aggregate(Sum("valor"))
            self.valor = soma_dict["valor__sum"] or Decimal("0.00")
            self.save()

            if hasattr(self, "agrupamentoemendaloa"):
                registros.delete()
                # self.agrupamentoemendaloa.save()
                self.agrupamentoemendaloa.agrupamento.sync()
            else:
                if old_self:
                    valor_old = old_self.valor
                    tipo_old = old_self.tipo
                    unidade_old = old_self.unidade
                else:
                    valor_old = self.valor
                    tipo_old = self.tipo
                    unidade_old = self.unidade

                if tipo_old != self.tipo or unidade_old != self.unidade:
                    registros.delete()

                if registros.exists():
                    soma_registros_old = registros.aggregate(Sum("valor")).get(
                        "valor__sum", Decimal("0.00")
                    )
                    soma_registros = Decimal("0.00")
                    for r in registros:
                        r.valor = (
                            quantize(
                                r.valor * self.valor / valor_old,
                                rounding=ROUND_HALF_DOWN,
                            )
                            if valor_old
                            else Decimal("0.00")
                        )
                        soma_registros = soma_registros + r.valor
                        r.save()
                    divergencia = soma_registros_old - soma_registros
                    if not soma_registros_old and divergencia:
                        r = registros.last()
                        r.valor = r.valor + divergencia
                        r.save()
                else:
                    # criar um registro contabil com o valor da emenda com base no tipo da unidade orcamentaria
                    if (
                        self.loa.despesa_default_deducao_diversos
                        or self.loa.despesa_default_deducao_educacao
                        or self.loa.despesa_default_deducao_saude
                    ):
                        if (
                            self.unidade
                            and self.unidade.area == UnidadeOrcamentaria.SAUDE_CHOICE
                        ):
                            despesa = self.loa.despesa_default_deducao_saude
                        elif (
                            self.unidade
                            and self.unidade.area == UnidadeOrcamentaria.EDUCACAO_CHOICE
                        ):
                            despesa = self.loa.despesa_default_deducao_educacao
                        else:
                            despesa = self.loa.despesa_default_deducao_diversos

                        if despesa:
                            rc = EmendaLoaRegistroContabil()
                            rc.emendaloa = self
                            rc.despesa = despesa
                            rc.valor = self.valor * (-1)
                            rc.save()
        else:
            registros.delete()
            self.save()
            qspa = self.emendaloaparlamentar_set.all()
            valores = [quantize(self.valor / qspa.count())] * qspa.count()
            sum_valores = sum(valores)
            resto = self.valor - sum_valores
            if resto:
                valores[-1] = valores[-1] + resto

            elpv = zip(qspa, valores)

            for elp, v in elpv:
                elp.valor = v
                elp.save()
        return self

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.unidade:
            self.indicacao = self.unidade.especificacao

        creating = not self.pk

        if not self._syncing and not creating:
            self._syncing = True
            r = self.sync()
            self._syncing = False
            return r

        r = super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

        self.loa.update_disponibilidades()
        return r

    @property
    def totais_contabeis(self):
        deducoes = self.registrocontabil_set.filter(
            valor__lt=Decimal("0.00")
        ).aggregate(deducoes=Sum("valor"))

        insercoes = self.registrocontabil_set.filter(
            valor__gt=Decimal("0.00")
        ).aggregate(insercoes=Sum("valor"))

        deducoes = deducoes["deducoes"] or Decimal("0.00")
        insercoes = insercoes["insercoes"] or Decimal("0.00")

        divergencia_registros = insercoes + deducoes
        divergencia_emenda = self.valor - insercoes

        return {
            "soma_deducoes": deducoes,
            "soma_insercoes": insercoes,
            "divergencia_registros": divergencia_registros,
            "divergencia_emenda": divergencia_emenda,
            "valor_emendaloa": self.valor,
        }

    def retrieve_file_bytes(self):

        base_url = settings.SITE_URL.rstrip("/")
        import io

        import fitz  # PyMuPDF
        import requests

        pra_frente = True
        arq_bytes, arq_name = None, ""
        while True:
            response = requests.get(f"{base_url}/api/loa/emendaloa/{self.id}/view/")
            if response.status_code != 200:
                break

            arq_name = (
                response.headers.get("Content-Disposition", f"emenda_loa_{self.id}.pdf")
                .split("filename=")[-1]
                .strip('"')
            )

            arq_bytes = io.BytesIO(response.content)
            pdf = fitz.open(stream=arq_bytes, filetype="pdf")

            if pdf.page_count == 0:
                break

            if pdf.page_count > 1:
                pra_frente = False

            md = self.metadata
            md["style"] = md.get(
                "style",
                {
                    "lineHeight": 150,
                    "espacoAssinatura": 0,
                },
            )
            md["style"]["espacoAssinatura"] = md["style"].get("espacoAssinatura", 0)
            lineHeight = md["style"]["lineHeight"]

            if lineHeight < 110:
                break

            if pdf.page_count == 1 and not pra_frente:
                break

            if pra_frente and lineHeight > 200 and pdf.page_count == 1:
                break

            if pra_frente:
                lineHeight += 5
            else:
                lineHeight -= 1

            md["style"]["lineHeight"] = lineHeight
            self.metadata = md
            self.save()

            if pra_frente:
                continue

            page2 = pdf.load_page(1)
            text = page2.get_text("text")
            text = text
            if "A presente emenda fará parte" in text:
                break

        return arq_bytes, arq_name

    def registrar_proposicao(self):
        try:
            arq_bytes, arq_name = self.retrieve_file_bytes()

            autor = self.owner.operadorautor_set.first().autor

            proposicao = self.proposicao
            created = False
            if not proposicao:
                np_max = Proposicao.objects.filter(
                    autor=autor,
                    ano=(
                        self.loa.materia.ano
                        if self.loa.materia
                        else timezone.now().year
                    ),
                ).aggregate(np=Max("numero_proposicao"))

                proposicao = Proposicao()
                proposicao.numero_proposicao = np_max.get("np", 0) + 1
                created = True
            else:
                metadata = self.metadata or {}
                if metadata.get("signs", {}).get("texto_original", {}).get("signs", []):
                    raise Exception(
                        "Não é possível atualizar a Proposição Legislativa "
                        "de uma Emenda LOA que já foi assinada digitalmente. "
                        "É necessário realizar a substituição manual do arquivo no módulo de Proposições Legislativas."
                    )

            proposicao.autor = autor

            proposicao.tipo = TipoProposicao.objects.get(
                id=33 if self.tipo != EmendaLoa.MODIFICATIVA else 5,
            )
            proposicao.descricao = self.ementa_format
            proposicao.ano = timezone.now().year
            proposicao.materia_de_vinculo = self.loa.materia
            proposicao.user = self.owner
            proposicao.texto_original = File(arq_bytes, name=arq_name)
            proposicao.save()
            proposicao.hash_code = proposicao.gerar_hash()
            proposicao.save()

            self.proposicao = proposicao

            metadata = self.metadata or {}
            metadata.pop("register_emendaloa_proposicao_task", None)
            self.metadata = metadata
            self.save()
            return proposicao
        except Exception as e:
            metadata = self.metadata or {}
            metadata.pop("register_emendaloa_proposicao_task", None)
            self.metadata = metadata
            self.save()
            raise Exception(
                f"Ocorreu um erro ao registrar a Proposição Legislativa: {e}"
            )


class EmendaLoaHistoricoFase(models.Model):

    emendaloa = models.ForeignKey(
        "loa.EmendaLoa",
        verbose_name=_("Emenda Impositiva"),
        related_name="emendaloahistoricofase_set",
        on_delete=CASCADE,
    )

    fase = models.PositiveSmallIntegerField(
        choices=EmendaLoa.FASE_CHOICE, default=10, verbose_name=_("Fase")
    )

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Data e Hora"))

    class Meta:
        verbose_name = _("Histórico de Fase da Emenda Impositiva")
        verbose_name_plural = _("Históricos de Fase das Emendas Impositivas")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp.strftime('%d/%m/%Y %H:%M:%S')} - {self.get_fase_display()}"


class EmendaLoaParlamentar(models.Model):

    emendaloa = models.ForeignKey(
        "loa.EmendaLoa",
        verbose_name=_("Emenda Impositiva"),
        related_name="emendaloaparlamentar_set",
        on_delete=CASCADE,
    )

    parlamentar = models.ForeignKey(
        "parlamentares.Parlamentar",
        related_name="emendaloaparlamentar_set",
        verbose_name=_("Parlamentar"),
        on_delete=PROTECT,
    )

    valor = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor por Parlamentar (R$)"),
    )

    def __str__(self):
        valor_str = formats.number_format(self.valor, force_grouping=True)
        return f"R$ {valor_str} - {self.parlamentar.nome_parlamentar}"

    class Meta:
        verbose_name = _("Participação Parlamentar na Emenda Impositiva")
        verbose_name_plural = _("Participações Parlamentares na Emenda Impositiva")
        ordering = ["id"]
