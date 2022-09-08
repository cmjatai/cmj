import logging

from django.conf import settings
from django.core import serializers
from django.utils import timezone
from django.utils.text import slugify
import requests

from cmj.celery import app

logger = logging.getLogger(__name__)

socials_connects = {
    'telegram': dict(
        TOKEN=settings.TELEGRAM_CMJATAI_BOT_KEY,
        API_ID=settings.TELEGRAM_API_ID,
        API_HASH=settings.TELEGRAM_API_HASH,
        CHAT_ID=settings.TELEGRAM_CHAT_ID,
        url_base=f"https://api.telegram.org/bot{settings.TELEGRAM_CMJATAI_BOT_KEY}/{{endpoint}}"
    )
}


@app.task(queue='celery', bind=True)
def task_send_rede_social(self, rede, instance_serialized):
    print('task_send_rede_social')

    list_objs = list(serializers.deserialize('json', instance_serialized))

    if not list_objs:
        return

    instance = list_objs[0].object

    send_func = f'send_{rede}_{instance._meta.db_table}'

    gf = globals()
    if send_func in gf:
        return gf[send_func](instance)


def send_telegram_materia_materialegislativa(instance):
    print('send_telegram_materia_materialegislativa')
    md = instance.metadata

    if not md:
        md = {}

    if 'send' not in md:
        md['send'] = {}

    md['send']['telegram'] = timezone.now()
    instance.metadata = md
    instance.save()

    autores_hash_tag = ' '.join(
        map(lambda a: '#{}'.format(''.join(str(a.nome).split(' '))), instance.autores.all()))

    autores = '\n'.join(
        map(lambda a: '<i>{}</i>'.format(a), instance.autores.all()))

    text = f"""<b>{str(instance).upper()}</b>   
    
<pre>{instance.ementa}</pre>

Autoria:
{autores}

<a href="{settings.SITE_URL}/materia/{instance.id}">Acompanhe o Processo Legislativo desta Matéria clicando aqui.</a>
#{instance.tipo.sigla} #MatériaLegislativa {autores_hash_tag}
    """

    #<tg-spoiler>spoiler</tg-spoiler>
    if settings.DEBUG:
        print(text)
        return

    url_base = socials_connects['telegram']['url_base']
    CHAT_ID = socials_connects['telegram']['CHAT_ID']

    try:
        r = requests.post(
            url_base.format(
                endpoint='sendMessage'
            ),
            data={
                'parse_mode': 'html',
                'chat_id': CHAT_ID,
                'text': text,
            }
        )
        with open(instance.texto_original.path, mode='rb') as fp:

            def custom_filename(item):
                arcname = '{}-{:03d}-{}-{}.{}'.format(
                    item.ano,
                    item.numero,
                    slugify(item.tipo.sigla),
                    slugify(item.tipo.descricao),
                    item.texto_original.path.split('.')[-1])
                return arcname

            r = requests.post(
                url_base.format(
                    endpoint='sendDocument'
                ),
                data={
                    'chat_id': CHAT_ID,
                    'caption': 'Uma cópia na integra do original para você conferir!'
                },
                files={
                    'document': (custom_filename(instance), fp.read(), 'application/pdf')
                }
            )

    except Exception as e:
        print(e)
