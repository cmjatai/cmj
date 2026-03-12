from decimal import Decimal

from django.db.models import Q
from django_filters import CharFilter, ModelChoiceFilter

from cmj.loa.models import EmendaLoa, Loa, RegistroAjusteLoa
from drfautoapi.drfautoapi import ApiFilterSetMixin
from sapl.parlamentares.models import Parlamentar


class EmendaLoaFilterSet(ApiFilterSetMixin):

    search = CharFilter(label="Busca", required=False, method="filter_search")

    situacao = CharFilter(label="Situação", required=False, method="filter_situacao")

    class Meta(ApiFilterSetMixin.Meta):
        model = EmendaLoa

    @property
    def qs(self):
        qs = super().qs
        if "situacao" not in self.data or not self.data.get("situacao"):
            qs = self.filter_situacao(qs, "situacao", "")
        return qs

    def filter_situacao(self, queryset, name, value):
        situacao = value.split(",")

        has_impedimento = "IMPEDIMENTO" in situacao
        has_em_tramitacao = "EM_TRAMITACAO" in situacao
        has_finalizado = "FINALIZADO" in situacao

        # tudo selecionado, retorna sem filtro
        if has_impedimento and has_em_tramitacao and has_finalizado:
            return queryset

        # Nada selecionado, retorna sem filtro
        if not has_impedimento and not has_em_tramitacao and not has_finalizado:
            return queryset

        q = Q()

        # Regra 1: inclui IMPEDIMENTO apenas se selecionado
        if has_impedimento:
            q &= Q(fase=EmendaLoa.IMPEDIMENTO_TECNICO)

        non_impedimento = ~Q(fase=EmendaLoa.IMPEDIMENTO_TECNICO)

        if has_em_tramitacao and has_finalizado:
            # ambos selecionados (sem impedimento): todas as não-impedimento
            q &= non_impedimento
        elif has_em_tramitacao:
            # Regra 2: exclui emendas que possuem registro FINALIZADO
            q &= non_impedimento & ~Q(prestacaocontaregistro_set__situacao="FINALIZADO")
        elif has_finalizado:
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


class RegistroAjusteLoaFilterSet(ApiFilterSetMixin):

    search = CharFilter(label="Busca", required=False, method="filter_search")

    situacao = CharFilter(label="Situação", required=False, method="filter_situacao")

    oficio_ajuste_loa__loa = ModelChoiceFilter(
        label="LOA", queryset=Loa.objects.all(), method="filter_oficio_ajuste_loa__loa"
    )

    class Meta(ApiFilterSetMixin.Meta):
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

        has_em_tramitacao = "EM_TRAMITACAO" in situacao
        has_finalizado = "FINALIZADO" in situacao
        has_impedimento = "IMPEDIMENTO" in situacao

        q = Q()
        if has_impedimento:
            q &= Q(registroajusteloaparlamentar_set__valor__lt=0)
            q &= Q(emendaloa__isnull=False)
        else:
            q &= (Q(registroajusteloaparlamentar_set__valor__gte=Decimal(0)) | Q(registroajusteloaparlamentar_set__isnull=True))

        # tudo selecionado, retorna sem filtro
        if has_em_tramitacao and has_finalizado and has_impedimento:
            return queryset.filter(q).distinct()

        # Nada selecionado, retorna sem filtro
        if not has_em_tramitacao and not has_finalizado and not has_impedimento:
            return queryset.filter(q).distinct()

        # Regra 1: inclui IMPEDIMENTO apenas se selecionado
        if has_impedimento:
            q &= Q(emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO)

        non_impedimento = ~Q(emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO)

        if has_em_tramitacao and has_finalizado:
            # ambos selecionados (sem impedimento): todas as não-impedimento
            q &= non_impedimento
        elif has_em_tramitacao:
            # Regra 2: exclui emendas que possuem registro FINALIZADO
            q &= non_impedimento & ~Q(prestacaocontaregistro_set__situacao="FINALIZADO")
        elif has_finalizado:
            # Regra 3: apenas emendas que possuem registro FINALIZADO
            q &= non_impedimento & Q(prestacaocontaregistro_set__situacao="FINALIZADO")

        return queryset.filter(q).distinct()
