import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

from cmj.utils import Manutencao
from cmj.utils_pdf import Pdf2PdfA

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):

        m = Manutencao()
        m.desativa_auto_now()
        m.desativa_signals()

        post_save.disconnect(dispatch_uid="signal_post_syncrefresh")
        post_save.disconnect(dispatch_uid="timerefresh_post_signal")

        logger.info("Auto_now and signals have been disabled.")
        logger.info("Post-save signals have been disconnected.")
        logger.info("OCR command setup is complete.")

        #in_path = settings.MEDIA_ROOT.child("teste", "ri.pdf")

        in_path = settings.MEDIA_ROOT.child("teste", "2026-4979-lei-lei-ordinaria.pdf")
        #in_path = '/home'
        logger.info("Pdf2PdfA conversion is starting for file: %s", in_path)
        Pdf2PdfA(in_path, ocr=True, level=3, jobs=8, verbose=2).execute()
