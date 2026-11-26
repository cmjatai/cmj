import re
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.db.models import manager
from django.db.models.deletion import CASCADE, PROTECT
from django.db.models.fields.json import JSONField
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from cmj.loa.models.m_emendaloa import EmendaLoa, EmendaLoaParlamentar
from cmj.loa.models.m_registrocontabil import EmendaLoaRegistroContabil
from cmj.loa.services.s_agrupamento import AgrupamentoService
from cmj.utils import PERCENTAGE_VALIDATOR, quantize
from cmj.utils.genia.loa_agrupamento import (
    IAEmentaEmendaColetiva,
    IAEmentaEmendaColetivaError,
)
from sapl.parlamentares.models import Parlamentar


class FinalidadeManualRemovida(ValueError):
    """A finalidade digitada foi apagada porque as emendas deixaram de ter a mesma
    unidade e entidade (LOA-AGR-053)."""

    MENSAGEM = (
        "A finalidade digitada foi apagada porque as emendas do agrupamento não têm "
        "mais a mesma unidade e entidade. Cada emenda coletiva receberá a finalidade "
        "automática do seu conjunto."
    )

    def __init__(self, mensagem=MENSAGEM):
        super().__init__(mensagem)


class Agrupamento(models.Model):
    service = AgrupamentoService()

    SAUDE = 10
    DIVERSOS = 99
    TIPOEMENDALOA_CHOICE = (
        (-1, _("Não selecionado")),
        (SAUDE, _("Em.Imp. Saúde")),
        (DIVERSOS, _("Em.Imp. Áreas Diversas")),
    )

    loa = models.ForeignKey(
        "loa.Loa",
        verbose_name=_("LOA"),
        related_name="agrupamento_set",
        on_delete=PROTECT,
    )

    nome = models.CharField(verbose_name=_("Nome do Agrupamento"), max_length=256)

    tipo = models.SmallIntegerField(
        choices=TIPOEMENDALOA_CHOICE, default=-1, verbose_name=_("Área de aplicação")
    )

    finalidade = models.TextField(verbose_name=_("Finalidade"), blank=True, default="")

    # LOA-AGR-053: finalidade digitada pelo editor, mantida nas inclusões e remoções
    finalidade_manual = models.BooleanField(
        verbose_name=_("Finalidade digitada manualmente"),
        default=False,
        db_default=False,
    )

    emendas = models.ManyToManyField(
        "loa.EmendaLoa",
        through="AgrupamentoEmendaLoa",
        related_name="agrupamento_set",
        verbose_name=_("Emendas Impositivas/Modificativas"),
        through_fields=("agrupamento", "emendaloa"),
    )

    despesas = models.ManyToManyField(
        "loa.Despesa",
        through="AgrupamentoRegistroContabil",
        related_name="agrupamento_set",
        verbose_name=_("Registro Contabeis Agrupamento"),
        through_fields=("agrupamento", "despesa"),
    )

    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    class Meta:
        verbose_name = _("Agrupamento de Emenda Impositiva/Modificativas")
        verbose_name_plural = _("Agrupamentos de Emendas Impositivas/Modificativas")
        ordering = ["id"]

    def __str__(self):
        return self.nome

    @property
    def finalidade_format(self):
        try:
            finalidade = self.finalidade or ""

            while len(finalidade) > 0 and (re.match(r"[^\w\)\$]", finalidade[-1])):
                finalidade = finalidade[:-1]

            return finalidade
        except Exception:
            return ""

    def create_copia(self):
        # verifica antes o número de cópias colocando o número dentro do nome
        nome = self.nome.split(" (Cópia")[0]
        num_copias = Agrupamento.objects.filter(
            loa=self.loa, nome__startswith=nome
        ).count()
        nome_copia = f"{nome} (Cópia {num_copias + 1})"
        copia = Agrupamento.objects.create(
            loa=self.loa,
            nome=nome_copia,
            finalidade="",
            metadata={},
        )

        for registro in self.agrupamentoregistrocontabil_set.all():
            copia.agrupamentoregistrocontabil_set.create(
                despesa=registro.despesa,
                percentual=registro.percentual,
                operacao=registro.operacao if hasattr(registro, "operacao") else None,
            )
        return copia

    def sync(self):
        registros = self.agrupamentoregistrocontabil_set.all()

        for emenda in self.emendas.all():
            emenda.registrocontabil_set.all().delete()

            deducoes = []
            insercoes = []
            soma_zero = Decimal("0.00")
            for r in registros:
                elrc = EmendaLoaRegistroContabil()
                elrc.emendaloa = emenda
                elrc.despesa = r.despesa
                elrc.valor = quantize(emenda.valor * r.percentual / Decimal(100))
                elrc.save()

                soma_zero += r.percentual

                if r.percentual < Decimal("0.00"):
                    deducoes.append(elrc)
                else:
                    insercoes.append(elrc)

            if soma_zero == Decimal("0.00"):
                sum_deducoes = sum(map(lambda x: x.valor, deducoes))
                sum_insercoes = sum(map(lambda x: x.valor, insercoes))

                if abs(sum_deducoes) != emenda.valor and deducoes:
                    resto = emenda.valor + sum_deducoes
                    deducoes[-1].valor = deducoes[-1].valor - resto
                    deducoes[-1].save()

                if abs(sum_insercoes) != emenda.valor and insercoes:
                    resto = emenda.valor - sum_insercoes
                    insercoes[-1].valor = insercoes[-1].valor + resto
                    insercoes[-1].save()

    def esta_vazio(self):
        """Sem emendas, registros contábeis, coletivas geradas nem finalidade (LOA-AGR-012)."""
        return not (
            self.finalidade.strip()
            or self.agrupamentoemendaloa_set.exists()
            or self.agrupamentoregistrocontabil_set.exists()
            or self.emendas_coletivas_geradas.exists()
        )

    def emendas_sem_juncao(self):
        """Emendas que formariam coletiva se "Gerar Emendas Coletivas" fosse chamado agora.

        Mesmo critério de preparar_dados_para_coletiva e gerar_emendas_coletivas, sem a I.A.:
        permitem junção, não têm matéria, não estão na fase -10 e estão num conjunto de unidade
        e entidade com mais de uma emenda (LOA-AGR-083).
        """
        conjuntos = {}
        for emenda in self.emendas.all():
            if not emenda.permite_juncao_coletiva or emenda.materia_id:
                continue
            key = (emenda.unidade_id, emenda.entidade_id)
            conjuntos.setdefault(key, []).append(emenda)

        return [
            e for emendas in conjuntos.values() if len(emendas) > 1 for e in emendas
        ]

    def update_finalidade_com_ia(self, forcar=False):
        """Gera a finalidade por I.A. (LOA-AGR-050 e 053).

        Sem forcar (inclusão e remoção de emenda), a finalidade digitada é mantida e a
        I.A. não é chamada. forcar=True (Ctrl+clique) substitui também a digitada.
        """

        # verifica se todas as emendas são tem a mesma unidade e entidade
        emendas = list(self.emendas.values("unidade", "entidade"))
        if not emendas:
            raise ValueError("Não há emendas para este agrupamento")
        first_unidade = emendas[0]["unidade"]
        first_entidade = emendas[0]["entidade"]
        error = False
        for e in emendas:
            if e["unidade"] != first_unidade or e["entidade"] != first_entidade:
                error = True
                break

        if error:
            era_manual = self.finalidade_manual and bool(self.finalidade.strip())
            self.finalidade = ""
            self.finalidade_manual = False
            self.save(update_fields=["finalidade", "finalidade_manual"])
            if era_manual:
                raise FinalidadeManualRemovida()
            raise ValueError(
                "É necessário que todas as emendas possuam a mesma unidade e entidade."
            )

        if self.finalidade_manual and not forcar:
            return

        try:
            ia = IAEmentaEmendaColetiva([str(e.finalidade) for e in self.emendas.all()])
            self.finalidade = ia.gerar_finalidade_global()
        except IAEmentaEmendaColetivaError:
            # erro repassado para ser exibido ao usuário; a finalidade gerada antes é
            # limpa, mas a digitada é mantida (LOA-AGR-053)
            if not self.finalidade_manual:
                self.finalidade = ""
                self.save(update_fields=["finalidade"])
            raise
        self.finalidade_manual = False
        self.save(update_fields=["finalidade", "finalidade_manual"])

    def preparar_dados_para_coletiva(self, for_preview=False):

        # a chave de agrupamento de emendas é a unidade + entidade, onde unidade nunca é nula mas a entidade pode ser nula

        emendas_coletivas = {}

        for emenda in self.emendas(
            manager=("all_objects" if for_preview else "objects")
        ).all():
            if not emenda.permite_juncao_coletiva or emenda.materia:
                continue

            key = (emenda.unidade, emenda.entidade)
            if key not in emendas_coletivas:
                emendas_coletivas[key] = {
                    "emendas": [],
                    "insercoes": {},
                    "deducoes": {},
                    "parlamentares": {},
                    "total_via_parlamentares": Decimal("0.00"),
                }
            emendas_coletivas[key]["emendas"].append(emenda)

            insercoes = emendas_coletivas[key]["insercoes"]
            deducoes = emendas_coletivas[key]["deducoes"]
            parlamentares = emendas_coletivas[key]["parlamentares"]
            total_via_parlamentares = emendas_coletivas[key]["total_via_parlamentares"]

            for r in emenda.registrocontabil_set.all_insercoes():
                insercoes[r.despesa] = (
                    insercoes.get(r.despesa, Decimal("0.00")) + r.valor
                )
            for r in emenda.registrocontabil_set.all_deducoes():
                deducoes[r.despesa] = deducoes.get(r.despesa, Decimal("0.00")) + r.valor

            for elp in emenda.emendaloaparlamentar_set.all():
                if elp.parlamentar not in parlamentares:
                    parlamentares[elp.parlamentar] = {
                        "valor": Decimal("0.00"),
                        "prefixo_finalidade": emenda.prefixo_finalidade,
                        "finalidade": [],
                    }
                parlamentares[elp.parlamentar]["valor"] += elp.valor
                parlamentares[elp.parlamentar]["finalidade"].append(
                    f"<strong>R$ {emenda.str_valor}</strong> - {emenda.prefixo_finalidade} {emenda.finalidade_format}"
                )
                total_via_parlamentares += elp.valor

            emendas_coletivas[key]["total_via_parlamentares"] = total_via_parlamentares

        # ordenar parlamentares por nome_parlamentar
        for key in emendas_coletivas:
            parlamentares = emendas_coletivas[key]["parlamentares"]
            emendas_coletivas[key]["parlamentares"] = dict(
                sorted(parlamentares.items(), key=lambda item: item[0].nome_parlamentar)
            )

        # criar finalidade agregada para cada agrupamento via I.A.
        # Na prévia, a falha vira aviso no PDF; na geração, interrompe com erro.
        if not self.finalidade:
            ia = IAEmentaEmendaColetiva()
            for key in emendas_coletivas:
                emendas = emendas_coletivas[key]["emendas"]
                finalidades = [emenda.finalidade for emenda in emendas]
                try:
                    finalidade_automatica = ia.gerar_finalidade_global(finalidades)
                except IAEmentaEmendaColetivaError as e:
                    if not for_preview:
                        raise
                    emendas_coletivas[key]["aviso_finalidade"] = str(e)
                    finalidade_automatica = ""
                emendas_coletivas[key]["finalidade_automatica"] = finalidade_automatica

        return [
            {
                "object": self,
                "emendas": value["emendas"],
                "unidade": unidade,
                "entidade": entidade,
                "finalidade_customizada": self.finalidade,
                "finalidade_automatica": value.get("finalidade_automatica", None),
                "aviso_finalidade": value.get("aviso_finalidade", ""),
                "bairro": value["emendas"][0].bairro if value["emendas"] else None,
                "total_via_parlamentares": value["total_via_parlamentares"],
                "parlamentares": Parlamentar.objects.filter(
                    id__in=[p.id for p in value["parlamentares"].keys()]
                ),
                "parlamentares_list_values": value["parlamentares"],
                "insercoes": value["insercoes"],
                "deducoes": value["deducoes"],
            }
            for (unidade, entidade), value in emendas_coletivas.items()
        ]

    def cancelar_emendas_coletivas(self, user=None):
        """Devolve o agrupamento à edição contábil (LOA-AGR-072).

        Exclui as coletivas geradas e devolve para 15 as emendas nas fases -10 e 17.
        Recusa, sem mudar nada, se alguma coletiva já está em tramitação.
        Devolve (coletivas excluídas, emendas devolvidas).
        """
        # manager="all_objects" já não filtra a fase; .all_objects() no related manager
        # perderia o filtro do relacionamento e traria emendas de toda a base
        coletivas = self.emendas_coletivas_geradas(manager="all_objects").all()
        if coletivas.filter(fase__gte=EmendaLoa.EM_TRAMITACAO).exists():
            raise ValueError(
                "Há emenda coletiva deste agrupamento em tramitação. "
                "Não é possível cancelar as coletivas."
            )

        with transaction.atomic():
            devolvidas = 0
            for e in self.emendas(manager="all_objects").filter(
                fase__in=(
                    EmendaLoa.TRANSFORMADA_EM_COLETIVA,
                    EmendaLoa.LIBERACAO_CONTABIL,
                )
            ):
                e.emenda_coletiva = None
                e.fase = EmendaLoa.EDICAO_CONTABIL
                e._usuario_fase = user  # LOA-FASE-067
                e.save()
                devolvidas += 1

            excluidas = 0
            for ec in coletivas:
                ec.delete()
                excluidas += 1

        return excluidas, devolvidas

    def gerar_emendas_coletivas(self, user=None):
        # LOA-FASE-071: sem responsável válido, recusa antes da I.A. e de qualquer gravação
        responsavel = self.loa.service.responsavel_coletivas(self.loa)

        emendas_preparadas = self.preparar_dados_para_coletiva()

        emendas_criadas = []  # Lista para armazenar as emendas coletivas criadas
        try:

            with transaction.atomic():

                for emenda in emendas_preparadas:
                    if not emenda["emendas"] or len(emenda["emendas"]) == 1:
                        continue

                    ec = EmendaLoa()  # ec -> emenda_coletiva
                    ec.permite_juncao_coletiva = False
                    ec.agrupamento_de_origem = self
                    # LOA-FASE-071: dono da coletiva é o responsável definido na LOA
                    ec.owner = responsavel
                    ec.valor = emenda["total_via_parlamentares"]
                    ec.loa = self.loa
                    ec.prefixo_finalidade = ""
                    ec.prefixo_indicacao = ""
                    ec.finalidade = (
                        self.finalidade or emenda["finalidade_automatica"] or ""
                    )
                    ec.unidade = emenda["unidade"]
                    ec.entidade = emenda["entidade"]
                    ec.bairro = emenda["bairro"]
                    ec.indicacao = emenda["unidade"].especificacao
                    ec.fase = EmendaLoa.EDICAO_CONTABIL
                    ec.tipo = emenda["emendas"][0].tipo
                    ec._usuario_fase = user  # LOA-FASE-067
                    ec.save()

                    for ems in emenda["emendas"]:
                        ems.emenda_coletiva = ec
                        ems.fase = EmendaLoa.TRANSFORMADA_EM_COLETIVA
                        ems._usuario_fase = user  # LOA-FASE-067
                        ems.save()

                    for p, v in emenda["parlamentares_list_values"].items():
                        elp = EmendaLoaParlamentar()
                        elp.emendaloa = ec
                        elp.parlamentar = p
                        elp.valor = v["valor"]
                        elp.save()

                    # inserções
                    for despesa, valor in emenda["insercoes"].items():
                        erc = EmendaLoaRegistroContabil()
                        erc.emendaloa = ec
                        erc.despesa = despesa
                        erc.valor = valor
                        erc.save()

                    # deduções
                    for despesa, valor in emenda["deducoes"].items():
                        erc = EmendaLoaRegistroContabil()
                        erc.emendaloa = ec
                        erc.despesa = despesa
                        erc.valor = valor
                        erc.save()

                    ec.refresh_from_db()
                    ec.save()

                    emendas_criadas.append(ec)
            return emendas_criadas
        except Exception as e:
            raise e


class AgrupamentoEmendaLoa(models.Model):
    agrupamento = models.ForeignKey(
        "loa.Agrupamento",
        verbose_name=_("Agrupamento de Emenda Impositiva"),
        related_name="agrupamentoemendaloa_set",
        on_delete=CASCADE,
    )

    emendaloa = models.OneToOneField(
        "loa.EmendaLoa",
        verbose_name=_("Emenda Impositiva"),
        related_name="agrupamentoemendaloa",
        on_delete=CASCADE,
    )

    class Meta:
        verbose_name = _("Agrupamento de Emenda Impositiva")
        verbose_name_plural = _("Agrupamentos de Emendas Impositivas")
        ordering = ["id"]

        unique_together = (
            (
                "agrupamento",
                "emendaloa",
            ),
        )


class AgrupamentoRegistroContabilManager(manager.Manager):

    use_for_related_fields = True

    def all_deducoes(self):
        qs = self.get_queryset()
        qs = qs.filter(percentual__lt=Decimal("0.00"))
        return qs

    def all_insercoes(self):
        qs = self.get_queryset()
        qs = qs.filter(percentual__gt=Decimal("0.00"))
        return qs


class AgrupamentoRegistroContabil(models.Model):

    DEDUCAO = 10
    INSERCAO = 20

    OPERACAO_CHOICE = ((DEDUCAO, _("Dedução")), (INSERCAO, _("Inserção")))

    objects = AgrupamentoRegistroContabilManager()

    agrupamento = models.ForeignKey(
        "loa.Agrupamento",
        verbose_name=_("Agrupamento de Emenda Impositiva"),
        related_name="agrupamentoregistrocontabil_set",
        on_delete=CASCADE,
    )

    despesa = models.ForeignKey(
        "loa.Despesa",
        blank=True,
        null=True,
        default=None,
        related_name="agrupamentoregistrocontabil_set",
        verbose_name=_("Despesa"),
        on_delete=CASCADE,
    )

    operacao = models.PositiveSmallIntegerField(
        choices=OPERACAO_CHOICE, default=10, verbose_name=_("Operação")
    )

    percentual = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("100.00"),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_("Percentual do Valor da Emenda"),
    )

    class Meta:
        verbose_name = _("Registro Contábil de Dedução e Inserção em Emendas")
        verbose_name_plural = _("Registros Contábeis de Dedução e Inserção em Emendas")
        ordering = ["id"]

        unique_together = (
            (
                "agrupamento",
                "despesa",
            ),
        )

    def __str__(self):
        percentual_str = formats.number_format(self.percentual, force_grouping=True)
        return f"{percentual_str}% - {self.despesa}"

    @property
    def str_percentual(self):
        return formats.number_format(self.percentual, force_grouping=True)
