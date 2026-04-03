import logging
from decimal import Decimal

from django import forms
from django.contrib.postgres.forms.array import SplitArrayField
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.utils.translation import gettext_lazy as _

from cmj.loa.models import (
    EmendaLoa,
    Entidade,
    OficioAjusteLoa,
    RegistroAjusteLoa,
    RegistroAjusteLoaParlamentar,
    UnidadeOrcamentaria,
)
from cmj.utils import DecimalField
from sapl.utils import FileFieldCheckMixin

logger = logging.getLogger(__name__)


class OficioAjusteLoaForm(FileFieldCheckMixin, ModelForm):

    class Meta:
        model = OficioAjusteLoa
        fields = ["epigrafe", "parlamentares", "arquivo"]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.loa = kwargs["initial"]["loa"]
        self.parlamentares = self.loa.parlamentares.order_by("nome_parlamentar")

        self.fields["parlamentares"].choices = [(p.pk, p) for p in self.parlamentares]


class RegistroAjusteLoaForm(ModelForm):

    emendaloa = forms.ModelMultipleChoiceField(
        queryset=EmendaLoa.objects.all(),
        label="Emendas da LOA relacionadas ao Parlamentar do Oficio de Ajuste",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "title": "Selecione as emendas relacionadas ao parlamentar do oficio de ajuste",
                "class": "selectpicker w-100",
                "data-actions-box": "true",
                "data-select-all-text": "Selecionar Todos",
                "data-deselect-all-text": "Desmarcar Todos",
                "data-live-search": "true",
                "data-header": "Emendas Cadastradas",
                "data-dropup-auto": "false",
            }
        ),
    )

    entidade = forms.ModelChoiceField(
        queryset=Entidade.objects.all(),
        label="Entidade Ativas",
        required=False,
        widget=forms.Select(
            attrs={
                "title": "Selecione as entidades ativas",
                "class": "selectpicker w-100",
                "data-actions-box": "true",
                "data-live-search": "true",
                "data-header": "Entidades Ativas",
                "data-dropup-auto": "false",
            }
        ),
    )

    parlamentares__valor = SplitArrayField(
        DecimalField(
            required=False,
            max_digits=14,
            decimal_places=2,
        ),
        10,
        label="Valores por Parlamentar",
        help_text="Valores negativos sem seleção de emenda são meramente informativos com a finalidade de concentração em outro item.",
        required=False,
    )

    class Meta:
        model = RegistroAjusteLoa
        fields = [
            "parlamentares__valor",
            "tipo",
            "emendaloa",
            "unidade",
            "entidade",
            "descricao",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.oficioajusteloa = kwargs["initial"]["oficioajusteloa"]
        self.parlamentares = self.oficioajusteloa.parlamentares.all()

        self.emendas = set()
        for p in self.parlamentares:
            emendas = p.emendaloaparlamentar_set.filter(
                emendaloa__loa=self.oficioajusteloa.loa
            ).order_by("-emendaloa__tipo", "emendaloa__materia")
            self.emendas.update(map(lambda e: e.emendaloa, emendas))

        self.fields["emendaloa"].choices = [("", "---------")] + [
            (e.pk, f'{e.materia.epigrafe_short if e.materia else ""} - {e}')
            for e in self.emendas
        ]

        self.fields["unidade"].choices = [
            (u.id, str(u))
            for u in UnidadeOrcamentaria.objects.filter(
                loa=self.oficioajusteloa.loa, recebe_emenda_impositiva=True
            )
        ]

        self.fields["entidade"].choices = [("", "---------")] + [
            (e.id, str(e))
            for e in Entidade.objects.filter(ativo=True).order_by("nome_fantasia")
        ]

        initial_pv = []
        if self.instance.pk:
            initial_pv = [[p, Decimal("0.00")] for p in self.parlamentares]
            for i, (p, v) in enumerate(initial_pv):
                ipv = p.registroajusteloaparlamentar_set.filter(
                    registro=self.instance
                ).first()
                if ipv:
                    initial_pv[i][1] = ipv.valor
        self.initial["parlamentares__valor"] = list(map(lambda x: x[1], initial_pv))

        fpv = self.fields["parlamentares__valor"]
        fpv.max_length = self.parlamentares.count()
        fpv.size = self.parlamentares.count()
        fpv.widget = EmendaLoaValorWidget(
            widget=self.fields["parlamentares__valor"].base_field.widget,
            parlamentares=list(self.parlamentares),
            user=None,
            attrs={"class": "text-right"},
            instance=self.instance,
        )

    def save(self, commit=True):

        i_init = self.instance

        # soma = sum(list(filter(lambda x: x, self.cleaned_data["parlamentares__valor"])))
        try:
            i = super().save(commit)
        except Exception as e:
            raise ValidationError("Erro")

        i.parlamentares_valor.clear()

        pv = zip(self.parlamentares, self.cleaned_data["parlamentares__valor"])

        for p, v in pv:
            r = RegistroAjusteLoaParlamentar()
            r.registro = i
            r.parlamentar = p
            r.valor = v
            r.save()

        return i
