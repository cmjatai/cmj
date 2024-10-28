import calendar
from datetime import datetime, timedelta

from django.core.exceptions import PermissionDenied
from django.views.generic.list import ListView

from cmj.agenda.forms import EventoForm
from cmj.agenda.models import Evento, TipoEvento
from cmj.core.models import AreaTrabalho
from sapl.crud.base import Crud, CrudAux


TipoEventoCrud = CrudAux.build(TipoEvento, '')


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
                qs = qs.filter(workspace__tipo=AreaTrabalho.TIPO_PUBLICO)
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
                        cal[i][j] = {
                            'data': datetime(mes_base.year, mes_base.month, dia),
                            'eventos': [],
                            'now': now.day == dia and mes_base.month == now.month,
                            'destaque': False
                        }

            for evento in ol.filter(
                    inicio__year=mes_base.year,
                    inicio__month=mes_base.month):
                ano = evento.inicio.year
                mes = evento.inicio.month
                dia = evento.inicio.day

                prim_dia = datetime(ano, mes, 1)
                dia_pos = dia + prim_dia.weekday()

                coluna = (dia_pos) % 7
                linha = (dia_pos - (7 if prim_dia.weekday() == 6 else 0)) // 7

                if evento.caracteristica == Evento.FERIADO:
                    cal[linha][coluna]['destaque'] = True

                cal[linha][coluna]['eventos'].insert(0, evento)

            linha_inicial = cal[0][::-1]
            for i, dia in enumerate(linha_inicial):
                if dia:
                    dia_pos = dia['data']
                else:
                    dia_pos = dia_pos - timedelta(days=1)
                    linha_inicial[i] = {
                        'data': dia_pos,
                        'eventos': None,
                        'now': False,
                        'destaque': False
                    }

            cal[0] = linha_inicial[::-1]

            linha_final = cal[-1]
            for i, dia in enumerate(linha_final):
                if dia:
                    dia_pos = dia['data']
                else:
                    dia_pos = dia_pos + timedelta(days=1)
                    linha_final[i] = {
                        'data': dia_pos,
                        'eventos': None,
                        'now': now.day == dia and mes_base.month == now.month,
                        'destaque': False
                    }

            cal[-1] = linha_final

            context['object_list'] = cal

            return context
