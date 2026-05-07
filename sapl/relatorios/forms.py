import django_filters
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import HTML, Button, Fieldset, Layout, Submit
from django import forms
from django.utils.translation import gettext_lazy as _

from sapl.crispy_layout_mixin import (
    SaplFormHelper,
    to_row,
)
from sapl.materia.models import (
    MateriaLegislativa,
)
from sapl.sessao.models import SessaoPlenaria, TipoSessaoPlenaria
from sapl.utils import (
    FilterOverridesMetaMixin,
    autor_label,
    autor_modal,
    qs_override_django_filter,
)


class RelatorioMateriasPorAutorFilterSet(django_filters.FilterSet):

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    # @property
    # def qs(self):
    #    parent = super().qs
    # return parent.order_by('autoria__autor', '-ano',
    # 'tipo__sequencia_regimental', '-numero').distinct()

    @property
    def qs(self):
        qs = super().qs
        return qs.select_related("tipo").order_by(
            "tipo__sequencia_regimental", "-numero"
        )

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ["tipo", "data_apresentacao"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters["tipo"].label = "Tipo de Matéria"

        row1 = to_row([("tipo", 12)])
        row2 = to_row([("data_apresentacao", 12)])
        row3 = to_row(
            [
                ("autoria__autor", 0),
                (
                    Button(
                        "pesquisar",
                        "Pesquisar Autor",
                        css_class="btn btn-primary btn-sm",
                    ),
                    2,
                ),
                (
                    Button(
                        "limpar", "limpar Autor", css_class="btn btn-primary btn-sm"
                    ),
                    10,
                ),
            ]
        )

        buttons = FormActions(
            *[HTML("""
                        <div class="form-check">
                            <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                            <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                        </div>
                    """)],
            Submit(
                "pesquisar",
                _("Pesquisar"),
                css_class="float-right",
                onclick="return true;",
            ),
            css_class="form-group row justify-content-between",
        )
        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = "GET"
        self.form.helper.layout = Layout(
            Fieldset(
                _("Pesquisar"),
                row1,
                row2,
                HTML(autor_label),
                HTML(autor_modal),
                row3,
                buttons,
            )
        )


class BtnSubmit(Submit):
    field_classes = "btn"


class RelatorioPresencaSessaoFilterSet(django_filters.FilterSet):

    class Meta(FilterOverridesMetaMixin):
        model = SessaoPlenaria
        fields = ["data_inicio", "sessao_legislativa", "tipo", "legislatura"]

        class Form(forms.Form):
            crispy_field_template = [
                "data_inicio",
                "sessao_legislativa",
                "tipo",
                "legislatura",
            ]

            def clean_data_inicio(self, *args, **kwargs):
                data_inicio = self.cleaned_data.get("data_inicio")
                if data_inicio and data_inicio.start and data_inicio.stop:
                    start_data = data_inicio.start
                    stop_data = data_inicio.stop
                    if start_data > stop_data:
                        raise forms.ValidationError(
                            _("A data inicial deve ser menor ou igual à data final.")
                        )
                    return data_inicio
                return data_inicio

            def clean(self):
                cleaned_data = super().clean()
                data_inicio = cleaned_data.get("data_inicio")
                sessao_legislativa = cleaned_data.get("sessao_legislativa")
                legislatura = cleaned_data.get("legislatura")

                if data_inicio and sessao_legislativa:
                    start_data = (
                        data_inicio.start.date()
                        if data_inicio.start
                        else sessao_legislativa.data_inicio
                    )
                    stop_data = (
                        data_inicio.stop.date()
                        if data_inicio.stop
                        else sessao_legislativa.data_fim
                    )
                    # Verifica se o intervalo de datas está dentro do intervalo da sessão legislativa

                    if (
                        start_data < sessao_legislativa.data_inicio
                        or stop_data > sessao_legislativa.data_fim
                        or start_data > sessao_legislativa.data_fim
                        or stop_data < sessao_legislativa.data_inicio
                    ):
                        raise forms.ValidationError(
                            _(
                                "O período deve estar dentro do intervalo da Sessão Legislativa {} ({} - {})."
                            ).format(
                                sessao_legislativa.nome,
                                sessao_legislativa.data_inicio.strftime("%d/%m/%Y"),
                                sessao_legislativa.data_fim.strftime("%d/%m/%Y"),
                            )
                        )

                if data_inicio and legislatura:
                    start_data = (
                        data_inicio.start.date()
                        if data_inicio.start
                        else legislatura.data_inicio
                    )
                    stop_data = (
                        data_inicio.stop.date()
                        if data_inicio.stop
                        else legislatura.data_fim
                    )
                    # Verifica se o intervalo de datas está dentro do intervalo da legislatura

                    if (
                        start_data < legislatura.data_inicio
                        or stop_data > legislatura.data_fim
                        or start_data > legislatura.data_fim
                        or stop_data < legislatura.data_inicio
                    ):
                        raise forms.ValidationError(
                            _(
                                "O período deve estar dentro do intervalo da Legislatura {} ({} - {})."
                            ).format(
                                legislatura.nome,
                                legislatura.data_inicio.strftime("%d/%m/%Y"),
                                legislatura.data_fim.strftime("%d/%m/%Y"),
                            )
                        )
                return cleaned_data

        form = Form

    def __init__(self, *args, **kwargs):
        super(RelatorioPresencaSessaoFilterSet, self).__init__(*args, **kwargs)

        self.form.fields["data_inicio"].label = "Período (Inicial - Final)"

        # la = Legislatura.cache_legislatura_atual()
        # if la:
        #    self.form.initial["legislatura"] = la["id"]
        self.form.fields["legislatura"].required = True

        self.form.initial["relatorio"] = False
        self.form.fields["relatorio"] = forms.BooleanField(
            required=False, label="Gerar relatório PDF"
        )

        row1 = to_row([("legislatura", 4), ("sessao_legislativa", 4), ("tipo", 4)])
        row2 = to_row([("data_inicio", 12)])
        row3 = to_row(
            [
                ("relatorio", "col-auto"),
                (
                    BtnSubmit(
                        "pesquisar",
                        "Pesquisar",
                        css_class="btn-primary",
                    ),
                    "col-auto",
                ),
            ],
            css_class="row justify-content-end align-items-center",
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = "GET"
        self.form.helper.layout = Layout(
            row1,
            row2,
            row3,
        )

        self.form.fields["tipo"].queryset = self.form.fields["tipo"].queryset.filter(
            tipogeral=TipoSessaoPlenaria.TIPOGERAL_SESSAO
        )

    @property
    def qs(self):
        return qs_override_django_filter(self).filter(
            tipo__tipogeral=TipoSessaoPlenaria.TIPOGERAL_SESSAO,
            iniciada=True,
            finalizada=True,
        )
