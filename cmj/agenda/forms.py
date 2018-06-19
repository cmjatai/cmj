from django.forms.fields import SplitDateTimeField
from django.forms.models import ModelForm
from django.forms.widgets import SplitDateTimeWidget
from django.utils.translation import ugettext_lazy as _

from cmj.agenda.models import Evento


class CustomSplitDateTimeWidget(SplitDateTimeWidget):
    def render(self, name, value, attrs=None, renderer=None):
        rendered_widgets = []
        for i, x in enumerate(self.widgets):
            rendered_widgets.append(
                x.render(
                    '%s_%d' % (name, i), self.decompress(
                        value)[i] if value else ''
                )
            )

        html = '<div class="col-xs-6">%s</div><div class="col-xs-6">%s</div>'\
            % tuple(rendered_widgets)
        return '<div class="row">%s</div>' % html


class EventoForm(ModelForm):
    inicio = SplitDateTimeField(widget=CustomSplitDateTimeWidget)
    fim = SplitDateTimeField(widget=CustomSplitDateTimeWidget, required=False)

    class Meta:
        model = Evento
        exclude = ('workspace', )