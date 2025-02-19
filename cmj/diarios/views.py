
import logging

from braces.views._forms import FormMessagesMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls.base import reverse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from cmj.core.models import CertidaoPublicacao
from cmj.diarios.forms import VinculoDocDiarioOficialForm
from cmj.diarios.models import TipoDeDiario, DiarioOficial, \
    VinculoDocDiarioOficial
from sapl.crispy_layout_mixin import get_field_display
from sapl.crud.base import CrudAux, Crud, RP_DETAIL, RP_LIST, \
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

        @property
        def extras_url(self):
            btns = []

            if self.request.user.has_perm('diarios.change_diariooficial'):
                btns += [
                    (
                        '%s?associar_certidoes' % reverse(
                            'cmj.diarios:diariooficial_detail',
                            kwargs={'pk': self.kwargs['pk']}),
                        'btn-primary',
                        _('Associar Certidões')
                    ),
                    (
                        '%s?extrato' % reverse(
                            'cmj.diarios:diariooficial_detail',
                            kwargs={'pk': self.kwargs['pk']}),
                        'btn-secondary',
                        _('Extrato')
                    ),

                ]
                return btns

        def get_context_data(self, **kwargs):
            c = super().get_context_data(**kwargs)
            c['bg_title'] = 'bg-maroon text-white'

            if self.extrato:
                c['object_list'] = VinculoDocDiarioOficial.objects.filter(
                    diario=self.object).order_by('content_type_id', 'object_id')

            return c

        def hook_vinculodocdiariooficial_set(self, obj):
            v = force_str(
                _('Documentos Públicados no PortalCMJ')
            ) if self.object.tipo.principal else force_str(
                _('Republicação de documentos no PortalCMJ')
            )
            text = []
            if obj.vinculodocdiariooficial_set.exists():
                for vinculo in obj.vinculodocdiariooficial_set.all():
                    if vinculo.content_object:
                        text.append(
                            f'<li><a href="{vinculo.reverse_link_content_object}">{vinculo.content_object}</a></li>'
                        )
            else:
                text.append(
                    f'<li>Não existe no PortalCMJ registros associados a este Diário</li>'
                )

            return v, f"<ul>{''.join(text)}</ul>"

        def get(self, request, *args, **kwargs):

            self.extrato = False
            if request.GET.get('extrato', None) is not None and \
                    self.request.user.has_perm('diarios.change_diariooficial'):
                self.template_name = 'diarios/diariooficial_extrato.html'
                self.extrato = True

            elif request.GET.get('associar_certidoes', None) is not None and \
                    self.request.user.has_perm('diarios.change_diariooficial'):
                self.associar_certidoes()
                messages.add_message(
                    self.request,
                    messages.INFO,
                    _('As certidões encontradas foram associadas a este diário!'))
                return redirect(
                    reverse(
                        'cmj.diarios:diariooficial_detail',
                        kwargs={'pk': self.kwargs['pk']}
                    )
                )

            return Crud.DetailView.get(self, request, *args, **kwargs)

        def associar_certidoes(self):
            self.object = self.model.objects.get(pk=self.kwargs['pk'])

            certs = CertidaoPublicacao.objects.filter(
                created__gte=self.object.data).order_by('id')

            # VinculoDocDiarioOficial.objects.filter(diario=self.object).delete()

            for c in certs:
                if c.cancelado or c.revogado or c.content_object is None:
                    continue
                # print(c.content_object)
                # continue
                if not VinculoDocDiarioOficial.objects.filter(
                    diario=self.object,
                    content_type_id=c.content_type_id,
                    object_id=c.object_id
                ).exists():
                    v = VinculoDocDiarioOficial()
                    v.content_object = c.content_object
                    v.diario = self.object
                    v.pagina = 1
                    v.save()


class VinculoDocDiarioOficialCrud(MasterDetailCrud):
    model = VinculoDocDiarioOficial
    parent_field = 'diario'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(Crud.PublicMixin, MasterDetailCrud.BaseMixin):
        list_field_names = ['object_id', 'pagina']

    class ListView(MasterDetailCrud.ListView):
        ordered_list = False

        def get(self, request, *args, **kwargs):
            self.parent_object = get_object_or_404(DiarioOficial, **kwargs)
            return MasterDetailCrud.ListView.get(self, request, *args, **kwargs)

        def hook_header_object_id(self, *args, **kwargs):
            if self.parent_object.tipo.principal:
                return force_str(_('Documentos Públicados no PortalCMJ'))
            return force_str(_('Republicação de documentos no PortalCMJ'))

        def hook_object_id(self, *args, **kwargs):
            ct = args[0].content_type
            if self.request.user.has_perm(
                    f'{ct.app_label}.change_{ct.model}'):
                return args[0].content_object, args[2]
            else:
                return args[0].content_object, args[0].reverse_link_content_object

    class CreateView(MasterDetailCrud.CreateView, FormMessagesMixin):
        layout_key = None
        form_class = VinculoDocDiarioOficialForm

        def get_initial(self):
            i = MasterDetailCrud.CreateView.get_initial(self)
            i.update({
                'diario': DiarioOficial.objects.get(pk=self.kwargs['pk']),
                'data_diario': DiarioOficial.objects.get(pk=self.kwargs['pk']).data,
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
                'diario': self.object.diario,
                'data_diario': self.object.diario.data
            })
            return i
