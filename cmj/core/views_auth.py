
from braces.views import FormMessagesMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, PasswordResetView,\
    PasswordResetConfirmView
from django.db.models import Q
from django.urls.base import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView, UpdateView

from cmj.core.forms import ListWithSearchForm
from cmj.core.forms_auth import CmjUserChangeForm, LoginForm,\
    RecuperarSenhaForm, CmjUserAdminForm, NovaSenhaForm
from cmj.settings import EMAIL_SEND_USER
from sapl.crud.base import FORM_MESSAGES, ACTION_UPDATE, Crud, CrudAux


class CmjUserChangeView(FormMessagesMixin, UpdateView):
    form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_UPDATE]
    model = get_user_model()
    form_class = CmjUserChangeForm
    template_name = 'crud/form.html'

    def get_context_data(self, **kwargs):

        context = UpdateView.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            self.object.get_full_name(),
            self.object.email)
        return context

    def get_success_url(self):
        return reverse('cmj.core:cmj_user_change')

    def cancel_url(self):
        return '/'

    def get_object(self, queryset=None):
        return self.request.user


class CmjLoginView(LoginView):
    template_name = 'core/user/login.html'
    authentication_form = LoginForm


class CmjPasswordResetView(PasswordResetView):
    email_template_name = 'core/user/recuperar_senha_email.html'
    success_url = reverse_lazy('cmj.core:recuperar_senha_finalizado')

    html_email_template_name = 'core/user/recuperar_senha_email.html'
    template_name = 'core/user/recuperar_senha_email_form.html'
    from_email = EMAIL_SEND_USER
    form_class = RecuperarSenhaForm


class CmjPasswordResetEncaminhadoView(PasswordResetView):
    template_name = 'core/user/recupera_senha_email_enviado.html'


class CmjPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = NovaSenhaForm
    template_name = 'core/user/nova_senha_form.html'


class UserCrud(CrudAux):
    model = get_user_model()

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = [
            'usuario', 'autor_set', 'areatrabalho_set', 'is_active'
        ]

        def get_context_object_name(self, *args, **kwargs):
            return None

    class CreateView(CrudAux.CreateView):
        form_class = CmjUserAdminForm

    class UpdateView(CrudAux.UpdateView):
        form_class = CmjUserAdminForm
        layout_key = ''

        def get_form_kwargs(self):
            kwargs = CrudAux.UpdateView.get_form_kwargs(self)
            kwargs['user_session'] = self.request.user
            return kwargs

    class DetailView(CrudAux.DetailView):
        layout_key = 'UserDetail'

    class ListView(CrudAux.ListView):
        form_search_class = ListWithSearchForm
        ordered_list = None
        paginate_by = 300

        def hook_header_usuario(self, *args, **kwargs):
            return 'Usuario'

        def hook_usuario(self, *args, **kwargs):
            return '{}<br><small>{}</small>'.format(
                args[0].get_full_name(),
                args[0].email
            ), args[2]

        def hook_header_autor_set(self, *args, **kwargs):
            return 'Operador de Autor'

        def hook_header_areatrabalho_set(self, *args, **kwargs):
            return 'Operador de Área de Trabalho'

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(first_name__icontains=q_param)
                q |= Q(last_name__icontains=q_param)
                q |= Q(email__icontains=q_param)
                qs = qs.filter(q)

            return qs

        def dispatch(self, request, *args, **kwargs):
            return CrudAux.ListView.dispatch(self, request, *args, **kwargs)
