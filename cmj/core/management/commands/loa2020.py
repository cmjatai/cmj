import io
import logging

import PyPDF4
from PyPDF4.pdf import PdfFileReader, PdfFileWriter
from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete, post_save
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import open_and_read
from reportlab.pdfgen import canvas


class Command(BaseCommand):

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        self.run_ploe42_2019()

    def run_ploe42_2019(self):

        def pagina_com_logotipo(x, y, size=(83, 60), xn=0, yn=0):
            logo_camara = '/home/leandro/Câmara/logo/logo.png'
            logo_horizontal = '/home/leandro/Câmara/logo/logo_horizontal.png'

            packet = io.BytesIO()
            try:
                can = canvas.Canvas(packet, pagesize=A4)  # landscape(A4)

                can.drawImage(logo_camara, x, y, size[0], size[1])

                # can.drawString(x, y, "Hello world")

                can.save()
            except Exception as e:
                print(e)

            packet.seek(0)

            pagina = PdfFileReader(packet)
            return pagina

        i = '/home/leandro/TEMP/autografos/PLOE-42/anexo_42.pdf'
        o = '/home/leandro/TEMP/autografos/PLOE-42/anexo_42_out.pdf'

        ofile = PdfFileWriter()
        ifile = PdfFileReader(open(i, "rb"))

        xy = []
        for num_page in range(ifile.getNumPages()):
            xy.append((10, 10))

        xy[1] = 100, 100

        for num_page in range(ifile.getNumPages()):
            pl = pagina_com_logotipo(*xy[num_page])

            p = ifile.getPage(num_page)

            p.mergePage(pl.getPage(0))
            ofile.addPage(p)

        outputStream = open(o, "wb")
        ofile.write(outputStream)
        outputStream.close()
