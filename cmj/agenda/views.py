from datetime import datetime, timedelta
import calendar

from django.core.exceptions import PermissionDenied
from django.views.generic.list import ListView

from cmj.agenda.forms import EventoForm
from cmj.agenda.models import Evento, TipoEvento
from cmj.core.models import AreaTrabalho
from cmj.crud.base import Crud, CrudAux


TipoEventoCrud = CrudAux.build(TipoEvento, None)


class EventoCrud(Crud):
    model_set = None
    model = Evento
    container_field = 'workspace__operadores'
    public = ['.list_']

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ('inicio', 'fim', 'titulo',
                            'solicitante', 'descricao')

        def get_initial(self):
            initial = super().get_initial()

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

    class ListView(Crud.ListView):
        paginate_by = None

        @property
        def title(self):
            return self.verbose_name_plural

        def get_queryset(self):
            qs = ListView.get_queryset(self)

            if not self.request.user.pk or not AreaTrabalho.objects.filter(
                    operadores=self.request.user.pk).exists():
                qs = qs.filter(workspace__tipo=AreaTrabalho.TIPO_INSTITUCIONAL)
            else:
                qs = qs.filter(workspace__operadores=self.request.user.pk)
            return qs

        def dispatch(self, request, *args, **kwargs):
            return ListView.dispatch(self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = ListView.get_context_data(self, **kwargs)
            ol = context['object_list']
            calendar.setfirstweekday(calendar.SUNDAY)

            try:
                m = int(self.request.GET.get('m', '0'))
            except:
                m = 0

            context['m_next'] = m + 1
            context['m_previous'] = m - 1

            now = datetime.now()
            mes_base = datetime(now.year, now.month, 15)
            mes_base = mes_base + timedelta(days=int(m) * 30)

            cal = calendar.monthcalendar(mes_base.year, mes_base.month)

            for i, semana in enumerate(cal):
                for j, dia in enumerate(semana):
                    if dia:
                        cal[i][j] = [
                            datetime(mes_base.year, mes_base.month, dia),
                            [],
                            now.day == dia and mes_base.month == now.month
                        ]

            for evento in ol.filter(
                    inicio__year=mes_base.year,
                    inicio__month=mes_base.month):
                ano = evento.inicio.year
                mes = evento.inicio.month
                dia = evento.inicio.day

                primeiro_dia = datetime(ano, mes, 1)
                dia_pos = dia + primeiro_dia.weekday()
                cal[(dia_pos) // 7][(dia_pos) % 7][1].insert(0, evento)

            linha_inicial = cal[0][::-1]
            for i, dia in enumerate(linha_inicial):
                if dia:
                    dia_pos = dia[0]
                else:
                    dia_pos = dia_pos - timedelta(days=1)
                    linha_inicial[i] = [dia_pos, None, False]

            cal[0] = linha_inicial[::-1]

            linha_final = cal[-1]
            for i, dia in enumerate(linha_final):
                if dia:
                    dia_pos = dia[0]
                else:
                    dia_pos = dia_pos + timedelta(days=1)
                    linha_final[i] = [
                        dia_pos, None,
                        now.day == dia and mes_base.month == now.month]

            cal[-1] = linha_final

            context['object_list'] = cal

            return context
