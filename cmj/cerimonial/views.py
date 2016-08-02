
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from sapl.crispy_layout_mixin import CrispyLayoutFormMixin

from cmj.cerimonial.forms import LocalTrabalhoForm, EnderecoForm,\
    TipoAutoridadeForm, LocalTrabalhoPerfilForm,\
    ContatoFragmentPronomesForm, ContatoForm, ProcessoForm,\
    ContatoFragmentSearchForm, ProcessoContatoForm, ListWithSearchProcessoForm,\
    GrupoDeContatosForm
from cmj.cerimonial.models import TipoTelefone, TipoEndereco,\
    TipoEmail, Parentesco, EstadoCivil, TipoAutoridade, TipoLocalTrabalho,\
    NivelInstrucao, Contato, Telefone, OperadoraTelefonia, Email,\
    PronomeTratamento, Dependente, LocalTrabalho, Endereco,\
    DependentePerfil, LocalTrabalhoPerfil,\
    EmailPerfil, TelefonePerfil, EnderecoPerfil, FiliacaoPartidaria,\
    StatusProcesso, ClassificacaoProcesso, TopicoProcesso, Processo,\
    AssuntoProcesso, ProcessoContato, GrupoDeContatos
from cmj.cerimonial.rules import rules_patterns
from cmj.core.forms import ListWithSearchForm
from cmj.core.models import AreaTrabalho
from cmj.globalrules import globalrules
from cmj.globalrules.crud_custom import DetailMasterCrud,\
    MasterDetailCrudPermission, PerfilAbstractCrud, PerfilDetailCrudPermission


globalrules.rules.config_groups(rules_patterns)

# -------------  Details Master Crud build----------------------------

TipoTelefoneCrud = DetailMasterCrud.build(TipoTelefone, None, 'tipotelefone')
TipoEnderecoCrud = DetailMasterCrud.build(TipoEndereco, None, 'tipoendereco')
TipoEmailCrud = DetailMasterCrud.build(TipoEmail, None, 'tipoemail')
ParentescoCrud = DetailMasterCrud.build(Parentesco, None, 'parentesco')

TipoLocalTrabalhoCrud = DetailMasterCrud.build(
    TipoLocalTrabalho, None, 'tipolocaltrabalho')
StatusProcessoCrud = DetailMasterCrud.build(
    StatusProcesso, None, 'statusprocesso')
ClassificacaoProcessoCrud = DetailMasterCrud.build(
    ClassificacaoProcesso, None, 'classificacaoprocesso')
TopicoProcessoCrud = DetailMasterCrud.build(
    TopicoProcesso, None, 'topicoprocesso')

# -------------  Details Master Crud herança----------------------------


class OperadoraTelefoniaCrud(DetailMasterCrud):
    model_set = 'telefone_set'
    model = OperadoraTelefonia
    container_field_set = 'contato__workspace__operadores'

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_set = ['numero_nome_contato', ]


class NivelInstrucaoCrud(DetailMasterCrud):
    model_set = 'contato_set'
    model = NivelInstrucao
    container_field_set = 'workspace__operadores'


class EstadoCivilCrud(DetailMasterCrud):
    model_set = 'contato_set'
    model = EstadoCivil
    container_field_set = 'workspace__operadores'


class PronomeTratamentoCrud(DetailMasterCrud):
    help_text = 'pronometratamento'
    model = PronomeTratamento

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = [
            'nome_por_extenso',
            ('abreviatura_singular_m', 'abreviatura_plural_m',),
            'vocativo_direto_singular_m',
            'vocativo_indireto_singular_m',
            ('prefixo_nome_singular_m', 'prefixo_nome_singular_f'),
            'enderecamento_singular_m', ]

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            context['fluid'] = '-fluid'
            return context


class TipoAutoridadeCrud(DetailMasterCrud):
    help_text = 'tipoautoriadade'
    model = TipoAutoridade

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = ['descricao']
        form_class = TipoAutoridadeForm


# ------------- Contato Master e Details ----------------------------


class ContatoCrud(DetailMasterCrud):
    model_set = None
    model = Contato
    container_field = 'workspace__operadores'

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = ['nome', 'nome_social', 'data_nascimento',
                            'estado_civil', 'sexo', ]

        """def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            context['fluid'] = '-fluid'
            return context"""

    class ListView(DetailMasterCrud.ListView):
        form_search_class = ListWithSearchForm

        def get(self, request, *args, **kwargs):
            if 'action' in request.GET and request.GET['action'] == 'import':
                from cmj.legacy_siscam.migration import migrate_siscam
                migrate_siscam()
                return HttpResponse('migração executada!')

            return DetailMasterCrud.ListView.get(
                self, request, *args, **kwargs)

    class CreateView(DetailMasterCrud.CreateView):
        form_class = ContatoForm
        template_name = 'cerimonial/contato_form.html'

    class UpdateView(DetailMasterCrud.UpdateView):
        form_class = ContatoForm
        template_name = 'cerimonial/contato_form.html'


class FiliacaoPartidariaCrud(MasterDetailCrudPermission):
    model = FiliacaoPartidaria
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'


class DependenteCrud(MasterDetailCrudPermission):
    model = Dependente
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['parentesco', 'nome', 'nome_social',
                            'data_nascimento', 'sexo', 'identidade_genero', ]


class PreferencialMixin:

    def post(self, request, *args, **kwargs):
        response = super(PreferencialMixin, self).post(
            self, request, *args, **kwargs)

        if self.object.preferencial:
            query_filter = {self.crud.parent_field: self.object.contato}
            self.crud.model.objects.filter(**query_filter).exclude(
                pk=self.object.pk).update(preferencial=False)
        return response


class TelefoneCrud(MasterDetailCrudPermission):
    model = Telefone
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = [
            'telefone', 'tipo', 'operadora', 'preferencial']

    class UpdateView(PreferencialMixin, MasterDetailCrudPermission.UpdateView):
        pass

    class CreateView(PreferencialMixin, MasterDetailCrudPermission.CreateView):
        pass


class EmailCrud(MasterDetailCrudPermission):
    model = Email
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['email', 'tipo', 'preferencial']

    class CreateView(PreferencialMixin, MasterDetailCrudPermission.CreateView):
        pass

    class UpdateView(PreferencialMixin, MasterDetailCrudPermission.UpdateView):
        pass


class LocalTrabalhoCrud(MasterDetailCrudPermission):
    model = LocalTrabalho
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['nome', 'nome_social', 'tipo', 'data_inicio']

    class CreateView(PreferencialMixin, MasterDetailCrudPermission.CreateView):
        form_class = LocalTrabalhoForm
        template_name = 'core/crispy_form_with_trecho_search.html'

    class UpdateView(PreferencialMixin, MasterDetailCrudPermission.UpdateView):
        form_class = LocalTrabalhoForm
        template_name = 'core/crispy_form_with_trecho_search.html'


# TODO: view está sem nenhum tipo de autenticação.
class ContatoFragmentFormPronomesView(FormView):
    form_class = ContatoFragmentPronomesForm
    template_name = 'crud/ajax_form.html'

    def get_initial(self):
        initial = FormView.get_initial(self)

        try:
            initial['instance'] = TipoAutoridade.objects.get(
                pk=self.kwargs['pk'])
        except:
            pass

        return initial

    def get(self, request, *args, **kwargs):

        return FormView.get(self, request, *args, **kwargs)


class EnderecoCrud(MasterDetailCrudPermission):
    model = Endereco
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = [('endereco', 'numero'), 'complemento', 'cep',
                            ('bairro', 'municipio', 'uf'), 'preferencial']

    class CreateView(PreferencialMixin, MasterDetailCrudPermission.CreateView):
        form_class = EnderecoForm
        template_name = 'core/crispy_form_with_trecho_search.html'

    class UpdateView(PreferencialMixin, MasterDetailCrudPermission.UpdateView):
        form_class = EnderecoForm
        template_name = 'core/crispy_form_with_trecho_search.html'


# ------------- Peril Master e Details ----------------------------

class PerfilCrud(PerfilAbstractCrud):
    pass


class EnderecoPerfilCrud(PerfilDetailCrudPermission):
    model = EnderecoPerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = [
            'endereco', 'numero', 'complemento', 'bairro', 'cep']

    class CreateView(PreferencialMixin, PerfilDetailCrudPermission.CreateView):

        form_class = EnderecoForm
        template_name = 'core/crispy_form_with_trecho_search.html'

    class UpdateView(PreferencialMixin, PerfilDetailCrudPermission.UpdateView):
        form_class = EnderecoForm
        template_name = 'core/crispy_form_with_trecho_search.html'


class TelefonePerfilCrud(PerfilDetailCrudPermission):
    model = TelefonePerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = [
            'telefone', 'tipo', 'operadora', 'preferencial']

    class UpdateView(PreferencialMixin, PerfilDetailCrudPermission.UpdateView):
        pass

    class CreateView(PreferencialMixin, PerfilDetailCrudPermission.CreateView):
        pass


class EmailPerfilCrud(PerfilDetailCrudPermission):
    model = EmailPerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = ['email', 'tipo', 'preferencial']

    class UpdateView(PreferencialMixin, PerfilDetailCrudPermission.UpdateView):
        pass

    class CreateView(PreferencialMixin, PerfilDetailCrudPermission.CreateView):
        pass


class LocalTrabalhoPerfilCrud(PerfilDetailCrudPermission):
    model = LocalTrabalhoPerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = ['nome', 'nome_social', 'tipo', 'data_inicio']

    class CreateView(PreferencialMixin, PerfilDetailCrudPermission.CreateView):
        form_class = LocalTrabalhoPerfilForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'

    class UpdateView(PreferencialMixin, PerfilDetailCrudPermission.UpdateView):
        form_class = LocalTrabalhoPerfilForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'


class DependentePerfilCrud(PerfilDetailCrudPermission):
    model = DependentePerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = ['parentesco', 'nome', 'nome_social',
                            'data_nascimento', 'sexo', 'identidade_genero', ]


"""

    class CreateView11(DetailMasterCrud.CreateView):

        def form_valid(self, form):
            adm = OperadorAreaTrabalho.objects.filter(
                administrador=True).first()
            self.object = form.save(commit=False)

            if not adm and not self.object.administrador:
                form._errors['administrador'] = ErrorList([_(
                    'A Área de Trabalho não pode ficar '
                    'sem um Administrador. O primeiro registro '
                    'deve ser de um Administrador.')])
                return self.form_invalid(form)

            oper = OperadorAreaTrabalho.objects.filter(
                operador_id=self.object.operador_id,
                area_trabalho_id=self.object.area_trabalho_id
            ).first()

            if oper:
                form._errors['operador'] = ErrorList([_(
                    'Este Operador já está registrado '
                    'nesta Área de Trabalho.')])
                return self.form_invalid(form)

            response = super().form_valid(form)

            if self.object.administrador:
                OperadorAreaTrabalho.objects.filter(
                    area_trabalho_id=self.object.area_trabalho_id).exclude(
                    pk=self.object.pk).update(administrador=False)

            self.reload_groups(self.object.area_trabalho_id)

            return response

    class DeleteView11(DetailMasterCrud.DeleteView):

        def post(self, request, *args, **kwargs):

            self.object = self.get_object()

            if self.object.administrador:
                messages.add_message(
                    request, messages.ERROR, _(
                        'O Administrador não pode ser excluido diretamente. '
                        'Primeiro você deve delegar a função de administrador '
                        'a outro operador!'))
                return HttpResponseRedirect(self.detail_url)

            globalrules.rules.groups_remove_user(
                self.object.operador, [
                    globalrules.GROUP_WORKSPACE_MANAGERS,
                    globalrules.GROUP_WORKSPACE_USERS, ])

            return DetailMasterCrud.DeleteView.post(
                self, request, *args, **kwargs)
"""


# ------------- Processo Master e Details ----------------------------

class AssuntoProcessoCrud(DetailMasterCrud):
    model = AssuntoProcesso
    container_field = 'workspace__operadores'
    model_set = 'processo_set'

    class BaseMixin(DetailMasterCrud.BaseMixin):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = \
                'cerimonial/subnav_assuntoprocesso.yaml'
            return context

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_set = ['data',
                                'titulo',
                                'contatos'
                                ]


class ProcessoMasterCrud(DetailMasterCrud):
    model = Processo
    container_field = 'workspace__operadores'

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = ['data',
                            ('titulo', 'contatos'),
                            'assuntos',
                            ('status',
                             'classificacoes',)
                            ]

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = 'cerimonial/subnav_processo.yaml'
            return context

        def get_form(self, form_class=None):
            try:
                form = super(CrispyLayoutFormMixin, self).get_form(form_class)
            except AttributeError as e:
                # simply return None if there is no get_form on super
                pass
            else:
                return form

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()

            kwargs.update({'yaml_layout': self.get_layout()})
            return kwargs

    class ListView(DetailMasterCrud.ListView):
        form_search_class = ListWithSearchProcessoForm

        def get_queryset(self):
            queryset = DetailMasterCrud.ListView.get_queryset(self)

            assunto = self.request.GET.get('assunto', '')

            if assunto:
                queryset = queryset.filter(assuntos=assunto)
            return queryset

    class CreateView(DetailMasterCrud.CreateView):
        form_class = ProcessoForm
        layout_key = 'ProcessoLayoutForForm'
        template_name = 'cerimonial/crispy_form_with_contato_search.html'

    class UpdateView(DetailMasterCrud.UpdateView):
        form_class = ProcessoForm
        layout_key = 'ProcessoLayoutForForm'
        template_name = 'cerimonial/crispy_form_with_contato_search.html'


class ContatoFragmentFormSearchView(FormView):
    form_class = ContatoFragmentSearchForm
    template_name = 'crud/ajax_form.html'

    def get_initial(self):
        initial = FormView.get_initial(self)

        try:
            initial['workspace'] = AreaTrabalho.objects.filter(
                operadores=self.request.user.pk)[0]
            initial['q'] = self.request.GET[
                'q'] if 'q' in self.request.GET else ''
            initial['pks_exclude'] = self.request.GET.getlist('pks_exclude[]')
        except:
            raise PermissionDenied(_('Sem permissão de Acesso!'))

        return initial

    def get(self, request, *args, **kwargs):

        return FormView.get(self, request, *args, **kwargs)


class ProcessoContatoCrud(MasterDetailCrudPermission):
    parent_field = 'contatos'
    model = ProcessoContato
    help_path = 'processo'
    is_m2m = True
    container_field = 'contatos__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['data',
                            'titulo',
                            'assuntos',
                            'status',
                            'classificacoes']

    class CreateView(MasterDetailCrudPermission.CreateView):
        layout_key = 'ProcessoLayoutForForm'
        form_class = ProcessoContatoForm

        """def form_valid(self, form):
            response = MasterDetailCrudPermission.CreateView.form_valid(
                self, form)

            pk = self.kwargs['pk']
            self.object.contatos.add(Contato.objects.get(pk=pk))

            return response"""

    class UpdateView(MasterDetailCrudPermission.UpdateView):
        layout_key = 'ProcessoLayoutForForm'
        form_class = ProcessoContatoForm

    class DetailView(MasterDetailCrudPermission.DetailView):
        layout_key = 'Processo'

    class ListView(MasterDetailCrudPermission.ListView):
        layout_key = 'ProcessoLayoutForForm'


class GrupoDeContatosMasterCrud(DetailMasterCrud):
    model = GrupoDeContatos
    container_field = 'workspace__operadores'

    model_set = 'contatos'

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = ['nome']
        list_field_names_set = ['nome', 'telefone_set', 'email_set']
        layout_key = 'GrupoDeContatosLayoutForForm'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context[
                'subnav_template_name'] = 'cerimonial/subnav_grupocontato.yaml'
            return context

        def get_form(self, form_class=None):
            try:
                form = super(CrispyLayoutFormMixin, self).get_form(form_class)
            except AttributeError as e:
                # simply return None if there is no get_form on super
                pass
            else:
                return form

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()

            kwargs.update({'yaml_layout': self.get_layout()})
            return kwargs

    class CreateView(DetailMasterCrud.CreateView):
        template_name = 'cerimonial/crispy_form_with_contato_search.html'
        form_class = GrupoDeContatosForm

    class UpdateView(DetailMasterCrud.UpdateView):
        template_name = 'cerimonial/crispy_form_with_contato_search.html'
        form_class = GrupoDeContatosForm
