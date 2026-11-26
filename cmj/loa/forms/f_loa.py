import logging
from decimal import ROUND_DOWN, Decimal

import yaml
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.utils.translation import gettext_lazy as _

from cmj.loa.forms.f_mixins import MateriaCheckFormMixin
from cmj.loa.models import Despesa, Loa
from cmj.utils import quantize
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Parlamentar

logger = logging.getLogger(__name__)


class LoaForm(MateriaCheckFormMixin, ModelForm):

    tipo_materia = forms.ModelChoiceField(
        label=_("Tipo Matéria"),
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label="Selecione",
    )

    numero_materia = forms.CharField(label="Número Matéria", required=False)

    ano_materia = forms.CharField(label="Ano Matéria", required=False)

    materia = forms.ModelChoiceField(
        required=False,
        widget=forms.HiddenInput(),
        queryset=MateriaLegislativa.objects.all(),
    )

    parlamentares = forms.ModelMultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        queryset=Parlamentar.objects.all(),
    )

    class Meta:
        model = Loa
        fields = [
            "ano",
            "materia",
            "tipo_materia",
            "numero_materia",
            "ano_materia",
            "receita_corrente_liquida",
            "publicado",
            "perc_disp_total",
            "perc_disp_saude",
            "perc_disp_diversos",
            "parlamentares",
            "yaml_obs",
            "despesa_default_deducao_saude",
            "despesa_default_deducao_diversos",
            "despesa_default_deducao_educacao",
            "forcar_detalhamento_de_fonte",
            "responsavel_coletivas",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = self.instance

        parlamentares = self._parlamentares_para_vincular()

        if not instance or not instance.pk or not instance.materia:
            despesa_default_deducao_saude = Despesa.objects.none()
            despesa_default_deducao_diversos = Despesa.objects.none()
            despesa_default_deducao_educacao = Despesa.objects.none()
        else:
            despesa_default_deducao_diversos = Despesa.objects.filter(
                loa=instance, funcao__codigo="99", fonte__codigo__startswith="100"
            ).order_by("fonte__codigo")
            despesa_default_deducao_educacao = Despesa.objects.filter(
                loa=instance,
                funcao__codigo="99",
                fonte__codigo__startswith="101",
            ).order_by("fonte__codigo")
            despesa_default_deducao_saude = Despesa.objects.filter(
                loa=instance,
                funcao__codigo="99",
                fonte__codigo__startswith="102",
            ).order_by("fonte__codigo")

        self.fields["parlamentares"].choices = [(p.pk, p) for p in parlamentares]
        self.fields["despesa_default_deducao_diversos"].queryset = (
            despesa_default_deducao_diversos
        )
        self.fields["despesa_default_deducao_educacao"].queryset = (
            despesa_default_deducao_educacao
        )
        self.fields["despesa_default_deducao_saude"].queryset = (
            despesa_default_deducao_saude
        )
        # LOA-CRUD-072: só quem pode ser dono das Emendas Coletivas
        self.fields["responsavel_coletivas"].queryset = (
            Loa.service.responsaveis_coletivas_elegiveis()
        )

    def _parlamentares_para_vincular(self):
        """LOA-CRUD-020: os que têm mandato na legislatura do projeto ou na do
        ano da LOA, e os já vinculados. Sem ano ou sem mandato registrado, os
        ativos do cadastro."""
        instance = self.instance
        ano = instance.ano if instance and instance.pk else self.data.get("ano")
        try:
            ano = int(ano)
        except (TypeError, ValueError):
            ano = None

        ids = Loa.service.parlamentares_elegiveis(ano) if ano else set()
        if not ids:
            return Parlamentar.objects.filter(ativo=True)
        if instance and instance.pk:
            ids |= set(instance.parlamentares.values_list("id", flat=True))
        return Parlamentar.objects.filter(id__in=ids)

    def clean(self):
        cd = super().clean()

        if not cd:
            cd = self.cleaned_data

        try:
            yo = yaml.safe_load(cd["yaml_obs"])
            # print(yo)
        except Exception as e:
            raise ValidationError("Erro na validação das observações de Rodapé.")

        return cd

    def save(self, commit=True):

        i = self.instance

        i.disp_total = quantize(
            i.receita_corrente_liquida * i.perc_disp_total / Decimal(100),
            rounding=ROUND_DOWN,
        )

        i.disp_saude = quantize(
            i.receita_corrente_liquida * i.perc_disp_saude / Decimal(100),
            rounding=ROUND_DOWN,
        )

        i.disp_diversos = quantize(
            i.receita_corrente_liquida * i.perc_disp_diversos / Decimal(100),
            rounding=ROUND_DOWN,
        )

        if not i.materia or not i.materia.normajuridica():
            i.rcl_previa = i.receita_corrente_liquida

        # if i.disp_diversos + i.disp_saude != i.disp_total:
        #    i.disp_diversos = i.disp_total - i.disp_saude
        #    i.perc_disp_diversos = quantize(
        #        i.disp_diversos / i.receita_corrente_liquida * Decimal(100),
        #        rounding=ROUND_DOWN)

        i = super().save(commit)

        i.update_disponibilidades()

        return i
