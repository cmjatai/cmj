
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView, UpdateView

from cmj.core.forms_auth import CmjUserChangeForm
from cmj.settings import LOGIN_URL


class CmjUserChangeView(UpdateView):
    model = get_user_model()
    form_class = CmjUserChangeForm
    template_name = 'crud/form.html'
    success_url = LOGIN_URL

    def get_object(self, queryset=None):
        return self.request.user

    """def form_valid(self, form):
        new_password = form.cleaned_data['new_password1']

        user = self.request.user
        user.set_password(new_password)
        user.save()

        return super().form_valid(form)"""
