import logging

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.utils.translation import gettext_lazy as _

from cmj.loa.models import (
    ArquivoPrestacaoContaLoa,
    ArquivoPrestacaoContaRegistro,
    EmendaLoa,
    PrestacaoContaLoa,
    PrestacaoContaRegistro,
    RegistroAjusteLoa,
)

logger = logging.getLogger(__name__)


class PrestacaoContaLoaForm(ModelForm):

    arquivos_cadastrados = forms.ModelMultipleChoiceField(
        label="Arquivos da Prestação de Contas",
        queryset=ArquivoPrestacaoContaLoa.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Desmarque para excluir arquivos vinculados à prestação de contas.",
    )

    arquivos = forms.FileField(required=False, label=_("Arquivos para Upload"))

    data_envio = forms.DateField(label="Data de Envio", required=True)

    class Meta:
        model = PrestacaoContaLoa
        fields = [
            "data_envio",
            "epigrafe",
            "arquivos",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["arquivos_cadastrados"].queryset = (
                ArquivoPrestacaoContaLoa.objects.filter(prestacao_conta=self.instance)
            )
            self.fields["arquivos_cadastrados"].initial = self.fields[
                "arquivos_cadastrados"
            ].queryset
        else:
            self.fields["arquivos_cadastrados"].queryset = (
                ArquivoPrestacaoContaLoa.objects.none()
            )

        self.fields["arquivos"].widget.attrs.update({"multiple": "multiple"})

    def save(self, commit=...):
        inst = super().save(commit)

        new_files = []
        if "arquivos" in self.files:
            for f in self.files.getlist("arquivos"):
                a = ArquivoPrestacaoContaLoa()
                a.prestacao_conta = inst
                a.arquivo = f
                a.descricao = f.name
                a.save()
                new_files.append(a.id)

        # remove arquivos não selecionados
        if inst.pk:
            arquivos_selecionados = self.cleaned_data.get("arquivos_cadastrados")
            for a in inst.arquivoprestacaocontaloa_set.exclude(id__in=new_files):
                if a not in arquivos_selecionados:
                    a.delete()

        return inst


class PrestacaoContaRegistroForm(ModelForm):

    arquivos_cadastrados = forms.ModelMultipleChoiceField(
        label="Arquivos do Registro da Prestação de Contas",
        queryset=ArquivoPrestacaoContaRegistro.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Desmarque para excluir arquivos vinculados ao registro da prestação de contas.",
    )

    arquivos = forms.FileField(required=False, label=_("Arquivos para Upload"))

    registro_ajuste = forms.ModelChoiceField(
        queryset=RegistroAjusteLoa.objects.all(),
        label="Registro de Ajuste Técnico",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "selectpicker",
                "data-live-search": "true",
                "data-header": "Registros Técnicos Cadastrados",
                "data-dropup-auto": "false",
            }
        ),
    )

    emendaloa = forms.ModelChoiceField(
        queryset=EmendaLoa.objects.all(),
        label="Emendas da LOA",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "selectpicker",
                "data-live-search": "true",
                "data-header": "Emendas Cadastradas",
                "data-dropup-auto": "false",
            }
        ),
    )

    class Meta:
        model = PrestacaoContaRegistro
        fields = [
            "registro_ajuste",
            "situacao",
            "emendaloa",
            "detalhamento",
            "arquivos",
        ]

    def __init__(self, *args, **kwargs):
        loa = kwargs["initial"].pop("loa")
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["arquivos_cadastrados"].queryset = (
                ArquivoPrestacaoContaRegistro.objects.filter(registro=self.instance)
            )
            self.fields["arquivos_cadastrados"].initial = self.fields[
                "arquivos_cadastrados"
            ].queryset
        else:
            self.fields["arquivos_cadastrados"].queryset = (
                ArquivoPrestacaoContaRegistro.objects.none()
            )

        self.fields["arquivos"].widget.attrs.update({"multiple": "multiple"})

        self.fields["emendaloa"].queryset = EmendaLoa.objects.filter(loa=loa)
        self.fields["registro_ajuste"].queryset = RegistroAjusteLoa.objects.filter(
            oficio_ajuste_loa__loa=loa
        )

        self.fields["emendaloa"].choices = [("", "---------")] + [
            (
                e.pk,
                f'{e.materia.epigrafe_short if e.materia else ""} - {str(e.unidade)} - {str(e)[:100]}',
            )
            for e in self.fields["emendaloa"].queryset
        ]

        self.fields["registro_ajuste"].choices = [("", "---------")] + [
            (
                r.pk,
                f'{r.oficio_ajuste_loa.epigrafe if r.oficio_ajuste_loa else ""} - {r.str_valor} - {str(r.descricao)[:100]}',
            )
            for r in self.fields["registro_ajuste"].queryset
        ]

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("registro_ajuste") and not cleaned_data.get(
            "emendaloa"
        ):
            raise ValidationError(
                "Você deve selecionar um Registro de Ajuste Técnico ou uma Emenda da LOA para vincular ao registro da prestação de contas."
            )

        return cleaned_data

    def save(self, commit=...):
        inst = super().save(commit)

        new_files = []
        if "arquivos" in self.files:
            for f in self.files.getlist("arquivos"):
                a = ArquivoPrestacaoContaRegistro()
                a.registro = inst
                a.arquivo = f
                a.descricao = f.name
                a.save()
                new_files.append(a.id)

        # remove arquivos não selecionados
        if inst.pk:
            arquivos_selecionados = self.cleaned_data.get("arquivos_cadastrados")
            for a in inst.arquivoprestacaocontaregistro_set.exclude(id__in=new_files):
                if a not in arquivos_selecionados:
                    a.delete()

        return inst
