import logging
from decimal import Decimal

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Fieldset
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.forms.widgets import TextInput
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from cmj.loa.models import Agrupamento, EmendaLoa
from cmj.utils import DecimalField
from sapl.crispy_layout_mixin import SaplFormLayout, form_actions, to_row

logger = logging.getLogger(__name__)


class AgrupamentoForm(ModelForm):

    busca_emendaloa = forms.CharField(
        label="Procurar por emendas cadastradas",
        required=False,
        widget=TextInput(attrs={"autocomplete": "off", "type": "search"}),
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

    finalidade = forms.CharField(
        label="Finalidade",
        required=False,
        help_text='Inserções ou remoções de Emenda geram "finalidade" automaticamente quando não há multiplicidade de Unidades e Entidades.'
        " Dê Ctrl+Clique para atualização por I.A. Sem Texto a I.A. criará Finalidade Automática quando for possível. Edição manual só é mantida ao final das inserções ou remoções de Emenda.",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = Agrupamento
        fields = ["nome", "finalidade", "tipo"]
        widgets = {"tipo": forms.RadioSelect()}

    def __init__(self, *args, **kwargs):
        self.user = kwargs["initial"].pop("user", None)
        self.loa = kwargs["initial"]["loa"]
        self.full_editor = full_editor = (
            self.user.has_perm("loa.emendaloa_full_editor")
            and not self.user.is_superuser
        )

        super().__init__(*args, **kwargs)

        agrupamento = self.instance

        row1 = to_row(
            [
                ("nome", 4),
                (
                    "tipo",
                    "col-auto",
                ),
                (
                    Div(
                        Div(
                            HTML("""
                                    <button type="button" id="create_copia_agrupamento" class="btn btn-secondary" title="Criar Cópia deste Agrupamento">
                                        <i class="fas fa-copy"></i>
                                    </button>
                                """),
                            css_class="btn-group btn-group mr-4",
                        ),
                        Div(
                            HTML(f"""
                                    <a href="{reverse('sapl.api:loa_agrupamento-view', args=[agrupamento.id])}?model=1" target="_blank" id="preview_m1" class="btn btn-secondary" title="Pre-visualização Modelo 1">
                                        <i class="fas fa-eye"></i>
                                    </a>
                                """),
                            css_class="btn-group btn-group mr-4",
                        ),
                        Div(
                            HTML(f"""
                                    <a href="#" id="cancelar_emendas_coletivas" class="btn btn-danger" title="Cancelar Emendas Coletivas e/ou reverter para edição">
                                        <i class="fas fa-arrow-rotate-left"></i>
                                    </a>
                                    <a href="#" id="gerar_emenda_coletiva" class="btn btn-success" title="Gerar Emendas Coletivas">
                                        <i class="fas fa-file-circle-plus"></i>
                                    </a>
                                """),
                            css_class="btn-group btn-group mr-4",
                        ),
                        Div(
                            HTML(f"""
                                    <a href="{reverse('cmj.loa:agrupamento_detail', args=[agrupamento.id])}" id="cancelar" class="btn btn-secondary" title="Fechar Edição">
                                        <i class="fas fa-times"></i>
                                    </a>
                                    <button type="submit" class="btn btn-primary" title="Liberar para Protocolo">
                                        <i class="fas fa-check"></i>
                                    </button>
                                """),
                            css_class="btn-group btn-group",
                        ),
                    ),
                    "col-auto d-flex align-items-start justify-content-start",
                ),
                ("finalidade", 12),
                ("ano_loa", 0),
            ]
        )

        """
            <a href="{reverse('sapl.api:loa_agrupamento-view', args=[agrupamento.id])}?model=1" target="_blank" id="preview_m1" class="btn btn-secondary" title="Previsualização Modelo 1">
                M1
            </a>
            <a href="{reverse('sapl.api:loa_agrupamento-view', args=[agrupamento.id])}?model=2" target="_blank" id="preview_m2" class="btn btn-secondary" title="Previsualização Modelo 2">
                M2
            </a>
            <a href="{reverse('sapl.api:loa_agrupamento-view', args=[agrupamento.id])}?model=3" target="_blank" id="preview_m3" class="btn btn-secondary" title="Previsualização Modelo 3">
                M3
            </a>
            <a href="{reverse('sapl.api:loa_agrupamento-view', args=[agrupamento.id])}?model=4" target="_blank" id="preview_m4" class="btn btn-secondary" title="Previsualização Modelo 4">
                M4
            </a>
        """

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

        actions = None
        if self.instance.pk:
            actions = form_actions(
                label="Encerrar Edição e Concluir Registro Contábil",
                more=[
                    HTML(
                        '<a href="{{ view.cancel_url }}"'
                        ' class="btn btn-inverse">Encerrar Edição</a>'
                    ),
                ],
            )

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_("Dados Gerais"), row1), row4, row5, actions=[]
        )

        self.initial["ano_loa"] = self.loa.ano
        self.initial["perc_despesa"] = Decimal("100.00")

    def clean(self):
        cleaned_data = super().clean()
        # acessar os registros contabeis de agrupamentos e verificar se percentual soma zero
        agrupamentos_contabeis = (
            self.instance.agrupamentoregistrocontabil_set.values_list(
                "percentual", flat=True
            )
        )
        soma_zero = sum(agrupamentos_contabeis)
        if soma_zero != 0:
            raise ValidationError(
                _(
                    "O percentual dos registros contábeis do agrupamento deve somar zero."
                )
            )
        if not agrupamentos_contabeis:
            raise ValidationError(
                _("Nenhum agrupamento contábil foi encontrado para validação.")
            )
        return cleaned_data

    def save(self, commit=False):
        if not self.instance.pk:
            return ModelForm.save(self, commit=commit)

        try:
            # self.instance.gerar_emendas_coletivas()

            # self.instance.refresh_from_db()
            # emendas.all() puxará apenas as emendas que não passaram para a fase TRANSFORMADA_EM_COLETIVA
            # ou seja, emendas com permitir_juncao_coletiva=False não foram transformadas em coletivas
            # e são simplesmente aqui liberadas para a fase de LIBERACAO_CONTABIL
            for e in self.instance.emendas.all():
                if 0 < e.fase < EmendaLoa.LIBERACAO_CONTABIL:
                    e.fase = EmendaLoa.LIBERACAO_CONTABIL
                e._usuario_fase = self.user  # LOA-FASE-067
                e.save()

            for e in self.instance.emendas_coletivas_geradas.all():
                if 0 < e.fase < EmendaLoa.LIBERACAO_CONTABIL:
                    e.fase = EmendaLoa.LIBERACAO_CONTABIL
                e._usuario_fase = self.user  # LOA-FASE-067
                e.save()

        except Exception as e:
            raise e

        return self.instance
