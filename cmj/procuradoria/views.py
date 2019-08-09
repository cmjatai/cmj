
from django.utils.translation import ugettext_lazy as _

from cmj.crud.base import CrudAux, Crud, RP_LIST, RP_DETAIL
from cmj.procuradoria.models import TipoDocumentoProcuradoria,\
    DocumentoProcuradoria


TipoDocumentoProcuradoriaCrud = CrudAux.build(
    TipoDocumentoProcuradoria, '')


class DocumentoProcuradoriaCrud(Crud):
    model = DocumentoProcuradoria
    help_topic = 'documentoprocuradoria'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['numero', 'ano', 'tipo', 'data',
                            'protocolo__numero', 'ementa',
                            'interessado']


"""
        @property
        def search_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesq_doc_procuradoria'))

        list_url = ''

    class ListView(RedirectView, Crud.ListView):

        def get_redirect_url(self, *args, **kwargs):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesq_doc_procuradoria'))

    class CreateView(Crud.CreateView):
        form_class = DocumentoProcuradoriaForm
        layout_key = None

        @property
        def cancel_url(self):
            return self.search_url

    class UpdateView(Crud.UpdateView):
        form_class = DocumentoProcuradoriaForm
        layout_key = None

        def get_initial(self):
            if self.object.protocolo:
                p = self.object.protocolo
                return {'ano_protocolo': p.ano,
                        'numero_protocolo': p.numero}

    class DetailView(Crud.DetailView):

        def get(self, *args, **kwargs):
            pk = self.kwargs['pk']
            documento = DocumentoProcuradoria.objects.get(id=pk)
            if documento.restrito and self.request.user.is_anonymous():
                return redirect('/')
            return super(Crud.DetailView, self).get(args, kwargs)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            self.layout_display[0]['rows'][-1][0]['text'] = (
                '<a href="%s"></a>' % reverse(
                    'cmj.procuradoria:doc_texto_integral',
                    kwargs={'pk': self.object.pk}))
            return context

    class DeleteView(Crud.DeleteView):

        def get_success_url(self):
            return self.search_url


class PesquisarDocumentoProcuradoriaView(PermissionRequiredMixin,
                                         FilterView):
    model = DocumentoProcuradoria
    filterset_class = DocumentoProcuradoriaFilterSet
    paginate_by = 10
    permission_required = ('procuradoria.list_documentoprocuradoria', )

    def get_filterset_kwargs(self, filterset_class):
        super(PesquisarDocumentoProcuradoriaView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset()

        if 'o' in self.request.GET and not self.request.GET['o']:
            qs = qs.order_by('-ano', '-numero')

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(PesquisarDocumentoProcuradoriaView,
                        self).get_context_data(**kwargs)

        if self.paginate_by:
            paginator = context['paginator']
            page_obj = context['page_obj']
            context['page_range'] = make_pagination(
                page_obj.number, paginator.num_pages)

        return context

    def get(self, request, *args, **kwargs):
        super(PesquisarDocumentoProcuradoriaView, self).get(request)
        # Se a pesquisa estiver quebrando com a paginação
        # Olhe esta função abaixo
        # Provavelmente você criou um novo campo no Form/FilterSet
        # Então a ordem da URL está diferente
        data = self.filterset.data
        if data and data.get('tipo') is not None:
            url = "&" + str(self.request.META['QUERY_STRING'])
            if url.startswith("&page"):
                ponto_comeco = url.find('tipo=') - 1
                url = url[ponto_comeco:]
        else:
            url = ''
        self.filterset.form.fields['o'].label = _('Ordenação')

        # é usada essa verificação anônima para quando os documentos da procuradoria
        # estão no modo ostensivo, mas podem existir documentos administrativos
        # restritos
        if request.user.is_anonymous():
            length = self.object_list.filter(restrito=False).count()
        else:
            length = self.object_list.count()

        context = self.get_context_data(filter=self.filterset,
                                        filter_url=url,
                                        numero_res=length
                                        )
        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        return self.render_to_response(context)
"""
