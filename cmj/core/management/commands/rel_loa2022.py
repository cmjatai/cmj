import io
import logging

import PyPDF4
from PyPDF4.pdf import PdfFileReader, PdfFileWriter
from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete, post_save
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.utils import open_and_read
from reportlab.pdfgen import canvas


class Command(BaseCommand):

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='timerefresh_post_delete_signal')
        post_save.disconnect(dispatch_uid='timerefresh_post_save_signal')



        self.logger = logging.getLogger(__name__)

        self.run_autografo(
            arquivos=self.get_parametros_845(),
            epigrafe='AUTÓGRAFO Nº 845, DE 16 DE DEZEMBRO DE 2021.',
            partes_ou_completo='C'
        )

        self.run_autografo(
            arquivos=self.get_parametros_846(),
            epigrafe='AUTÓGRAFO Nº 846, DE 16 DE DEZEMBRO DE 2021.',
            partes_ou_completo='C'
        )

        self.run_autografo(
            arquivos=self.get_parametros_847(),
            epigrafe='AUTÓGRAFO Nº 847, DE 16 DE DEZEMBRO DE 2021.',
            partes_ou_completo='C'
        )

    def get_parametros_846(self):

        coordenadas = [
            (
                0,
                {
                    'x': 57, 'y': 497, 'w': 92, 'h': 70,  # logotipo
                    'xf': 55, 'yf': 493, 'wf': 96, 'hf': 80,  # fundo do logotipo
                    'xh': 155, 'yh': 518, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 155, 'yfh': 518, 'wfh': 359, 'hfh': 57,  # fundo do cabeçalho
                }
            ),


        ]

        arquivos = [(
            '/home/leandro/Câmara/autografos/2021/846/aut_846.pdf',
            '/home/leandro/Câmara/autografos/2021/aut_846__completo.pdf',
            {}
        ),
        ]
        for i in range(1, 15):
            arquivos.append(
                (
                    f'/home/leandro/Câmara/autografos/2021/846/anexo/{i}.pdf',
                    f'/home/leandro/Câmara/autografos/2021/846/anexo/{i}_out.pdf',
                    coordenadas
                ),
            )

        return arquivos

    def get_parametros_847(self):

        coordenadas = [
            (
                81,
                {
                    'x': 84, 'y': 476, 'w': 115, 'h': 90,  # logotipo
                    'xf': 82, 'yf': 475, 'wf': 118, 'hf': 94,  # fundo do logotipo
                    'xh': 207, 'yh': 511, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 206, 'yfh': 507, 'wfh': 450, 'hfh': 62,  # fundo do cabeçalho
                }
            ),
            (
                80,
                {
                    'x': 42, 'y': 476, 'w': 115, 'h': 90,  # logotipo
                    'xf': 40, 'yf': 475, 'wf': 118, 'hf': 94,  # fundo do logotipo
                    'xh': 165, 'yh': 511, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 165, 'yfh': 509, 'wfh': 450, 'hfh': 60,  # fundo do cabeçalho
                }
            ),
            (
                72,
                {
                    'x': 57, 'y': 481, 'w': 115, 'h': 90,  # logotipo
                    'xf': 56, 'yf': 480, 'wf': 116, 'hf': 94,  # fundo do logotipo
                    'xh': 177, 'yh': 515, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 177, 'yfh': 515, 'wfh': 450, 'hfh': 57,  # fundo do cabeçalho
                }
            ),
            (
                68,
                {
                    'x': 58, 'y': 477, 'w': 117, 'h': 90,  # logotipo
                    'xf': 57, 'yf': 475, 'wf': 119, 'hf': 94,  # fundo do logotipo
                    'xh': 183, 'yh': 509, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 183, 'yfh': 505, 'wfh': 450, 'hfh': 63,  # fundo do cabeçalho
                }
            ),

            (
                67,
                {
                    'x': 33, 'y': 477, 'w': 117, 'h': 90,  # logotipo
                    'xf': 32, 'yf': 475, 'wf': 119, 'hf': 94,  # fundo do logotipo
                    'xh': 157, 'yh': 509, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 156, 'yfh': 502, 'wfh': 450, 'hfh': 67,  # fundo do cabeçalho
                }
            ),

            (
                56,
                {
                    'x': 40, 'y': 477, 'w': 117, 'h': 90,  # logotipo
                    'xf': 39, 'yf': 475, 'wf': 119, 'hf': 94,  # fundo do logotipo
                    'xh': 167, 'yh': 509, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 166, 'yfh': 502, 'wfh': 450, 'hfh': 67,  # fundo do cabeçalho
                }
            ),

            (
                54,
                {
                    'x': 57, 'y': 495, 'w': 92, 'h': 70,  # logotipo
                    'xf': 55, 'yf': 487, 'wf': 96, 'hf': 83,  # fundo do logotipo
                    'xh': 155, 'yh': 513, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 155, 'yfh': 513, 'wfh': 359, 'hfh': 57,  # fundo do cabeçalho
                }
            ),


            (
                27,
                {
                    'x': 50, 'y': 478, 'w': 117, 'h': 90,  # logotipo
                    'xf': 48, 'yf': 476, 'wf': 120, 'hf': 94,  # fundo do logotipo
                    'xh': 175, 'yh': 521, 'wh': 350, 'hh': 49,  # cabeçalho horizontal
                    'xfh': 175, 'yfh': 521, 'wfh': 450, 'hfh': 49,  # fundo do cabeçalho
                }
            ),
            (
                0,
                {
                    'x': 82, 'y': 477, 'w': 117, 'h': 90,  # logotipo
                    'xf': 81, 'yf': 475, 'wf': 119, 'hf': 94,  # fundo do logotipo
                    'xh': 207, 'yh': 509, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 206, 'yfh': 502, 'wfh': 450, 'hfh': 67,  # fundo do cabeçalho
                }
            ),

        ]

        arquivos = [(
            '/home/leandro/Câmara/autografos/2021/847/aut_847.pdf',
            '/home/leandro/Câmara/autografos/2021/aut_847__completo.pdf',
            {}
        ),
        ]
        for i in range(1, 14):
            arquivos.append(
                (
                    f'/home/leandro/Câmara/autografos/2021/847/anexo/{i}.pdf',
                    f'/home/leandro/Câmara/autografos/2021/847/anexo/{i}_out.pdf',
                    coordenadas
                ),
            )

        return arquivos

    def get_parametros_845(self):

        coordenadas = [
            (
                332,
                {
                    'x': 82, 'y': 477, 'w': 117, 'h': 90,  # logotipo
                    'xf': 81, 'yf': 475, 'wf': 119, 'hf': 94,  # fundo do logotipo
                    'xh': 207, 'yh': 509, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 206, 'yfh': 502, 'wfh': 450, 'hfh': 67,  # fundo do cabeçalho
                }
            ),

            (
                248,
                {
                    'x': 41, 'y': 477, 'w': 117, 'h': 90,  # logotipo
                    'xf': 39, 'yf': 475, 'wf': 119, 'hf': 94,  # fundo do logotipo
                    'xh': 166, 'yh': 507, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 164, 'yfh': 505, 'wfh': 450, 'hfh': 65,  # fundo do cabeçalho
                }
            ),

            (
                0,
                {
                    'x': 30, 'y': 488, 'w': 101, 'h': 79,  # logotipo
                    'xf': 28, 'yf': 486, 'wf': 105, 'hf': 83,  # fundo do logotipo
                    'xh': 136, 'yh': 512, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
                    'xfh': 136, 'yfh': 512, 'wfh': 359, 'hfh': 57,  # fundo do cabeçalho
                }
            ),

        ]

        arquivos = [(
            '/home/leandro/Câmara/autografos/2021/845/aut_845.pdf',
            '/home/leandro/Câmara/autografos/2021/aut_845__completo.pdf',
            {}
        ),
        ]
        for i in range(1, 9):
            arquivos.append(
                (
                    f'/home/leandro/Câmara/autografos/2021/845/anexo/{i}.pdf',
                    f'/home/leandro/Câmara/autografos/2021/845/anexo/{i}_out.pdf',
                    coordenadas
                ),
            )

        return arquivos

    def run_autografo(self, arquivos=None, epigrafe='', partes_ou_completo='C'):

        page_mask = None
        pl = None
        count_page = 0

        def pagina_com_logotipo(coord, num_page):

            nonlocal page_mask
            nonlocal pl
            nonlocal count_page

            print(count_page, num_page)

            v = None
            for p, va in coord:
                if count_page >= p:
                    v = va
                    break

            if v != page_mask:
                page_mask = v
            else:
                return pl

            logo_camara = '/home/leandro/Câmara/logo/logo_128.jpg'
            logo_horizontal = '/home/leandro/Câmara/logo/logo_horizontal_mini.jpg'

            packet = io.BytesIO()
            try:
                can = canvas.Canvas(
                    packet, pagesize=portrait(A4))  # landscape(A4)
                # can.setFillColorRGB(255, 255, 0, 1)
                can.rotate(90)
                can.translate(0, -595)
                # can.setPageRotation(270)
                can.setFillColorCMYK(
                    0, 0, 255 if partes_ou_completo == 'P' else 0, 0, 1)
                """can.setStrokeColorCMYK(
                    0, 0, 255 if partes_ou_completo == 'P' else 0, 0, 1)"""
                #can.rect(0, 0, 842, 595, stroke=0, fill=1)
                can.rect(v['xf'], v['yf'], v['wf'], v['hf'], stroke=0, fill=1)
                can.drawImage(logo_camara, v['x'], v['y'], v['w'], v['h'])

                can.setFillColorCMYK(
                    0, 0, 255 if partes_ou_completo == 'P' else 0, 0,  1)

                can.rect(v['xfh'], v['yfh'], v['wfh'],
                         v['hfh'], stroke=0, fill=1)

                can.drawImage(logo_horizontal,
                              v['xh'], v['yh'], v['wh'], v['hh'])

                can.setFillColorCMYK(0, 0, 0, 1, 1)
                can.setFontSize(9)
                can.drawString(v['xh'] + v['wh'] * 0.62,
                               v['yh'] + v['hh'] - 12, epigrafe)

                can.save()

            except Exception as e:

                print(e)

            packet.seek(0)

            pagina = PdfFileReader(packet)
            return pagina

        if partes_ou_completo == 'P':
            vo = ''

            for i, o, coord in arquivos:
                print(i)
                ofile = PdfFileWriter()
                vo = o

                ifile = PdfFileReader(open(i, "rb"))

                if coord:
                    xy = []
                    for num_page in range(ifile.getNumPages()):
                        xy.append(coord)

                page_mask = None
                pl = None
                for num_page in range(ifile.getNumPages()):

                    """if num_page < 0:
                        continue

                    if num_page > 0:
                        break"""

                    if coord:
                        pl = pagina_com_logotipo(coord, num_page)
                        count_page += 1

                    p = ifile.getPage(num_page)
                    if coord:
                        p.mergePage(pl.getPage(0))
                        #p.mergeRotatedPage(pl.getPage(0), 90, False)

                    ofile.addPage(p)

                outputStream = open(vo, "wb")
                ofile.write(outputStream)
                outputStream.close()
        else:

            ofile = PdfFileWriter()
            vo = ''

            for i, o, coord in arquivos:
                if not coord:
                    vo = o

                ifile = PdfFileReader(open(i, "rb"))

                page_mask = None
                pl = None
                for num_page in range(ifile.getNumPages()):

                    if coord:
                        pl = pagina_com_logotipo(coord, num_page)
                        count_page += 1

                    p = ifile.getPage(num_page)
                    if coord:
                        p.mergePage(pl.getPage(0))

                    ofile.addPage(p)

            outputStream = open(vo, "wb")
            ofile.write(outputStream)
            outputStream.close()
