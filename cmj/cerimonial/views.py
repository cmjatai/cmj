
from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.utils import ErrorList
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormMixin, FormView
from sapl.crud.base import DETAIL, CrudListView
from sapl.parlamentares.models import Partido, Parlamentar, Filiacao

from cmj.cerimonial.forms import LocalTrabalhoForm, EnderecoForm,\
    OperadorAreaTrabalhoForm, TipoAutoridadeForm,\
    LocalTrabalhoFragmentPronomesForm, LocalTrabalhoPerfilForm
from cmj.cerimonial.models import StatusVisita, TipoTelefone, TipoEndereco,\
    TipoEmail, Parentesco, EstadoCivil, TipoAutoridade, TipoLocalTrabalho,\
    NivelInstrucao, Contato, Telefone, OperadoraTelefonia, Email,\
    PronomeTratamento, Dependente, LocalTrabalho, Endereco,\
    AreaTrabalho, OperadorAreaTrabalho, DependentePerfil, LocalTrabalhoPerfil,\
    EmailPerfil, TelefonePerfil, EnderecoPerfil, FiliacaoPartidaria
from cmj.cerimonial.rules import rules_patterns
from cmj.globalrules import globalrules
from cmj.globalrules.crud_custom import DetailMasterCrud,\
    MasterDetailCrudPermission, PerfilAbstractCrud, PerfilDetailCrudPermission
from cmj.utils import normalize


globalrules.rules.config_groups(rules_patterns)

# -------------  Details Master ----------------------------


StatusVisitaCrud = DetailMasterCrud.build(StatusVisita, None, 'statusvisita')
TipoTelefoneCrud = DetailMasterCrud.build(TipoTelefone, None, 'tipotelefone')
TipoEnderecoCrud = DetailMasterCrud.build(TipoEndereco, None, 'tipoendereco')
TipoEmailCrud = DetailMasterCrud.build(TipoEmail, None, 'tipoemail')
ParentescoCrud = DetailMasterCrud.build(Parentesco, None, 'parentesco')


TipoLocalTrabalhoCrud = DetailMasterCrud.build(
    TipoLocalTrabalho, None, 'tipolocaltrabalho')


# ------------- Area de Trabalho Master e Details ----------------------------


class AreaTrabalhoCrud(DetailMasterCrud):
    model = AreaTrabalho

    class BaseMixin(DetailMasterCrud.BaseMixin):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context[
                'subnav_template_name'] = 'cerimonial/subnav_areatrabalho.yaml'
            return context

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_set = ['user_name', ]


class OperadorAreaTrabalhoCrud(MasterDetailCrudPermission):
    parent_field = 'areatrabalho'
    model = OperadorAreaTrabalho
    help_path = 'operadorareatrabalho'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context[
                'subnav_template_name'] = 'cerimonial/subnav_areatrabalho.yaml'
            return context

    class UpdateView(MasterDetailCrudPermission.UpdateView):
        form_class = OperadorAreaTrabalhoForm

        # TODO tornar operador readonly na edição
        def form_valid(self, form):
            old = OperadorAreaTrabalho.objects.get(pk=self.object.pk)

            groups = list(old.grupos_associados.values_list('name', flat=True))
            globalrules.rules.groups_remove_user(old.user, groups)

            response = super().form_valid(form)

            groups = list(self.object.grupos_associados.values_list(
                'name', flat=True))
            globalrules.rules.groups_add_user(self.object.user, groups)

            return response

    class CreateView(MasterDetailCrudPermission.CreateView):
        form_class = OperadorAreaTrabalhoForm
        # TODO mostrar apenas usuários que não possuem grupo ou que são de
        # acesso social

        def form_valid(self, form):
            self.object = form.save(commit=False)
            oper = OperadorAreaTrabalho.objects.filter(
                user_id=self.object.user_id,
                areatrabalho_id=self.object.areatrabalho_id
            ).first()

            if oper:
                form._errors['user'] = ErrorList([_(
                    'Este Operador já está registrado '
                    'nesta Área de Trabalho.')])
                return self.form_invalid(form)

            response = super().form_valid(form)

            groups = list(self.object.grupos_associados.values_list(
                'name', flat=True))
            globalrules.rules.groups_add_user(self.object.user, groups)

            return response

    class DeleteView(MasterDetailCrudPermission.DeleteView):

        def post(self, request, *args, **kwargs):

            self.object = self.get_object()
            groups = list(
                self.object.grupos_associados.values_list('name', flat=True))
            globalrules.rules.groups_remove_user(self.object.user, groups)

            return MasterDetailCrudPermission.DeleteView.post(
                self, request, *args, **kwargs)


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


class PartidoCrud(DetailMasterCrud):
    help_text = 'partidos'
    model_set = 'filiacaopartidaria_set'
    model = Partido
    container_field_set = 'contato__workspace__operadores'
    # container_field = 'filiacoes_partidarias_set__contato__workspace__operadores'

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_set = ['contato_nome', ]

    class ListView(DetailMasterCrud.ListView):

        def get(self, request, *args, **kwargs):

            ws = AreaTrabalho.objects.filter(operadores=request.user).first()

            if ws and ws.parlamentar:
                filiacao_parlamentar = Filiacao.objects.filter(
                    parlamentar=ws.parlamentar)

                if filiacao_parlamentar.exists():
                    partido = filiacao_parlamentar.first().partido
                    return redirect(
                        reverse(
                            'sapl.parlamentares:partido_detail',
                            args=(partido.pk,)))

            """else:
                self.kwargs['queryset_liberar_sem_container'] = True"""

            return DetailMasterCrud.ListView.get(
                self, request, *args, **kwargs)

        """def get_queryset(self):
            queryset = CrudListView.get_queryset(self)
            if not self.request.user.is_authenticated():
                return queryset

            if 'queryset_liberar_sem_container' in self.kwargs and\
                    self.kwargs['queryset_liberar_sem_container']:
                return queryset

            if self.container_field:
                params = {}
                params[self.container_field] = self.request.user.pk
                return queryset.filter(**params)

            return queryset"""


class PronomeTratamentoCrud(DetailMasterCrud):
    help_text = 'pronometratamento'
    model = PronomeTratamento

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = [
            'nome_por_extenso',
            'abreviatura_singular_m',
            'abreviatura_plural_m',
            'vocativo_direto_singular_m',
            'vocativo_indireto_singular_m',
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
                            'estado_civil', 'sexo', 'identidade_genero', ]

        """def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            context['fluid'] = '-fluid'
            return context"""

    class ListView(DetailMasterCrud.ListView):

        def get_queryset(self):
            queryset = DetailMasterCrud.ListView.get_queryset(self)

            request = self.request
            if request.GET.get('q') is not None:
                query = normalize(str(request.GET.get('q')))

                query = query.split(' ')
                if query:
                    q = Q()
                    for item in query:
                        if not item:
                            continue
                        q = q & Q(search__icontains=item)

                    if q:
                        queryset = queryset.filter(q)

            return queryset


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
            'ddd', 'numero', 'tipo', 'operadora', 'preferencial']

    class UpdateView(MasterDetailCrudPermission.UpdateView, PreferencialMixin):
        pass

    class CreateView(MasterDetailCrudPermission.CreateView):

        def post(self, request, *args, **kwargs):
            response = MasterDetailCrudPermission.CreateView.post(
                self, request, *args, **kwargs)

            if self.object.preferencial:
                Telefone.objects.filter(
                    contato_id=self.object.contato_id).exclude(
                    pk=self.object.pk).update(preferencial=False)
            return response


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
        template_name = 'cerimonial/localtrabalho_form.html'

    class UpdateView(PreferencialMixin, MasterDetailCrudPermission.UpdateView):
        form_class = LocalTrabalhoForm
        template_name = 'cerimonial/localtrabalho_form.html'


# TODO: view está sem nenhum tipo de autenticação.
class LocalTrabalhoFragmentFormPronomesView(FormView):
    form_class = LocalTrabalhoFragmentPronomesForm
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

    class CreateView(MasterDetailCrudPermission.CreateView):
        form_class = EnderecoForm
        template_name = 'core/crispy_form_with_trecho_search.html'

    class UpdateView(MasterDetailCrudPermission.UpdateView):
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

    class CreateView(PerfilDetailCrudPermission.CreateView):

        form_class = EnderecoForm
        template_name = 'core/crispy_form_with_trecho_search.html'

    class UpdateView(PerfilDetailCrudPermission.UpdateView):
        form_class = EnderecoForm
        template_name = 'core/crispy_form_with_trecho_search.html'


class TelefonePerfilCrud(PerfilDetailCrudPermission):
    model = TelefonePerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = [
            'ddd', 'numero', 'tipo', 'operadora', 'preferencial']

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
