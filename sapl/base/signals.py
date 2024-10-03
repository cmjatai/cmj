from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete
from django.db.models.signals import post_migrate
from django.db.utils import DEFAULT_DB_ALIAS
from django.dispatch import Signal, receiver
from django.utils.translation import gettext_lazy as _

from sapl.base.models import Autor, TipoAutor as modelTipoAutor
from sapl.materia.models import Tramitacao
from sapl.protocoloadm.models import TramitacaoAdministrativo
from sapl.utils import get_base_url
from sapl.utils import models_with_gr_for_model

from .tasks import task_envia_email_tramitacao


tramitacao_signal = Signal(providing_args=['post', 'request'])


@receiver(tramitacao_signal)
def handle_tramitacao_signal(sender, **kwargs):
    tramitacao = kwargs.get("post")
    request = kwargs.get("request")
    if 'protocoloadm' in str(sender):
        doc_mat = tramitacao.documento
        tipo = "documento"
    elif 'materia' in str(sender):
        tipo = "materia"
        doc_mat = tramitacao.materia

    kwargs = {'base_url': get_base_url(request), 'tipo': tipo, 'doc_mat_id': doc_mat.id,
              'tramitacao_status_id': tramitacao.status.id,
              'tramitacao_unidade_tramitacao_destino_id': tramitacao.unidade_tramitacao_destino.id}

    task_envia_email_tramitacao.delay(kwargs)


@receiver(post_delete, sender=Tramitacao)
@receiver(post_delete, sender=TramitacaoAdministrativo)
def status_tramitacao_materia(sender, instance, **kwargs):
    if sender == Tramitacao:
        if instance.status.indicador == 'F':
            materia = instance.materia
            materia.em_tramitacao = True
            materia.save()
    elif sender == TramitacaoAdministrativo:
        if instance.status.indicador == 'F':
            documento = instance.documento
            documento.tramitacao = True
            documento.save()


@receiver(post_migrate, dispatch_uid='cria_models_tipo_autor')
def cria_models_tipo_autor(app_config=None, verbosity=2, interactive=True,
                           using=DEFAULT_DB_ALIAS, **kwargs):

    models = models_with_gr_for_model(Autor)

    print("\n\033[93m\033[1m{}\033[0m".format(
        _('Atualizando registros TipoAutor do SAPL:')))
    TipoAutor = modelTipoAutor
    for model in models:
        content_type = ContentType.objects.get_for_model(model)
        tipo_autor = TipoAutor.objects.filter(
            content_type=content_type.id).exists()

        if tipo_autor:
            msg1 = "Carga de {} não efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " Já Existe um {} {} relacionado...".format(
                TipoAutor._meta.verbose_name,
                model._meta.verbose_name)
            msg = "  {}{}".format(msg1, msg2)
        else:
            novo_autor = TipoAutor()
            novo_autor.content_type_id = content_type.id
            novo_autor.descricao = model._meta.verbose_name
            novo_autor.save()
            msg1 = "Carga de {} efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " {} {} criado...".format(
                TipoAutor._meta.verbose_name, content_type.model)
            msg = "  {}{}".format(msg1, msg2)
        print(msg)
    # Disconecta função para evitar a chamada repetidas vezes.
    post_migrate.disconnect(dispatch_uid='cria_models_tipo_autor')
