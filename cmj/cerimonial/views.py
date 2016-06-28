
from django.contrib import messages
from django.contrib.auth.models import Group
from django.forms.utils import ErrorList
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormMixin

from cmj.cerimonial.forms import LocalTrabalhoForm, EnderecoForm,\
    OperadorAreaTrabalhoForm
from cmj.cerimonial.models import StatusVisita, TipoTelefone, TipoEndereco,\
    TipoEmail, Parentesco, EstadoCivil, TipoAutoridade, TipoLocalTrabalho,\
    NivelInstrucao, Contato, Telefone, OperadoraTelefonia, Email,\
    PronomeTratamento, Dependente, LocalTrabalho, Endereco,\
    AreaTrabalho, OperadorAreaTrabalho, DependentePerfil, LocalTrabalhoPerfil,\
    EmailPerfil, TelefonePerfil, EnderecoPerfil
from cmj.cerimonial.rules import rules_patterns
from cmj.globalrules import globalrules
from cmj.globalrules.crud_custom import DetailMasterCrud,\
    MasterDetailCrudPermission, PerfilAbstractCrud, PerfilDetailCrudPermission


globalrules.rules.config_groups(rules_patterns)

# -------------  Details Master ----------------------------
EstadoCivilCrud = DetailMasterCrud.build(
    EstadoCivil, 'contatos_set', 'estadocivil')
NivelInstrucaoCrud = DetailMasterCrud.build(
    NivelInstrucao, 'contatos_set', 'nivelinstrucao')

StatusVisitaCrud = DetailMasterCrud.build(StatusVisita, None, 'statusvisita')
TipoTelefoneCrud = DetailMasterCrud.build(TipoTelefone, None, 'tipotelefone')
TipoEnderecoCrud = DetailMasterCrud.build(TipoEndereco, None, 'tipoendereco')
TipoEmailCrud = DetailMasterCrud.build(TipoEmail, None, 'tipoemail')
ParentescoCrud = DetailMasterCrud.build(Parentesco, None, 'parentesco')

AreaTrabalhoCrud = DetailMasterCrud.build(AreaTrabalho, None, 'areatrabalho')


TipoAutoridadeCrud = DetailMasterCrud.build(
    TipoAutoridade, None, 'tipoautoriadade')
TipoLocalTrabalhoCrud = DetailMasterCrud.build(
    TipoLocalTrabalho, None, 'tipolocaltrabalho')
PronomeTratamentoCrud = DetailMasterCrud.build(
    PronomeTratamento, None, 'pronometratamento')

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
        list_field_names_model_set = ['user_name', ]


class OperadorAreaTrabalhoCrud(MasterDetailCrudPermission):
    parent_field = 'area_trabalho'
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
                area_trabalho_id=self.object.area_trabalho_id
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
    model_set = 'telefones_set'
    model = OperadoraTelefonia

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_model_set = ['numero_nome_contato', ]

# ------------- Contato Master e Details ----------------------------


class ContatoCrud(DetailMasterCrud):
    model_set = None
    model = Contato
    container_field = 'workspace__operadores'

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = ['nome', 'nome_social', 'data_nascimento',
                            'estado_civil', 'sexo', 'identidade_genero', ]

    class ListView(DetailMasterCrud.ListView):

        def get_queryset(self):

            queryset = DetailMasterCrud.ListView.get_queryset(self)
            return queryset


class DependenteCrud(MasterDetailCrudPermission):
    model = Dependente
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['parentesco', 'nome', 'nome_social',
                            'data_nascimento', 'sexo', 'identidade_genero', ]


class TelefoneCrud(MasterDetailCrudPermission):
    model = Telefone
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['ddd', 'numero', 'tipo', 'operadora']

    class UpdateView(MasterDetailCrudPermission.UpdateView):

        def post(self, request, *args, **kwargs):
            response = MasterDetailCrudPermission.UpdateView.post(
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

    class UpdateView(MasterDetailCrudPermission.UpdateView):

        def post(self, request, *args, **kwargs):
            response = EmailCrud.UpdateView.post(
                self, request, *args, **kwargs)

            if self.object.preferencial:
                Email.objects.filter(
                    contato_id=self.object.contato_id).exclude(
                    pk=self.object.pk).update(preferencial=False)
            return response


class LocalTrabalhoCrud(MasterDetailCrudPermission):
    model = LocalTrabalho
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['nome', 'nome_social', 'tipo', 'data_inicio']

    class CreateView(MasterDetailCrudPermission.CreateView):
        form_class = LocalTrabalhoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'

    class UpdateView(MasterDetailCrudPermission.UpdateView):
        form_class = LocalTrabalhoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'


class EnderecoCrud(MasterDetailCrudPermission):
    model = Endereco
    parent_field = 'contato'
    container_field = 'contato__workspace__operadores'

    class CreateView(MasterDetailCrudPermission.CreateView):
        form_class = EnderecoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'

    class UpdateView(MasterDetailCrudPermission.UpdateView):
        form_class = EnderecoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'


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
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'

    class UpdateView(PerfilDetailCrudPermission.UpdateView):
        form_class = EnderecoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'


class TelefonePerfilCrud(PerfilDetailCrudPermission):
    model = TelefonePerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = [
            'ddd', 'numero', 'tipo', 'operadora', 'preferencial']

    class UpdateView(PerfilDetailCrudPermission.UpdateView):

        def post(self, request, *args, **kwargs):
            response = PerfilDetailCrudPermission.UpdateView.post(
                self, request, *args, **kwargs)

            if self.object.preferencial:
                Telefone.objects.filter(
                    contato_id=self.object.contato_id).exclude(
                    pk=self.object.pk).update(preferencial=False)
            return response


class EmailPerfilCrud(PerfilDetailCrudPermission):
    model = EmailPerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = ['email', 'tipo', 'preferencial']

    class UpdateView(PerfilDetailCrudPermission.UpdateView):

        def post(self, request, *args, **kwargs):
            response = PerfilDetailCrudPermission.UpdateView.post(
                self, request, *args, **kwargs)

            if self.object.preferencial:
                Email.objects.filter(
                    contato_id=self.object.contato_id).exclude(
                    pk=self.object.pk).update(preferencial=False)
            return response


class LocalTrabalhoPerfilCrud(PerfilDetailCrudPermission):
    model = LocalTrabalhoPerfil
    parent_field = 'contato'

    class BaseMixin(PerfilDetailCrudPermission.BaseMixin):
        list_field_names = ['nome', 'nome_social', 'tipo', 'data_inicio']

    class CreateView(PerfilDetailCrudPermission.CreateView):
        form_class = LocalTrabalhoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'

    class UpdateView(PerfilDetailCrudPermission.UpdateView):
        form_class = LocalTrabalhoForm
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
