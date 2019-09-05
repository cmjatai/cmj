
from braces.views import FormMessagesMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, PasswordResetView
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView, UpdateView

from cmj.core.forms_auth import CmjUserChangeForm, LoginForm,\
    RecuperarSenhaForm
from cmj.settings import EMAIL_SEND_USER
from sapl.crud.base import FORM_MESSAGES, ACTION_UPDATE


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
