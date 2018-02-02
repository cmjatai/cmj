
from braces.views import FormMessagesMixin
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView, UpdateView

from cmj.core.forms_auth import CmjUserChangeForm
from cmj.crud.base import FORM_MESSAGES, ACTION_UPDATE


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

    """def form_valid(self, form):
        new_password = form.cleaned_data['new_password1']

        user = self.request.user
        user.set_password(new_password)
        user.save()

        return super().form_valid(form)"""
