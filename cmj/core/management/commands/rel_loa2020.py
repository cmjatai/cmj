import io
import logging

import PyPDF4
from PyPDF4.pdf import PdfFileReader, PdfFileWriter
from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete, post_save
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import open_and_read
from reportlab.pdfgen import canvas


class Command(BaseCommand):

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='timerefresh_post_delete_signal')
        post_save.disconnect(dispatch_uid='timerefresh_post_save_signal')



        self.logger = logging.getLogger(__name__)

        self.run_ploe43_2019()

    def run_ploe41_2019(self):

        def pagina_com_logotipo(v):
            logo_camara = '/home/leandro/Câmara/logo/logo_256.jpg'
            logo_horizontal = '/home/leandro/Câmara/logo/logo_horizontal.jpg'

            packet = io.BytesIO()
            try:
                can = canvas.Canvas(
                    packet, pagesize=landscape(A4))  # landscape(A4)

                #can.setFillColorRGB(255, 255, 0, 1)
                can.setFillColorCMYK(0, 0, 0, 0, 1)
                can.rect(v['xf'], v['yf'], v['wf'], v['hf'], stroke=0, fill=1)
                can.drawImage(logo_camara, v['x'], v['y'], v['w'], v['h'])

                can.setFillColorCMYK(0, 0, 0, 0, 1)
                can.rect(v['xh'], v['yh'], v['wh'], v['hh'], stroke=0, fill=1)

                can.drawImage(logo_horizontal,
                              v['xh'], v['yh'], v['wh'], v['hh'])

                can.setFillColorCMYK(0, 0, 0, 1, 1)
                can.setFontSize(9)
                can.drawString(
                    v['xh'] + 250, v['yh'] + 45,
                    'AUTÓGRAFO Nº 641, DE 13 DE DEZEMBRO DE 2019.')

                can.save()

            except Exception as e:
                print(e)

            packet.seek(0)

            pagina = PdfFileReader(packet)
            return pagina

        arquivos = (
            (
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/autografo641.pdf',
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/autografo641__completo.pdf',
                {}
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a01.pdf',
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a01__out.pdf',
                {
                    'x': 57,
                    'y': 499,
                    'w': 93,
                    'h': 68,
                    'xf': 56,
                    'yf': 493,
                    'wf': 95,
                    'hf': 80,

                    'xh': 155,
                    'yh': 518,
                    'wh': 359,
                    'hh': 57,

                }
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a02.pdf',
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a02__out.pdf',
                {
                    'x': 57,
                    'y': 499,
                    'w': 93,
                    'h': 68,
                    'xf': 56,
                    'yf': 493,
                    'wf': 95,
                    'hf': 80,

                    'xh': 155,
                    'yh': 518,
                    'wh': 359,
                    'hh': 57,
                }
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a03.pdf',
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a03__out.pdf',
                {
                    'x': 57,
                    'y': 499,
                    'w': 93,
                    'h': 68,
                    'xf': 56,
                    'yf': 493,
                    'wf': 95,
                    'hf': 80,

                    'xh': 155,
                    'yh': 518,
                    'wh': 359,
                    'hh': 57,
                }
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a04.pdf',
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a04__out.pdf',
                {
                    'x': 57,
                    'y': 499,
                    'w': 93,
                    'h': 68,
                    'xf': 56,
                    'yf': 493,
                    'wf': 95,
                    'hf': 80,

                    'xh': 155,
                    'yh': 518,
                    'wh': 359,
                    'hh': 57,
                }
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a05.pdf',
                '/home/leandro/TEMP/autografos/PLOE-41/autografo/a05__out.pdf',
                {
                    'x': 57,
                    'y': 499,
                    'w': 93,
                    'h': 68,
                    'xf': 56,
                    'yf': 493,
                    'wf': 95,
                    'hf': 80,

                    'xh': 155,
                    'yh': 518,
                    'wh': 359,
                    'hh': 57,
                }
            ),
        )

        ofile = PdfFileWriter()
        vo = ''
        for i, o, v in arquivos:
            if not v:
                vo = o

            ifile = PdfFileReader(open(i, "rb"))

            if v:
                xy = []
                for num_page in range(ifile.getNumPages()):
                    xy.append(v)

            #xy[1] = 400, 100

            for num_page in range(ifile.getNumPages()):

                if v:
                    pl = pagina_com_logotipo(v)

                p = ifile.getPage(num_page)

                if v:
                    p.mergePage(pl.getPage(0))
                ofile.addPage(p)

        outputStream = open(vo, "wb")
        ofile.write(outputStream)
        outputStream.close()

    def run_ploe42_2019(self):

        def pagina_com_logotipo(v):
            logo_camara = '/home/leandro/Câmara/logo/logo_256.jpg'
            logo_horizontal = '/home/leandro/Câmara/logo/logo_horizontal.jpg'

            packet = io.BytesIO()
            try:
                can = canvas.Canvas(
                    packet, pagesize=landscape(A4))  # landscape(A4)

                #can.setFillColorRGB(255, 255, 0, 1)
                can.setFillColorCMYK(0, 0, 0, 0, 1)
                can.rect(v['xf'], v['yf'], v['wf'], v['hf'], stroke=0, fill=1)
                can.drawImage(logo_camara, v['x'], v['y'], v['w'], v['h'])

                can.setFillColorCMYK(0, 0, 0, 1, 1)
                can.line(v['xh'], v['yh'] - 1, v['xh'] + 400, v['yh'] - 1)

                can.setFillColorCMYK(0, 0, 0, 0, 1)
                can.rect(v['xh'], v['yh'], v['wh'], v['hh'], stroke=0, fill=1)

                can.drawImage(logo_horizontal,
                              v['xh'], v['yh'], v['wh'] - 100, v['hh'])

                can.setFillColorCMYK(0, 0, 0, 1, 1)
                can.setFontSize(9)
                can.drawString(
                    v['xh'] + 215, v['yh'] + 37,
                    'AUTÓGRAFO Nº 639, DE 13 DE DEZEMBRO DE 2019.')

                can.save()

            except Exception as e:
                print(e)

            packet.seek(0)

            pagina = PdfFileReader(packet)
            return pagina

        coordenadas = coordenadas_a01 = {
            'x': 83, 'y': 478, 'w': 115, 'h': 83,
            'xf': 80, 'yf': 475, 'wf': 121, 'hf': 95,
            'xh': 205, 'yh': 522, 'wh': 450, 'hh': 48,
        }
        coordenadas_a02 = {
            'x': 34, 'y': 478, 'w': 115, 'h': 83,
            'xf': 31, 'yf': 475, 'wf': 121, 'hf': 95,
            'xh': 158, 'yh': 522, 'wh': 450, 'hh': 48,
        }
        coordenadas_a03 = {
            'x': 59, 'y': 478, 'w': 115, 'h': 83,
            'xf': 56, 'yf': 475, 'wf': 121, 'hf': 93,
            'xh': 182, 'yh': 522, 'wh': 450, 'hh': 48,
        }
        coordenadas_a07 = {
            'x': 59, 'y': 485, 'w': 112, 'h': 83,
            'xf': 56, 'yf': 480, 'wf': 117, 'hf': 93,
            'xh': 178, 'yh': 528, 'wh': 450, 'hh': 48,
        }
        coordenadas_a08 = {
            'x': 44, 'y': 479, 'w': 112, 'h': 83,
            'xf': 41, 'yf': 476, 'wf': 117, 'hf': 93,
            'xh': 167, 'yh': 523, 'wh': 450, 'hh': 48,
        }
        arquivos = (
            (
                '/home/leandro/TEMP/autografos/PLOE-42/autografo639.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/autografo639__completo.pdf',
                {}
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-42/a01.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/a01__out.pdf',
                coordenadas_a01
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-42/a02.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/a02__out.pdf',
                coordenadas_a02
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-42/a03.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/a03__out.pdf',
                coordenadas_a03
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-42/a04.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/a04__out.pdf',
                coordenadas_a03
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-42/a05.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/a05__out.pdf',
                coordenadas_a03
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-42/a06.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/a06__out.pdf',
                coordenadas_a03
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-42/a07.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/a07__out.pdf',
                coordenadas_a07
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-42/a08.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/a08__out.pdf',
                coordenadas_a08
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-42/a09.pdf',
                '/home/leandro/TEMP/autografos/PLOE-42/a09__out.pdf',
                coordenadas_a03
            ),
        )

        ofile = PdfFileWriter()
        vo = ''
        for i, o, v in arquivos:
            if not v:
                vo = o

            ifile = PdfFileReader(open(i, "rb"))

            if v:
                xy = []
                for num_page in range(ifile.getNumPages()):
                    xy.append(v)

            #xy[1] = 400, 100

            for num_page in range(ifile.getNumPages()):

                if v:
                    pl = pagina_com_logotipo(v)

                p = ifile.getPage(num_page)

                if v:
                    p.mergePage(pl.getPage(0))
                ofile.addPage(p)

        outputStream = open(vo, "wb")
        ofile.write(outputStream)
        outputStream.close()

    def run_ploe43_2019(self):

        def pagina_com_logotipo(v):
            logo_camara = '/home/leandro/Câmara/logo/logo_256.jpg'
            logo_horizontal = '/home/leandro/Câmara/logo/logo_horizontal.jpg'

            packet = io.BytesIO()
            try:
                can = canvas.Canvas(
                    packet, pagesize=landscape(A4))  # landscape(A4)

                #can.setFillColorRGB(255, 255, 0, 1)
                can.setFillColorCMYK(0, 0, 0, 0, 1)
                can.rect(v['xf'], v['yf'], v['wf'], v['hf'], stroke=0, fill=1)
                can.drawImage(logo_camara, v['x'], v['y'], v['w'], v['h'])

                can.setFillColorCMYK(0, 0, 0, 1, 1)
                can.line(v['xh'], v['yh'] - 1, v['xh'] + 400, v['yh'] - 1)

                can.setFillColorCMYK(0, 0, 0, 0, 1)
                can.rect(v['xh'], v['yh'], v['wh'], v['hh'], stroke=0, fill=1)

                can.drawImage(logo_horizontal,
                              v['xh'], v['yh'], v['wh'] - 60, v['hh'])

                can.setFillColorCMYK(0, 0, 0, 1, 1)
                can.setFontSize(9)
                can.drawString(
                    v['xh'] + 240, v['yh'] + 50,
                    'AUTÓGRAFO Nº 640, DE 13 DE DEZEMBRO DE 2019.')

                can.save()

            except Exception as e:
                print(e)

            packet.seek(0)

            pagina = PdfFileReader(packet)
            return pagina

        coordenadas = {
            'x': 42, 'y': 478, 'w': 113, 'h': 83,
            'xf': 39, 'yf': 475, 'wf': 119, 'hf': 95,
            'xh': 163, 'yh': 505, 'wh': 450, 'hh': 65,
        }

        arquivos = (
            (
                '/home/leandro/TEMP/autografos/PLOE-43/autografo640.pdf',
                '/home/leandro/TEMP/autografos/PLOE-43/autografo640__completo.pdf',
                {}
            ),
            (
                '/home/leandro/TEMP/autografos/PLOE-43/a01.pdf',
                '/home/leandro/TEMP/autografos/PLOE-43/a01__out.pdf',
                coordenadas
            ),
        )

        ofile = PdfFileWriter()
        vo = ''
        for i, o, v in arquivos:
            if not v:
                vo = o

            ifile = PdfFileReader(open(i, "rb"))

            if v:
                xy = []
                for num_page in range(ifile.getNumPages()):
                    xy.append(v)

            #xy[1] = 400, 100

            for num_page in range(ifile.getNumPages()):

                if v:
                    pl = pagina_com_logotipo(v)

                p = ifile.getPage(num_page)

                if v:
                    p.mergePage(pl.getPage(0))
                ofile.addPage(p)

        outputStream = open(vo, "wb")
        ofile.write(outputStream)
        outputStream.close()
