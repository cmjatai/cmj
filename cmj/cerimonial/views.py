
from django.utils.translation import ugettext_lazy as _

from cmj.cerimonial.forms import LocalTrabalhoForm, EnderecoForm
from cmj.cerimonial.models import StatusVisita, TipoTelefone, TipoEndereco,\
    TipoEmail, Parentesco, EstadoCivil, TipoAutoridade, TipoLocalTrabalho,\
    NivelInstrucao, Contato, Telefone, OperadoraTelefonia, Email,\
    PronomeTratamento, Dependente, LocalTrabalho, Endereco
from cmj.core.sapl_crud_custom import DetailMasterCrud,\
    MasterDetailCrudPermission


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

TipoAutoridadeCrud = DetailMasterCrud.build(
    TipoAutoridade, None, 'tipoautoriadade')
TipoLocalTrabalhoCrud = DetailMasterCrud.build(
    TipoLocalTrabalho, None, 'tipolocaltrabalho')
PronomeTratamentoCrud = DetailMasterCrud.build(
    PronomeTratamento, None, 'pronometratamento')


class OperadoraTelefoniaCrud(DetailMasterCrud):
    model_set = 'telefones_set'
    model = OperadoraTelefonia

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_model_set = ['numero_nome_contato', ]


class ContatoCrud(DetailMasterCrud):
    model_set = None
    model = Contato

    class BaseMixin(DetailMasterCrud.BaseMixin):
        list_field_names = ['nome', 'nome_social', 'data_nascimento',
                            'estado_civil', 'sexo', 'identidade_genero', ]


# ------------- Master Details ----------------------------


class DependenteCrud(MasterDetailCrudPermission):
    model = Dependente
    parent_field = 'contato'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['parentesco', 'nome', 'nome_social',
                            'data_nascimento', 'sexo', 'identidade_genero', ]


class TelefoneCrud(MasterDetailCrudPermission):
    model = Telefone
    parent_field = 'contato'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['ddd', 'numero', 'tipo', 'operadora']

    class UpdateView(MasterDetailCrudPermission.UpdateView):

        def post(self, request, *args, **kwargs):
            response = TelefoneCrud.UpdateView.post(
                self, request, *args, **kwargs)

            if self.object.preferencial:
                Telefone.objects.filter(
                    contato_id=self.object.contato_id).exclude(
                    pk=self.object.pk).update(preferencial=False)
            return response


class EmailCrud(MasterDetailCrudPermission):
    model = Email
    parent_field = 'contato'

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

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['nome', 'nome_social', 'tipo', 'data_inicio']

    class CreateView(MasterDetailCrudPermission.CreateView):
        form_class = LocalTrabalhoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'

    class UpdateView(MasterDetailCrudPermission.UpDateView):
        form_class = LocalTrabalhoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'


class EnderecoCrud(MasterDetailCrudPermission):
    model = Endereco
    parent_field = 'contato'

    class CreateView(MasterDetailCrudPermission.CreateView):
        form_class = EnderecoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'

    class UpdateView(MasterDetailCrudPermission.UpDateView):
        form_class = EnderecoForm
        template_name = 'cerimonial/crispy_form_with_trecho_search.html'
