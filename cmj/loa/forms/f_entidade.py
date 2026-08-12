import logging

from django import forms
from django.forms.models import ModelForm
from django.utils.translation import gettext_lazy as _

from cmj.loa.models.m_entidade import Entidade, EntidadeLoa

logger = logging.getLogger(__name__)


class EntidadeLoaForm(ModelForm):

    entidade = forms.ModelChoiceField(
        queryset=Entidade.objects.filter(ativo=True),
        label="Entidade",
        required=True,
        widget=forms.Select(
            attrs={
                "class": "selectpicker",
                "data-live-search": "true",
                "data-header": "Entidades Cadastradas",
                "data-dropup-auto": "false",
            }
        ),
    )

    class Meta:
        model = EntidadeLoa
        fields = ["entidade"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.loa = self.initial.get("loa") or self.data.get("loa")
        self.user = self.initial.get("user") or self.data.get("user")

        if self.instance and self.instance.pk:
            self.fields["entidade"].queryset = Entidade.objects.filter(
                pk=self.instance.entidade.pk
            )
        else:
            # Filtrar apenas entidades que não estão associadas a LOA atual.
            # A unique_together do model EntidadeLoa garante que não haverá duplicidade porém,
            # para evitar que o usuário tente cadastrar uma entidade que já está associada a LOA,
            # vamos filtrar as entidades que já estão associadas.

            if self.loa:
                entidades_associadas = EntidadeLoa.objects.filter(
                    loa=self.loa
                ).values_list("entidade_id", flat=True)
                self.fields["entidade"].queryset = Entidade.objects.exclude(
                    pk__in=entidades_associadas
                )
            else:
                self.fields["entidade"].queryset = Entidade.objects.all()
