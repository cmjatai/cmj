import django_filters
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import HTML, Button, Fieldset, Layout, Submit
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sapl.crispy_layout_mixin import (
    SaplFormHelper,
    form_actions,
    to_row,
)
from sapl.materia.models import (
    MateriaLegislativa,
)
from sapl.parlamentares.models import (
    Legislatura,
    SessaoLegislativa,
)
from sapl.sessao.models import SessaoPlenaria
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


class RelatorioPresencaSessaoFilterSet(django_filters.FilterSet):

    class Meta(FilterOverridesMetaMixin):
        model = SessaoPlenaria
        fields = ["data_inicio", "sessao_legislativa", "tipo", "legislatura"]

    def __init__(self, *args, **kwargs):
        super(RelatorioPresencaSessaoFilterSet, self).__init__(*args, **kwargs)

        self.form.fields["exibir_ordem_dia"] = forms.BooleanField(
            required=False, label="Exibir presença das Ordens do Dia"
        )
        self.form.initial["exibir_ordem_dia"] = True

        self.filters["data_inicio"].label = "Período (Inicial - Final)"

        now = timezone.now()
        self.form.initial["legislatura"] = Legislatura.objects.filter(
            data_inicio__lte=now, data_fim__gte=now
        ).first()

        if self.form.initial["legislatura"]:
            self.form.initial["sessao_legislativa"] = SessaoLegislativa.objects.filter(
                legislatura=self.form.initial["legislatura"],
                data_inicio__lte=now,
                data_fim__gte=now,
            ).first()

        self.form.initial["tipo"] = (
            self.filters["tipo"].queryset.filter(nome__endswith=" Ordinária").first()
        )

        row1 = to_row([("data_inicio", 12)])
        row2 = to_row([("legislatura", 4), ("sessao_legislativa", 4), ("tipo", 4)])
        row3 = to_row([("exibir_ordem_dia", 12)])

        self.form.fields["legislatura"].required = True
        # self.form.fields['data_inicio'].required = True
        self.form.fields["tipo"].required = True
        self.form.fields["sessao_legislativa"].required = True

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = "GET"
        self.form.helper.layout = Layout(
            Fieldset(
                _("Presença dos parlamentares nas sessões plenárias"),
                row2,
                row1,
                row3,
                form_actions(label="Pesquisar"),
            )
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)
