import logging

from django.db.models import Q
from django_filters import CharFilter, ModelChoiceFilter, MultipleChoiceFilter

from cmj.loa.models import (
    EmendaLoa,
    Entidade,
    Loa,
    RegistroAjusteLoa,
)
from drfautoapi.drfautoapi import ApiFilterSetMixin

logger = logging.getLogger(__name__)


class CmjFilterSetMixin(ApiFilterSetMixin):
    pass


class EntidadeFilterSet(CmjFilterSetMixin):

    search = CharFilter(label="Busca", required=False, method="filter_search")

    emendaloa_set__loa = ModelChoiceFilter(
        label="LOA", queryset=Loa.objects.all(), method="filter_emendaloa_set__loa"
    )

    loa = ModelChoiceFilter(
        label="LOA", queryset=Loa.objects.all(), method="filter_loa"
    )

    class Meta(CmjFilterSetMixin.Meta):
        model = Entidade

    def filter_loa(self, queryset, name, value):
        return (
            queryset.filter(emendaloa_set__loa=value)
            .union(queryset.filter(registroajusteloa_set__oficio_ajuste_loa__loa=value))
            .order_by("nome_fantasia")
        )

    def filter_emendaloa_set__loa(self, queryset, name, value):
        return queryset.filter(emendaloa_set__loa=value).distinct()

    def filter_search(self, queryset, name, value):
        query = value.split(" ")

        q = Q()
        for termo in query:
            q &= Q(nome_fantasia__unaccent__icontains=termo) | Q(
                razao_social__unaccent__icontains=termo
            )
            continue
        return queryset.filter(q)


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

        # se nada selecionado, retorna tudo
        if (
            not incluir_impedidas
            and not incluir_em_execucao
            and not incluir_finalizadas
        ):
            return queryset

        q = Q()

        if incluir_impedidas:
            q |= Q(fase=EmendaLoa.IMPEDIMENTO_TECNICO)
        if incluir_em_execucao:
            q |= Q(fase=EmendaLoa.EMENDA_EM_EXECUCAO)
        if incluir_finalizadas:
            q |= Q(fase=EmendaLoa.EMENDA_FINALIZADA)

        return queryset.filter(q)

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
        return qs.order_by("id").distinct()

    def filter_oficio_ajuste_loa__loa(self, queryset, name, value):
        return queryset.filter(oficio_ajuste_loa__loa=value).distinct()

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

        # tudo selecionado, retorna sem filtro
        if incluir_em_execucao and incluir_finalizadas and incluir_impedidas:
            return queryset

        # se nada selecionado, retorna tudo
        if (
            not incluir_em_execucao
            and not incluir_finalizadas
            and not incluir_impedidas
        ):
            return queryset

        q = Q()
        if incluir_impedidas:
            q |= Q(fase=RegistroAjusteLoa.AJUSTE_IMPEDIDO)
        if incluir_em_execucao:
            q |= Q(fase=RegistroAjusteLoa.AJUSTE_EM_EXECUCAO)
        if incluir_finalizadas:
            q |= Q(fase=RegistroAjusteLoa.AJUSTE_FINALIZADO)

        return queryset.filter(q)
