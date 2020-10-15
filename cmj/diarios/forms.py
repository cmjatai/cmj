from crispy_forms.bootstrap import Alert
from crispy_forms.layout import Fieldset, Row, Div
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.forms.models import ModelForm
from django.utils.encoding import force_text

from cmj.diarios.models import VinculoDocDiarioOficial
from sapl.crispy_layout_mixin import SaplFormHelper, SaplFormLayout,\
    to_column
from sapl.utils import ChoiceWithoutValidationField,\
    models_with_gr_for_model


class CustomAttrSelect(forms.widgets.Select):
    def __init__(self, attrs=None, choices=(), modify_choices=()):
        super(CustomAttrSelect, self).__init__(attrs, choices=choices)
        # set data
        self.modify_choices = modify_choices

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super(CustomAttrSelect, self).create_option(
            name, value, label, selected, index, subindex, attrs)

        option['attrs'] = {
            'app_label': option['label'].app_label,
            'model': option['label'].model
        }

        if selected:
            option['attrs']['selected'] = 'selected'

        return option


class VinculoDocDiarioOficialForm(ModelForm):

    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        label=VinculoDocDiarioOficial._meta.get_field(
            'content_type').verbose_name,
        required=True,
        help_text=VinculoDocDiarioOficial._meta.get_field(
            'content_type').help_text,
        widget=CustomAttrSelect())

    tipo = ChoiceWithoutValidationField(
        label="Seleção de Tipo",
        required=False,
        widget=forms.Select())

    numero = forms.CharField(
        label='Número', required=False)

    ano = forms.CharField(
        label='Ano', required=False)

    class Meta:
        model = VinculoDocDiarioOficial
        fields = ('content_type', 'tipo', 'ano', 'numero', 'pagina')

    def __init__(self, *args, **kwargs):

        layout_form = Fieldset(
            VinculoDocDiarioOficial._meta.verbose_name,
            Row(
                to_column(('content_type', 3)),
                to_column(('tipo', 3)),
                to_column(('numero', 2)),
                to_column(('ano', 2)),
                to_column(('pagina', 2)),
            ),
            Alert(
                '',
                css_class="doc_selected hidden alert-info",
                dismiss=False
            ),
        )

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(layout_form)

        super().__init__(*args, **kwargs)

        content_types = ContentType.objects.get_for_models(
            *models_with_gr_for_model(VinculoDocDiarioOficial))

        self.fields['content_type'].choices = [
            (ct.pk, ct) for k, ct in content_types.items()]
        # Ordena por id
        self.fields['content_type'].choices.sort(key=lambda x: x[0])

    def save(self, commit=True):
        cd = self.cleaned_data
        inst = ModelForm.save(self, commit=False)

        inst.content_object = inst.content_type.get_object_for_this_type(
            numero=cd['numero'], ano=cd['ano'], tipo_id=cd['tipo'])
        inst.save()

        return inst
