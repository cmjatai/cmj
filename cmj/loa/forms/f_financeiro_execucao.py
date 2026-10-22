import logging
from datetime import timedelta

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from django import forms
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, ChoiceFilter, FilterSet

from cmj.loa.models.m_financeiro_execucao import Empenho
from cmj.utils import DecimalField
from sapl.crispy_layout_mixin import SaplFormLayout, to_row

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

    busca_emendas_ajustes = forms.CharField(
        label="Associação de Emendas e Ajustes Técnicos",
        required=False,
        help_text="Informe termos para buscar emendas e ajustes relacionados a este empenho. A busca é feita em todos os campos dos Empenhos e a dados ligados às emendas e ajustes técnicos. Use o prefixo '-' para excluir termos da busca. Adições e exclusões são autosaves, ou seja, não é necessário clicar em salvar para que as alterações sejam aplicadas.",
        widget=forms.TextInput(
            attrs={
                "type": "search",
                "placeholder": "Informe termos para buscar emendas e ajustes relacionados a este empenho",
                "title": "Associação de Emendas e Ajustes Técnicos",
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


class EmpenhoFilterSet(FilterSet):

    search = CharFilter(
        label=_("Busca por termos"),
        method="filter_search",
    )

    # criar um choice com periodos: * Ultimos 7 dias, * Ultimo 30 dias, * Ultimo 90 dias, * Ultimo ano, * Tudo
    # default period is "7"
    period = ChoiceFilter(
        label=_("Período"),
        initial="7",
        choices=[
            ("7", _("Últimos 7 dias")),
            ("30", _("Últimos 30 dias")),
            ("90", _("Últimos 90 dias")),
            ("365", _("Último ano")),
        ],
        method="filter_period",
    )

    class Meta:
        model = Empenho
        fields = ["search", "period"]

        class Form(forms.Form):
            crispy_field_template = ("search",)

        form = Form

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset

        terms = value.split()
        if terms:
            if len(terms) == 1 and terms[0].isdigit():
                # Se for um único termo numérico, buscar por número do empenho
                return queryset.filter(codigo=terms[0])

            fq = Q()
            for term in terms:
                if term.startswith("-") and len(term) > 1:
                    fq &= ~Q(search__unaccent__icontains=term[1:])
                else:
                    fq &= Q(search__unaccent__icontains=term)

            queryset = queryset.filter(fq)
        return queryset

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        search_field = FieldWithButtons(
            Field(
                "search", label=_("Busca"), placeholder=_("Informe termos a filtrar...")
            ),
            StrictButton(_("Filtrar"), css_class="btn-secondary", type="submit"),
        )

        row = to_row(
            [
                ("period", 4),
                (search_field, 8),
            ]
        )
        fields = [row]
        self.form.helper = FormHelper()
        self.form.helper.form_method = "get"
        self.form.helper.form_class = "container"
        self.form.helper.layout = SaplFormLayout(*fields, actions=False)

    def filter_period(self, queryset, name, value):
        if value == "7":
            return queryset.filter(created_at__gte=timezone.now() - timedelta(days=7))
        elif value == "30":
            return queryset.filter(created_at__gte=timezone.now() - timedelta(days=30))
        elif value == "90":
            return queryset.filter(created_at__gte=timezone.now() - timedelta(days=90))
        elif value == "365":
            return queryset.filter(created_at__gte=timezone.now() - timedelta(days=365))
        elif value == "all":
            return queryset
        return queryset
