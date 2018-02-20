
from braces.views import FormMessagesMixin
from django.contrib.auth import get_user_model, logout
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView

from cmj.ouvidoria.forms import DenunciaForm
from cmj.ouvidoria.models import Solicitacao


class DenunciaAnonimaFormView(FormMessagesMixin, CreateView):
    form_valid_message, form_invalid_message = (
        _('Sua denúncia anônima foi encaminha.'),
        _('Houve um erro no envio de sua mensagem.'))
    model = Solicitacao
    form_class = DenunciaForm
    template_name = 'ouvidoria/denuncia_form.html'

    def get_context_data(self, **kwargs):

        context = CreateView.get_context_data(self, **kwargs)
        context['title'] = _('Denúncia Anônima')
        return context

    def get_success_url(self):
        return reverse('cmj.ouvidoria:denuncia_form')

    def get_initial(self):
        initial = CreateView.get_initial(self)
        initial.update({'logged_user':
                        bool(self.request.user.is_authenticated)})
        return initial

    def get(self, request, *args, **kwargs):
        response = CreateView.get(self, request, *args, **kwargs)
        if self.request.user.is_authenticated:
            logout(request)

        return response


class SolicitacaoDetailView(DetailView):
    model = Solicitacao
    template_name = 'ouvidoria/solicitacao_detail.html'
