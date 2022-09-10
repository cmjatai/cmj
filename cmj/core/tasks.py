import logging

from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import requests

from cmj.celery import app
from sapl.materia.models import MateriaLegislativa

logger = logging.getLogger(__name__)

socials_connects = {
    'telegram': dict(
        TOKEN=settings.TELEGRAM_CMJATAI_BOT_KEY,
        API_ID=settings.TELEGRAM_API_ID,
        API_HASH=settings.TELEGRAM_API_HASH,
        CHAT_ID=settings.TELEGRAM_CHAT_ID if not settings.DEBUG else settings.TELEGRAM_CHAT_DEV_ID,
        url_base=f"https://api.telegram.org/bot{settings.TELEGRAM_CMJATAI_BOT_KEY}/{{endpoint}}"
    )
}


@app.task(queue='celery', bind=True)
def task_send_rede_social(self, rede, app_label, model_name, pk):
    # print(args)
    # print(kwargs)
    # return

    send_func = f'send_{rede}_{app_label}_{model_name}'
    print(f'print, task_send_rede_social iniciou execução: {send_func}')
    logger.info(f'logger task_send_rede_social iniciou execução: {send_func}')

    gf = globals()
    if send_func in gf:
        return gf[send_func](pk)


def send_telegram_materia_materialegislativa(pk):
    print('send matéria iniciou execução')
    logger.info('send matéria iniciou execução')

    instance = MateriaLegislativa.objects.get(pk=pk)
    md = instance.metadata

    if not md:
        md = {}

    if 'send' not in md:
        md['send'] = {}

    md['send']['telegram'] = timezone.localtime()
    instance.metadata = md
    instance.save()

    autores_hash_tag = ' '.join(
        map(lambda a: '#{}'.format(''.join(str(a.nome).split(' '))), instance.autores.all()))

    autores = '\n'.join(
        map(lambda a: '<i>{}</i>'.format(a), instance.autores.all()))

    text = f"""#{instance.tipo.sigla} #MatériaLegislativa
<b>{str(instance).upper()}</b>   
    
<pre>{instance.ementa}</pre>

Autoria:
{autores}

{autores_hash_tag}
<a href="{settings.SITE_URL}/materia/{instance.id}">Acompanhe o Processo Legislativo desta Matéria clicando aqui.</a>
    """

    #<tg-spoiler>spoiler</tg-spoiler>
    # if settings.DEBUG:
    print(text)
    logger.info(text)
    #    return

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
