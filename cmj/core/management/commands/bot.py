import logging

from django.conf import settings
from django.core.management.base import BaseCommand
import requests
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.updater import Updater
from telegram.update import Update

from cmj.sigad.models import Documento
from sapl.materia.models import MateriaLegislativa


logger = logging.getLogger(__name__)


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, default='')

    def handle(self, *args, **options):

        d = Documento.objects.filter(
            parent__isnull=True,
            public_date__isnull=False
        ).exclude(slug__icontains='video').order_by('-public_date').first()
        if not d.metadata:
            d.metadata = {}
        d.metadata['send'] = {}
        d.save()

        d = Documento.objects.filter(
            parent__isnull=True,
            public_date__isnull=False
        ).order_by('-public_date').first()
        if not d.metadata:
            d.metadata = {}
        d.metadata['send'] = {}
        d.save()
        return

        m = MateriaLegislativa.objects.first()
        m.metadata['signs'] = {}
        m.metadata['send'] = {}
        m.save()
        #n = NormaJuridica.objects.first()
        # n.save()
        # task_send_rede_social(
        #    self, 'telegram', serialize('json', [m])
        #)

        # send_telegram_materia_materialegislativa(m)
        # m.save()
        return

        self.start = options['start']

        if self.start == 'bot':
            self.start_bot()
            return
        TOKEN = settings.TELEGRAM_CMJATAI_BOT_KEY
        API_ID = settings.TELEGRAM_API_ID
        API_HASH = settings.TELEGRAM_API_HASH
        CHAT_ID = settings.TELEGRAM_CHAT_ID

        url = "https://api.telegram.org/bot{token}/{endpoint}"

        teste = f"sendMessage?chat_id={CHAT_ID}&text=Hello Word!!!"

        r = requests.post(
            url.format(
                token=TOKEN,
                endpoint='sendMessage'
            ),
            data={
                'chat_id': CHAT_ID,
                'text': 'https://www.jatai.go.leg.br/materia/19484'
            }
        )
        """with open('/home/leandro/Downloads/20220629_084955_3.jpg', mode='rb') as fp:

            r = requests.post(
                url.format(
                    token=TOKEN,
                    endpoint='sendPhoto'
                ),
                data={
                    'chat_id': CHAT_ID,
                },
                files={
                    'photo': fp.read()
                }
            )
        print(r)

        with open('/home/leandro/Downloads/ed_391_assinado.pdf', mode='rb') as fp:

            r = requests.post(
                url.format(
                    token=TOKEN,
                    endpoint='sendDocument'
                ),
                data={
                    'chat_id': CHAT_ID,
                },
                files={
                    'document': ('diario.pdf', fp.read(), 'application/pdf')
                }
            )
            print(r)"""

    def start_bot(self):
        TOKEN = settings.TELEGRAM_CMJATAI_BOT_KEY

        updater = Updater(TOKEN, use_context=True)

        def start(update: Update, context: CallbackContext):
            update.message.reply_text(
                "Olá Cidadão, Bem vindo ao bot da Câmara Municipal de Jataí. \
                Use /help para ver os comandos disponíveis.")

        def help(update: Update, context: CallbackContext):
            update.message.reply_text("""Comandos Disponíveis:
            /youtube - Para ver o link do nosso canal no Youtube
            /instagram - Para ver o link do Instagram""")

        def youtube_url(update: Update, context: CallbackContext):
            update.message.reply_text("Youtube Link =>\
            \nhttps://www.youtube.com/CâmaraMunicipalJataí")

        def instagram_url(update: Update, context: CallbackContext):
            update.message.reply_text("Instagram Link =>\
            \nhttps://www.instagram.com/cmjatai")

        def unknown(update: Update, context: CallbackContext):
            update.message.reply_text(
                "Desculpe, '%s' é um comando inválido" % update.message.text)

        def unknown_text(update: Update, context: CallbackContext):
            update.message.reply_text(
                "Desculpe, não pude reconhecer o texto... ['%s']" % update.message.text)

        updater.dispatcher.add_handler(
            CommandHandler('youtube', youtube_url))
        updater.dispatcher.add_handler(
            CommandHandler('instagram', instagram_url))
        updater.dispatcher.add_handler(CommandHandler('start', start))
        updater.dispatcher.add_handler(CommandHandler('help', help))
        updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown))
        updater.dispatcher.add_handler(MessageHandler(
            Filters.command, unknown))

        # Filters out unknown messages.
        updater.dispatcher.add_handler(
            MessageHandler(Filters.text, unknown_text))

        updater.start_polling()

        print('Ouvindo...')
