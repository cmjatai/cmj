import logging
from decimal import Decimal

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Fieldset
from django import forms
from django.forms.models import ModelForm
from django.forms.widgets import TextInput
from django.utils.translation import gettext_lazy as _

from cmj.loa.models import Agrupamento, EmendaLoa
from cmj.utils import DecimalField
from sapl.crispy_layout_mixin import SaplFormLayout, to_row

logger = logging.getLogger(__name__)


class AgrupamentoForm(ModelForm):

    busca_emendaloa = forms.CharField(
        label="Procurar por emendas cadastradas",
        required=False,
    )

    busca_despesa = forms.CharField(
        label="Buscar",
        required=False,
        widget=TextInput(attrs={"autocomplete": "off", "type": "search"}),
    )

    perc_despesa = DecimalField(
        label="Percentual da Despesa",
        required=False,
        max_digits=5,
        decimal_places=2,
    )

    despesa_codigo = forms.CharField(label="Código", required=False)

    despesa_orgao = forms.CharField(
        label="Orgão",
        required=False,
    )
    despesa_unidade = forms.CharField(
        label="Unidade",
        required=False,
    )

    despesa_especificacao = forms.CharField(
        label="Descrição da Ação",
        required=False,
    )

    despesa_natureza = forms.CharField(
        label="Natureza",
        required=False,
    )

    despesa_fonte = forms.CharField(
        label="Fonte",
        required=False,
    )

    ano_loa = forms.CharField(label="", widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Agrupamento
        fields = [
            "nome",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs["initial"].pop("user", None)
        self.loa = kwargs["initial"]["loa"]
        self.full_editor = full_editor = (
            self.user.has_perm("loa.emendaloa_full_editor")
            and not self.user.is_superuser
        )

        row1 = to_row(
            [
                ("nome", 12),
                ("ano_loa", 0),
            ]
        )

        row4_1 = to_row(
            [
                ("busca_despesa", 3),
                ("despesa_orgao", 2),
                ("despesa_unidade", 2),
                ("despesa_natureza", 3),
                ("despesa_fonte", 2),
            ]
        )
        row4_2 = to_row(
            [
                ("perc_despesa", 2),
                ("despesa_codigo", 3),
                ("despesa_especificacao", "col-4"),
                (
                    Div(
                        HTML("""
                <button type="button" id="clean_form_search" class="btn btn-secondary" title="Limpar Formulário de Busca">
                    <i class="fas fa-backspace"></i>
                </button>
                <button type="button" id="add_registro" class="btn btn-primary" title="Adicionar Registro Contábil">
                    <i class="fas fa-plus-circle"></i>
                </button>
            """),
                        css_class="btn-group btn-group",
                    ),
                    "col-2",
                ),
                (Div(css_class="busca-render"), 12),
            ]
        )

        row4_3 = to_row(
            [
                (Div(css_class="registro-render"), 12),
            ]
        )

        row4 = to_row(
            [
                (
                    Fieldset(
                        _("Registrar Deduções e Inserções"),
                        row4_1,
                        row4_2,
                        css_class="fieldset-busca-registrocontabil",
                    ),
                    12,
                ),
                (Fieldset(_("Registros das Despesas Orçamentárias"), row4_3), 12),
            ]
        )

        row5_1 = to_row(
            [
                ("busca_emendaloa", 12),
                (Div(css_class="busca-render-emendaloa"), 12),
            ]
        )

        row5_2 = to_row(
            [
                (Div(css_class="emendaloa-selecteds"), 12),
            ]
        )

        row5 = to_row(
            [
                (Fieldset(_("Busca por Emendas "), row5_1), 7),
                (Fieldset(_("Emendas Selecionadas"), row5_2), 5),
            ]
        )

        super().__init__(*args, **kwargs)

        btns = {}
        if self.instance.pk:
            btns = {
                "cancel_label": "Encerrar Edição",
                "save_label": "Encerrar Edição e Concluir Registro Contábil",
            }

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_("Dados Gerais"), row1), row4, row5, **btns
        )

        self.initial["ano_loa"] = self.loa.ano
        self.initial["perc_despesa"] = Decimal("100.00")

    def save(self, commit=False):
        if not self.instance.pk:
            return ModelForm.save(self, commit=commit)

        for e in self.instance.emendas.all():
            if e.fase < EmendaLoa.LIBERACAO_CONTABIL:
                e.fase = 17
            e.save()

        return self.instance
