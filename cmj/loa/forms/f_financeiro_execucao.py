import logging

from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext_lazy as _

from cmj.loa.models.m_ajusteloa import RegistroAjusteLoa
from cmj.loa.models.m_emendaloa import EmendaLoa
from cmj.loa.models.m_financeiro_execucao import Empenho
from cmj.utils import DecimalField

logger = logging.getLogger(__name__)


class WidgetSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        placeholder = kwargs.pop("placeholder", "")
        super().__init__(*args, **kwargs)
        self.attrs.update(
            {
                "title": placeholder or _("Selecione uma opção"),
                "class": "selectpicker w-100",
                "data-live-search": "true",
                "data-placeholder": placeholder or _("Selecione uma opção"),
                "data-dropup-auto": "false",
            }
        )


class EmpenhoForm(forms.ModelForm):

    valor_empenhado = DecimalField(
        label="Valor Empenhado",
        required=True,
        max_digits=14,
        decimal_places=2,
    )

    valor_anulado = DecimalField(
        label="Valor Anulado",
        required=False,
        max_digits=14,
        decimal_places=2,
    )

    valor_liquidado = DecimalField(
        label="Valor Liquidado",
        required=False,
        max_digits=14,
        decimal_places=2,
    )

    valor_pago_bruto = DecimalField(
        label="Valor Pago Bruto",
        required=False,
        max_digits=14,
        decimal_places=2,
    )

    emendas = forms.ModelMultipleChoiceField(
        queryset=EmendaLoa.objects.all(),
        label="Emendas da LOA",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "title": "Selecione as emendas relacionadas ao Empenho",
                "class": "selectpicker w-100",
                "data-actions-box": "true",
                "data-select-all-text": "Selecionar Todos",
                "data-deselect-all-text": "Desmarcar Todos",
                "data-live-search": "true",
                "data-header": "Emendas Cadastradas",
                "data-dropup-auto": "true",
            }
        ),
    )

    ajustes = forms.ModelMultipleChoiceField(
        queryset=RegistroAjusteLoa.objects.all(),
        label="Registros de Ajuste da LOA",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "title": "Selecione os registros de ajuste relacionados ao Empenho",
                "class": "selectpicker w-100",
                "data-actions-box": "true",
                "data-select-all-text": "Selecionar Todos",
                "data-deselect-all-text": "Desmarcar Todos",
                "data-live-search": "true",
                "data-header": "Registros de Ajuste Cadastrados",
                "data-dropup-auto": "true",
            }
        ),
    )

    class Meta:
        model = Empenho
        fields = "__all__"
        widgets = {
            "processo": forms.widgets.TextInput(),
            "numero_licitacao": forms.widgets.TextInput(),
            "modalidade": forms.widgets.TextInput(),
            "dotacao": forms.widgets.TextInput(),
            "cpfcnpj": forms.widgets.TextInput(),
            "nome": forms.widgets.TextInput(),
            "programa": WidgetSelect(placeholder="Selecione um programa"),
            "acao": WidgetSelect(placeholder="Selecione uma ação"),
            "natureza": WidgetSelect(placeholder="Selecione uma natureza"),
            "fonte": WidgetSelect(placeholder="Selecione uma fonte"),
        }

    def __init__(self, *args, **kwargs):
        self.loa = kwargs["initial"].pop("loa", None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()

        # orgao, unidade, funcao, subfuncao, programa, acao, natureza, fonte são filtrados pela LOA
        fields_filter_loa = [
            "orgao",
            "unidade",
            "funcao",
            "subfuncao",
            "programa",
            "acao",
            "natureza",
            "fonte",
        ]
        for field in fields_filter_loa:
            self.fields[field].queryset = self.fields[field].queryset.filter(
                loa=self.loa
            )

        self.fields["natureza"].choices = [("", "---------")] + [
            (n.pk, f"{n.codigo} - {n.especificacao} ({n.codigo.replace('.', '')})")
            for n in self.fields["natureza"].queryset.order_by("codigo")
        ]

        self.fields["emendas"].queryset = (
            self.fields["emendas"]
            .queryset.filter(loa=self.loa)
            .exclude(tipo=EmendaLoa.MODIFICATIVA)
            .order_by("materia__numero")
        )
        self.fields["ajustes"].queryset = self.fields["ajustes"].queryset.filter(
            oficio_ajuste_loa__loa=self.loa
        )

        self.fields["emendas"].choices = (
            [("", "---------")]
            + [
                (
                    e.pk,
                    f"{e.str_short} - {', '.join([p.nome_parlamentar.upper() for p in e.parlamentares.all()])} - {e.ementa_format}",
                )
                for e in self.fields["emendas"]
                .queryset.filter(id__in=kwargs["initial"].get("emendas", []))
                .order_by("materia__numero")
            ]
            + [
                (
                    e.pk,
                    f"{e.str_short} - {', '.join([p.nome_parlamentar.upper() for p in e.parlamentares.all()])} - {e.ementa_format}",
                )
                for e in self.fields["emendas"]
                .queryset.exclude(id__in=kwargs["initial"].get("emendas", []))
                .order_by("materia__numero")
            ]
        )

        self.fields["ajustes"].choices = (
            [("", "---------")]
            + [
                (
                    r.pk,
                    f'{r.oficio_ajuste_loa.epigrafe if r.oficio_ajuste_loa else ""} - {r.str_valor} - {str(r.descricao)}',
                )
                for r in self.fields["ajustes"]
                .queryset.filter(id__in=kwargs["initial"].get("ajustes", []))
                .order_by("parlamentares_valor", "descricao")
            ]
            + [
                (
                    r.pk,
                    f'{r.oficio_ajuste_loa.epigrafe if r.oficio_ajuste_loa else ""} - {r.str_valor} - {str(r.descricao)}',
                )
                for r in self.fields["ajustes"]
                .queryset.exclude(id__in=kwargs["initial"].get("ajustes", []))
                .order_by("parlamentares_valor", "descricao")
            ]
        )
        if self.instance.pk:
            self.fields["codigo"].widget.attrs["readonly"] = True

    def save(self, commit=True):
        instance = super().save(commit=False)

        if not instance.id:
            instance.id = instance.codigo
        instance.save()

        instance.empenhoemendaajuste_set.all().delete()

        for emenda in self.cleaned_data["emendas"]:
            instance.empenhoemendaajuste_set.create(emendaloa=emenda)
        for ajuste in self.cleaned_data["ajustes"]:
            instance.empenhoemendaajuste_set.create(ajuste=ajuste)

        return instance
