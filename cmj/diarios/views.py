
from braces.views._forms import FormMessagesMixin
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from cmj.diarios.forms import VinculoDocDiarioOficialForm
from cmj.diarios.models import TipoDeDiario, DiarioOficial,\
    VinculoDocDiarioOficial
from sapl.crispy_layout_mixin import get_field_display
from sapl.crud.base import CrudAux, Crud, RP_DETAIL, RP_LIST,\
    MasterDetailCrud


TipoDeDiarioCrud = CrudAux.build(TipoDeDiario, None)


class DiarioOficialCrud(Crud):
    model = DiarioOficial
    help_topic = 'diariooficial'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(Crud.PublicMixin, Crud.BaseMixin):
        list_field_names = ['edicao', 'data', 'tipo', 'descricao', 'arquivo']

    class ListView(Crud.PublicMixin, Crud.ListView):
        def get_context_data(self, **kwargs):
            c = super().get_context_data(**kwargs)
            c['bg_title'] = 'bg-maroon text-white'
            return c

    class DetailView(Crud.PublicMixin, Crud.DetailView):
        layout_key = 'DiarioOficialDetail'

        def get_context_data(self, **kwargs):
            c = super().get_context_data(**kwargs)
            c['bg_title'] = 'bg-maroon text-white'
            return c

        def hook_vinculodocdiariooficial_set(self, obj):
            v = force_text(
                _('Documentos Públicados no PortalCMJ')
            ) if self.object.tipo.principal else force_text(
                _('Republicação de documentos no PortalCMJ')
            )
            text = []
            for vinculo in obj.vinculodocdiariooficial_set.all():
                text.append(
                    f'<li><a href="{vinculo.reverse_link_content_object}">{vinculo.content_object}</a></li>'
                )
            empty:
                text.append(
                    f'<li>Não existe no PortalCMJ registros associados a este Diário</li>'
                )

            return v, f"<ul>{''.join(text)}</ul>"


class VinculoDocDiarioOficialCrud(MasterDetailCrud):
    model = VinculoDocDiarioOficial
    parent_field = 'diario'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(Crud.PublicMixin, MasterDetailCrud.BaseMixin):
        list_field_names = ['content_object', 'pagina']

    class ListView(MasterDetailCrud.ListView):
        def get(self, request, *args, **kwargs):
            self.parent_object = get_object_or_404(DiarioOficial, **kwargs)
            return MasterDetailCrud.ListView.get(self, request, *args, **kwargs)

        def hook_header_content_object(self, *args,  **kwargs):
            if self.parent_object.tipo.principal:
                return force_text(_('Documentos Públicados no PortalCMJ'))
            return force_text(_('Republicação de documentos no PortalCMJ'))

        def hook_content_object(self, *args, **kwargs):
            ct = args[0].content_type
            if self.request.user.has_perm(
                    f'{ct.app_label}.change_{ct.model}'):
                return args[0].content_object, args[2]
            else:
                return args[1], ''

    class CreateView(MasterDetailCrud.CreateView, FormMessagesMixin):
        layout_key = None
        form_class = VinculoDocDiarioOficialForm

        def get_initial(self):
            i = MasterDetailCrud.CreateView.get_initial(self)
            i.update({
                'diario': DiarioOficial.objects.get(pk=self.kwargs['pk']),
            })

            return i

    class UpdateView(MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = VinculoDocDiarioOficialForm

        def get_initial(self):
            i = MasterDetailCrud.UpdateView.get_initial(self)
            i.update({
                'content_type': self.object.content_type,
                'tipo': self.object.content_object.tipo_id,
                'numero': self.object.content_object.numero,
                'ano': self.object.content_object.ano,
                'diario': self.object.diario
            })
            return i
