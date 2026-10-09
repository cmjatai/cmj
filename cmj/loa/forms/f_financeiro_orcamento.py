import logging

from crispy_forms.layout import Fieldset
from django import forms
from django.utils.translation import gettext_lazy as _

from cmj.loa.models import UnidadeOrcamentaria
from cmj.loa.models.m_ajusteloa import RegistroAjusteLoa
from cmj.loa.models.m_emendaloa import EmendaLoa
from cmj.loa.models.m_financeiro_execucao import DespesaPaga, Empenho
from cmj.loa.models.m_financeiro_orcamento import Despesa, Orgao, ReceitaOrcamentaria
from sapl.crispy_layout_mixin import SaplFormHelper, SaplFormLayout, to_row

logger = logging.getLogger(__name__)


class OrgaoForm(forms.ModelForm):

    outros_orgaos = forms.ModelMultipleChoiceField(
        queryset=Orgao.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Outros Orgãos"),
    )

    class Meta:
        model = Orgao
        fields = (
            "codigo",
            "especificacao",
        )
        widgets = {
            "codigo": forms.TextInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(
                _("Orgão"),
                to_row(
                    [
                        ("codigo", 3),
                        ("especificacao", 9),
                        ("outros_orgaos", 12),
                    ]
                ),
            ),
        )
        self.fields["outros_orgaos"].choices = [
            (orgao.pk, f"{orgao}")
            for orgao in Orgao.objects.filter(loa=self.instance.loa)
            .exclude(pk=self.instance.pk)
            .order_by("codigo")
        ]

    def save(self, commit=True):
        instance = super().save(commit=commit)
        outros_orgaos_a_substituir = self.cleaned_data["outros_orgaos"]

        models_a_substituir = (
            (UnidadeOrcamentaria, "orgao"),
            (ReceitaOrcamentaria, "orgao"),
            (DespesaPaga, "orgao"),
            (Empenho, "orgao"),
            (Despesa, "orgao"),
        )
        for model, field in models_a_substituir:
            for item in model.objects.filter(
                **{f"{field}__in": outros_orgaos_a_substituir}
            ):
                setattr(item, field, self.instance)
                item.save()
        try:
            for orgao in outros_orgaos_a_substituir:
                orgao.delete()
        except Exception as e:
            logger.error(f"Erro ao excluir orgãos substituídos: {e}")
        return instance


class UnidadeOrcamentariaForm(forms.ModelForm):

    outras_unidades = forms.ModelMultipleChoiceField(
        queryset=UnidadeOrcamentaria.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Outras Unidades"),
    )

    class Meta:
        model = UnidadeOrcamentaria
        fields = (
            "codigo",
            "especificacao",
            "recebe_emenda_impositiva",
            "orgao",
            "area",
            "outras_unidades",
        )
        widgets = {
            "codigo": forms.TextInput,
            "outras_unidades": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [
                ("codigo", 2),
                ("especificacao", 4),
                ("orgao", 4),
                ("recebe_emenda_impositiva", 2),
                ("area", 6),
                ("outras_unidades", 12),
            ]
        )
        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(
                _("Unidade Orçamentária"),
                row1,
            )
        )
        super().__init__(*args, **kwargs)
        self.fields["outras_unidades"].choices = [
            (uo.pk, f"{uo} ({uo.orgao})")
            for uo in UnidadeOrcamentaria.objects.filter(loa=self.instance.loa)
            .exclude(pk=self.instance.pk)
            .order_by("codigo")
        ]

    def save(self, commit=True):
        instance = super().save(commit=commit)
        unidades_a_substituir = self.cleaned_data["outras_unidades"]

        models_a_substituir = (
            (RegistroAjusteLoa, "unidade"),
            (EmendaLoa, "unidade"),
            (DespesaPaga, "unidade"),
            (Empenho, "unidade"),
            (Despesa, "unidade"),
        )
        for model, field in models_a_substituir:
            for item in model.objects.filter(**{f"{field}__in": unidades_a_substituir}):
                setattr(item, field, self.instance)
                if hasattr(item, "orgao"):
                    item.orgao = self.instance.orgao
                item.save()
        try:
            for uo in unidades_a_substituir:
                uo.delete()
        except Exception as e:
            logger.error(f"Erro ao excluir unidades orçamentárias substituídas: {e}")
        return instance
