from datetime import datetime, date, timedelta
import inspect
import json
import logging
import time

from asgiref.sync import async_to_sync
from asn1crypto import cms
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.mail.message import EmailMultiAlternatives
from django.template import loader
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cmj.context_processors import site_url
from cmj.core import tasks
from cmj.core.models import AuditLog, OcrMyPDF, Bi
from cmj.loa.models import ScrapRecord, DespesaPaga
from cmj.painelset.models import Cronometro
from cmj.settings.email import EMAIL_SEND_USER
from cmj.sigad.models import ShortRedirect
from cmj.videos.models import VideoParte, PullExec
from sapl.materia.models import AnaliseSimilaridade


logger = logging.getLogger(__name__)


def auditlog_signal_function(sender, **kwargs):

    try:
        app_name = sender._meta.app_config.name[:4]
        if app_name not in ('cmj.', 'sapl'):
            return
    except:
        # não é necessário usar logger, aqui é usada apenas para
        # eliminar um o if complexo
        return

    instance = kwargs.get('instance')
    if instance._meta.model in (
        AuditLog,        # Causa recursividade
        # Revisao,       # já é o log de notícias
        ShortRedirect,   # já é o log de redirecionamento de short links
        OcrMyPDF,        # já é o log de execução de ocr
        Bi,              # Bi é um processo automático estatístico
        PullExec,        # Conexão com youtube
        ScrapRecord,      # Extração Automática das Despesas e Receitas
        DespesaPaga,
        AnaliseSimilaridade,  # Análise de Similaridade
        Cronometro,  # Cronometro é um processo automático que possui seu próprio log
    ):
        return

    #if settings.DEBUG:
    #    logger.debug(f'START')
    u = None
    stack = ''
    for i in inspect.stack():
        stack = str(i)
        if i.function == 'migrate':
            return
        r = i.frame.f_locals.get('request', None)
        try:
            if r.user._meta.label == settings.AUTH_USER_MODEL:
                u = r.user
                if u.is_anonymous:
                    return
                break
        except:
            # não é necessário usar logger, aqui é usada apenas para
            # eliminar um o if complexo
            pass

    try:
        # logger.info('\n'.join(stack))

        operation = kwargs.get('created', 'D')
        if operation != 'D':
            operation = 'C' if operation else 'U'

        al = AuditLog()
        al.user = u
        al.email = u.email if u else ''
        al.operation = operation
        al.obj = json.loads(serializers.serialize("json", (instance, )))
        al.content_object = instance if operation != 'D' else None
        al.obj_id = instance.id
        al.model_name = instance._meta.model_name
        al.app_name = instance._meta.app_label

        al.obj[0]['stack'] = stack

        if hasattr(instance, 'visibilidade'):
            al.visibilidade = instance.visibilidade

        al.save()

        #if settings.DEBUG:
        #    logger.debug(f'END')

    except Exception as e:
        logger.error('Error saving auditing log object')
        logger.error(e)


def notificacao_signal_function(sender, instance, **kwargs):

    if hasattr(instance, 'not_send_mail') and instance.not_send_mail:
        return

    if settings.DEBUG:
        return

    if instance.user.be_notified_by_email:

        send_mail(
            instance.content_object.email_notify['subject'],
            'email/notificacao_%s_%s.html' % (
                instance.content_object._meta.app_label,
                instance.content_object._meta.model_name
            ),
            {
                'notificacao': instance,
                'site_url': settings.SITE_URL
            },
             EMAIL_SEND_USER, instance.user.email)

        print('Uma Notificação foi enviada %s - user: %s - user_origin: %s' % (
            instance.pk,
            instance.user,
            instance.user_origin))


def redesocial_post_function_time_call_documento(inst):
    if settings.DEBUG:
        return 30

    if inst.visibilidade:
        raise Exception

    ct = ContentType.objects.get_by_natural_key('sigad', 'documento')
    vp = VideoParte.objects.filter(
        content_type=ct, object_id=inst.id).first()

    if inst.classe_id in (10, ):
        raise Exception

    if not vp:
        return 3600

    if vp.video.json['snippet']['liveBroadcastContent'] == 'live':
        return 120
    elif vp.video.json['snippet']['liveBroadcastContent'] == 'none':
        return 3600
    raise Exception


def redesocial_post_function_time_call_materialegislativa(inst):
    if settings.DEBUG:
        return 30
    return 600


def redesocial_post_function(sender, instance, **kwargs):

    if not hasattr(instance, '_meta') or \
        instance._meta.app_config is None or \
            not instance._meta.app_config.name in settings.BUSINESS_APPS:
        return

    if not hasattr(instance, 'metadata'):
        return

    if hasattr(instance, 'parent') and instance.parent:
        return

    #if settings.DEBUG:
    #    logger.debug(f'START redesocial_post_signal {timezone.localtime()}')

    running = {
        'MateriaLegislativa': {
            'data_min': date(2023, 3, 10) if not settings.DEBUG else date(2022, 1, 1),
            'time_call': redesocial_post_function_time_call_materialegislativa
        },
        'Documento': {
            'data_min': date(2023, 3, 10) if not settings.DEBUG else date(2022, 1, 1),
            'time_call': redesocial_post_function_time_call_documento
        },
    }

    if instance._meta.object_name not in running.keys():
        return

    redes = [
        'telegram'
    ]

    for i, r in enumerate(redes, 1):
        md = instance.metadata
        if not md:
            md = {}

        if 'send' in md and r in md['send']:
            return

        s = md.get('send', {r: None})

        if r in s and s[r]:
            return

        for d in ('data', 'data_apresentacao', 'public_date'):

            if hasattr(instance, d):
                d = getattr(instance, d)

                if not d:
                    return
                if isinstance(d, datetime):
                    d = d.date()

                if d < running[instance._meta.object_name]['data_min']:
                    return

        now = timezone.now()
        try:
            td = timedelta(
                seconds=running[instance._meta.object_name]['time_call'](
                    instance)
            )
        except:
            return

        s[r] = timezone.localtime()
        md['send'] = s
        instance.metadata = md
        instance.save()

        logger.info('chamou task_send_rede_social')
        tasks.task_send_rede_social.apply_async(
            (
                r,
                instance._meta.app_label,
                instance._meta.model_name,
                instance.id
            ),
            eta=now + td
        )


def send_mail(subject, email_template_name, context, from_email, to_email):
    subject = ''.join(subject.splitlines())
    html_email = loader.render_to_string(email_template_name, context)
    email_message = EmailMultiAlternatives(subject, '', from_email, [to_email])
    email_message.attach_alternative(html_email, 'text/html')
    email_message.send()


def send_signal_for_websocket_time_refresh(inst, **kwargs):

    action = 'post_save' if 'created' in kwargs else 'post_delete'
    created = kwargs.get('created', False)

    if hasattr(inst, '_meta') and \
        not inst._meta.app_config is None and \
        (
            inst._meta.app_config.name in settings.SAPL_APPS or
            inst._meta.label in (
                'painelset.Individuo',
                'painelset.Cronometro',
                'painelset.CronometroEvent'
            )
        ):

        if settings.DEBUG:
            logger.debug(f'start: {inst.id} {inst._meta.app_label}.{inst._meta.model_name}')

        try:
            if hasattr(inst, 'ws_sync') and not inst.ws_sync():
                return

            inst_serialize = None
            if hasattr(inst, 'ws_serialize'):
                inst_serialize = inst.ws_serialize()

            channel_layer = get_channel_layer()

            if inst._meta.label in (
                'painelset.Evento',
                'painelset.Individuo',
                'painelset.Cronometro',
                'painelset.CronometroEvent'
            ):
                #if not inst_serialize:
                #    inst_serialize = json.loads(
                #        serializers.serialize("json", (inst, )))[0]['fields']
                #    inst_serialize['id'] = inst.id

                async_to_sync(channel_layer.group_send)(
                    "group_sync_channel", {
                        "type": "sync",
                        'action': action,
                        'id': inst.id,
                        'app': inst._meta.app_label,
                        'model': inst._meta.model_name,
                        'created': created,
                        'instance': inst_serialize,
                        'timestamp': time.time()
                    }
                )
            else:
                # deprecated canal, manter para compatibilidade, coverter para group_sync_channel
                async_to_sync(channel_layer.group_send)(
                    "group_time_refresh_channel", {
                        "type": "time_refresh.message",
                        'message': {
                            'action': action,
                            'id': inst.id,
                            'app': inst._meta.app_label,
                            'model': inst._meta.model_name,
                            'created': created,
                            'instance': inst_serialize
                        }
                    }
                )

        except Exception as e:
            logger.error(_("Erro na comunicação com o backend do redis. "
                           "Certifique se possuir um servidor de redis "
                           "ativo funcionando como configurado em "
                           "CHANNEL_LAYERS"))

def signed_files_extraction_post_save_signal_function(sender, instance, **kwargs):

    if not hasattr(instance, 'FIELDFILE_NAME') or not hasattr(instance, 'metadata'):
        return

    params_tasks = (
        sender._meta.app_label,
        sender._meta.model_name,
        instance.pk
    )

    if not settings.DEBUG or (
            settings.DEBUG and settings.FOLDER_DEBUG_CONTAINER == settings.PROJECT_DIR):
        tasks.signed_files_extraction.apply_async(
            params_tasks,
            countdown=3
        )
    else:
        tasks.task_signed_files_extraction_function(*params_tasks)
