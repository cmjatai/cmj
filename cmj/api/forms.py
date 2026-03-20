import logging
from decimal import Decimal

from django.db.models import Q
from django_filters import CharFilter, ModelChoiceFilter

from cmj.loa.models import EmendaLoa, Loa, RegistroAjusteLoa
from drfautoapi.drfautoapi import ApiFilterSetMixin

logger = logging.getLogger(__name__)


class CmjFilterSetMixin(ApiFilterSetMixin):
    pass


class EmendaLoaFilterSet(CmjFilterSetMixin):

    search = CharFilter(label="Busca", required=False, method="filter_search")

    situacao = CharFilter(label="Situação", required=False, method="filter_situacao")

    class Meta(CmjFilterSetMixin.Meta):
        model = EmendaLoa

    @property
    def qs(self):
        qs = super().qs
        if "situacao" not in self.data or not self.data.get("situacao"):
            qs = self.filter_situacao(qs, "situacao", "")
        return qs

    def filter_situacao(self, queryset, name, value):
        situacao = value.split(",")

        incluir_impedidas = "IMPEDIMENTO" in situacao
        incluir_em_execucao = "EM_EXECUCAO" in situacao
        incluir_finalizadas = "FINALIZADO" in situacao

        # tudo selecionado, retorna sem filtro
        if incluir_impedidas and incluir_em_execucao and incluir_finalizadas:
            return queryset

        # Nada selecionado, retorna sem filtro
        if not incluir_impedidas and not incluir_em_execucao and not incluir_finalizadas:
            return queryset

        q = Q()

        # Regra 1: inclui IMPEDIMENTO apenas se selecionado
        if incluir_impedidas:
            q &= Q(
                fase__in=[EmendaLoa.IMPEDIMENTO_TECNICO]
            )

        non_impedimento = ~Q(
            fase__in=[EmendaLoa.IMPEDIMENTO_TECNICO, EmendaLoa.EMENDA_REDEFINIDA]
        )

        if incluir_em_execucao and incluir_finalizadas and not incluir_impedidas:
            # ambos selecionados (sem impedimento): todas as não-impedimento
            if not incluir_impedidas:
                q &= non_impedimento
        elif incluir_em_execucao and not incluir_finalizadas and not incluir_impedidas:
            # Regra 2: exclui emendas que possuem registro FINALIZADO
            q &= non_impedimento & ~Q(prestacaocontaregistro_set__situacao="FINALIZADO")
        elif incluir_finalizadas and not incluir_em_execucao and not incluir_impedidas:
            # Regra 3: apenas emendas que possuem registro FINALIZADO
            q &= non_impedimento & Q(prestacaocontaregistro_set__situacao="FINALIZADO")

        return queryset.filter(q).distinct()

    def filter_search(self, queryset, name, value):
        query = value.split(" ")

        q = Q()
        for termo in query:
            q &= Q(search__unaccent__icontains=termo)
            continue
        return queryset.filter(q)


class RegistroAjusteLoaFilterSet(CmjFilterSetMixin):

    search = CharFilter(label="Busca", required=False, method="filter_search")

    situacao = CharFilter(label="Situação", required=False, method="filter_situacao")

    oficio_ajuste_loa__loa = ModelChoiceFilter(
        label="LOA", queryset=Loa.objects.all(), method="filter_oficio_ajuste_loa__loa"
    )

    class Meta(CmjFilterSetMixin.Meta):
        model = RegistroAjusteLoa

    @property
    def qs(self):
        qs = super().qs
        if "situacao" not in self.data or not self.data.get("situacao"):
            qs = self.filter_situacao(qs, "situacao", "")
        return qs

    def filter_oficio_ajuste_loa__loa(self, queryset, name, value):
        return queryset.filter(oficio_ajuste_loa__loa=value)

    def filter_search(self, queryset, name, value):

        query = value.split(" ")

        q = Q()
        for termo in query:
            q &= Q(search__unaccent__icontains=termo)
            continue
        return queryset.filter(q)

    def filter_situacao(self, queryset, name, value):
        situacao = value.split(",")

        incluir_em_execucao = "EM_EXECUCAO" in situacao
        incluir_finalizadas = "FINALIZADO" in situacao
        incluir_impedidas = "IMPEDIMENTO" in situacao

        q = Q()
        if incluir_impedidas:
            q &= Q(registroajusteloaparlamentar_set__valor__lt=0)
            q &= Q(emendaloa__isnull=False)
        else:
            q &= Q(registroajusteloaparlamentar_set__valor__gte=Decimal(0)) | Q(
                registroajusteloaparlamentar_set__isnull=True
            )

        # tudo selecionado, retorna sem filtro
        if incluir_em_execucao and incluir_finalizadas and incluir_impedidas:
            return queryset.filter(q).distinct()

        # Nada selecionado, retorna sem filtro
        if not incluir_em_execucao and not incluir_finalizadas and not incluir_impedidas:
            return queryset.filter(q).distinct()

        # Regra 1: inclui IMPEDIMENTO apenas se selecionado
        if incluir_impedidas:
            q &= Q(
                emendaloa__fase__in=[
                    EmendaLoa.IMPEDIMENTO_TECNICO,
                    EmendaLoa.EMENDA_REDEFINIDA,
                ]
            )

        non_impedimento = ~Q(
            emendaloa__fase__in=[
                EmendaLoa.IMPEDIMENTO_TECNICO,
                EmendaLoa.EMENDA_REDEFINIDA,
            ]
        )

        if incluir_em_execucao and incluir_finalizadas and not incluir_impedidas:
            # ambos selecionados (sem impedimento): todas as não-impedimento
            q &= non_impedimento
        elif incluir_em_execucao:
            # Regra 2: exclui emendas que possuem registro FINALIZADO
            q &= non_impedimento & ~Q(prestacaocontaregistro_set__situacao="FINALIZADO")
        elif incluir_finalizadas:
            # Regra 3: apenas emendas que possuem registro FINALIZADO
            q &= non_impedimento & Q(prestacaocontaregistro_set__situacao="FINALIZADO")

        return queryset.filter(q).distinct()
