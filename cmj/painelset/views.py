
from ast import In
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from cmj.painelset.forms import EventoForm, IndividuoForm
from cmj.painelset.models import Evento, Individuo
from sapl.crud.base import Crud, MasterDetailCrud
from django.utils import timezone, formats


def app_vue_painel(request, slug=None):
    return render(request, 'painelset/app_vue_painel.html')


class EventoCrud(Crud):
    model = Evento

    class CreateView(Crud.CreateView):
        form_class = EventoForm
        layout_key = None

    class UpdateView(Crud.UpdateView):
        form_class = EventoForm
        layout_key = None

    class ListView(Crud.ListView):
        def hook_start_previsto(self, obj, default, url):
            if obj.start_previsto:
                return formats.date_format(obj.start_previsto, "d/m/Y - H:i"), ''
            return '', ''

    class DetailView(Crud.DetailView):

        def hook_start_previsto(self, obj, verbose_name, field_display):
            if obj.start_previsto:
                return verbose_name, formats.date_format(timezone.localtime(obj.start_previsto), "d/m/Y - H:i")
            return verbose_name, ''

        def hook_start_real(self, obj, verbose_name, field_display):
            if obj.start_real:
                return verbose_name, formats.date_format(timezone.localtime(obj.start_real), "d/m/Y - H:i")
            return verbose_name, ''

        def hook_end_real(self, obj, verbose_name, field_display):
            if obj.end_real:
                return verbose_name, formats.date_format(timezone.localtime(obj.end_real), "d/m/Y - H:i")
            return verbose_name, ''


class IndividuoCrud(MasterDetailCrud):
    model = Individuo
    parent_field = 'evento'

    class ListView(MasterDetailCrud.ListView):
        paginate_by = 100
        layout_key = 'IndividuoUpdate'

        def hook_name(self, obj, default, url):
            return '<a href="{}" pk="{}">{}</a>'.format(
                url, obj.id, obj.name), ''

    class CreateView(MasterDetailCrud.CreateView):
        layout_key = 'IndividuoCreate'
        form_class = IndividuoForm

    class UpdateView(MasterDetailCrud.UpdateView):
        layout_key = 'IndividuoUpdate'
        form_class = IndividuoForm
        
    class DetailView(MasterDetailCrud.DetailView):
        layout_key = 'IndividuoUpdate'
