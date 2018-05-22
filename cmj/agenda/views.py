from django.core.exceptions import PermissionDenied

from cmj.agenda.forms import EventoForm
from cmj.agenda.models import Evento
from cmj.core.models import AreaTrabalho
from cmj.crud.base import Crud


class EventoCrud(Crud):
    model_set = None
    model = Evento
    container_field = 'workspace__operadores'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ('inicio', 'fim', 'titulo',
                            'solicitante', 'descricao')

        def get_initial(self):
            initial = {}

            try:
                initial['workspace'] = AreaTrabalho.objects.filter(
                    operadores=self.request.user.pk)[0]
            except:
                raise PermissionDenied(_('Sem permissão de Acesso!'))

            return initial

    class CreateView(Crud.CreateView):
        form_class = EventoForm

    class UpdateView(Crud.UpdateView):
        form_class = EventoForm
