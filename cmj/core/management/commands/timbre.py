import io
import logging

import PyPDF4
from PyPDF4.pdf import PdfFileReader, PdfFileWriter
from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete, post_save
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import open_and_read
from reportlab.pdfgen import canvas

from cmj.settings.project import PROJECT_DIR
from cmj.utils import Manutencao


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'input_file', nargs='*')

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        post_save.disconnect(dispatch_uid='timerefresh_post_signal')
        m = Manutencao()
        m.desativa_auto_now()
        m.desativa_signals()

        def pagina_com_logotipo():
            topo = PROJECT_DIR.child(
                '_frontend', 'v1', 'dist', 'img', 'pdf_cabec_margem.jpg')
            rodape = PROJECT_DIR.child(
                '_frontend', 'v1', 'dist', 'img', 'pdf_rodape_margem.jpg')

            packet = io.BytesIO()
            try:
                can = canvas.Canvas(
                    packet, pagesize=landscape(A4))  # landscape(A4)

                #can.setFillColorRGB(255, 255, 0, 1)
                #can.setFillColorCMYK(0, 0, 0, 0, 1)
                #can.rect(v['xf'], v['yf'], v['wf'], v['hf'], stroke=0, fill=1)
                largura = 595
                can.drawImage(topo, 0, 746, largura, 400 / 2500 * largura)

                #can.setFillColorCMYK(0, 0, 0, 0, 1)
                #can.rect(v['xh'], v['yh'], v['wh'], v['hh'], stroke=0, fill=1)
                can.drawImage(rodape, 0, 0, largura, 150 / 1700 * largura)

                #can.setFillColorCMYK(0, 0, 0, 1, 1)
                # can.setFontSize(9)
                # can.drawString(
                ##    v['xh'] + 250, v['yh'] + 45,
                #   'AUTÓGRAFO Nº 641, DE 13 DE DEZEMBRO DE 2019.')

                can.save()

            except Exception as e:
                print(e)

            packet.seek(0)

            pagina = PdfFileReader(packet)
            return pagina

        name_ifile = options['input_file']

        for nifile in name_ifile:

            name_ofile = nifile.replace('.pdf', '__timbrado.pdf')

            ofile = PdfFileWriter()

            ifile = PdfFileReader(
                open(nifile, "rb"))

            for num_page in range(ifile.getNumPages()):

                pl = pagina_com_logotipo()

                p = ifile.getPage(num_page)

                p.mergePage(pl.getPage(0))
                ofile.addPage(p)

            outputStream = open(name_ofile, 'wb')
            ofile.write(outputStream)
            outputStream.close()
