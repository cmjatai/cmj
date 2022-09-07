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

        """self.run_autografo(
            arquivos=self.get_parametros_711(),
            epigrafe='AUTÓGRAFO Nº 711, DE 04 DE DEZEMBRO DE 2020.',
            partes_ou_completo='C'
        )

        self.run_autografo(
            arquivos=self.get_parametros_712(),
            epigrafe='AUTÓGRAFO Nº 712, DE 04 DE DEZEMBRO DE 2020.',
            partes_ou_completo='C'
        )"""

        self.run_autografo(
            arquivos=self.get_parametros_713(),
            epigrafe='AUTÓGRAFO Nº 713, DE 04 DE DEZEMBRO DE 2020.',
            partes_ou_completo='C'

        )

    def get_parametros_713(self):

        coordenadas = {
            'x': 43, 'y': 479, 'w': 112, 'h': 80,  # logotipo
            'xf': 38, 'yf': 474, 'wf': 121, 'hf': 95,  # fundo do logotipo
            'xh': 165, 'yh': 507, 'wh': 400, 'hh': 60,  # cabeçalho horizontal
            'xfh': 162, 'yfh': 500, 'wfh': 500, 'hfh': 68,  # fundo do cabeçalho
        }
        arquivos = [
            [
                '/home/leandro/Câmara/autografos/2020/713/aut_713.pdf',
                '/home/leandro/Câmara/autografos/2020/aut_713__completo.pdf',
                {}
            ],
        ]
        for i in range(1, 2):
            arquivos.append(
                [
                    f'/home/leandro/Câmara/autografos/2020/713/anexo/a{i}.pdf',
                    f'/home/leandro/Câmara/autografos/2020/713/anexo/a{i}_out.pdf',
                    coordenadas
                ],
            )
        return arquivos

    def get_parametros_712(self):

        coordenadas = {
            'x': 84, 'y': 479, 'w': 112, 'h': 80,  # logotipo
            'xf': 79, 'yf': 474, 'wf': 122, 'hf': 95,  # fundo do logotipo
            'xh': 205, 'yh': 521, 'wh': 362, 'hh': 48,  # cabeçalho horizontal
            'xfh': 205, 'yfh': 521, 'wfh': 362, 'hfh': 48,  # fundo do cabeçalho
        }
        arquivos = [
            [
                '/home/leandro/Câmara/autografos/2020/712/aut_712.pdf',
                '/home/leandro/Câmara/autografos/2020/aut_712__completo.pdf',
                {}
            ],
        ]
        for i in range(1, 12):
            arquivos.append(
                [
                    f'/home/leandro/Câmara/autografos/2020/712/anexo/a{i}.pdf',
                    f'/home/leandro/Câmara/autografos/2020/712/anexo/a{i}_out.pdf',
                    coordenadas
                ],
            )

        arquivos[2][2] = {
            'x': 35, 'y': 479, 'w': 112, 'h': 80,  # logotipo
            'xf': 30, 'yf': 474, 'wf': 122, 'hf': 95,  # fundo do logotipo
            'xh': 156, 'yh': 521, 'wh': 362, 'hh': 48,  # cabeçalho horizontal
            'xfh': 156, 'yfh': 521, 'wfh': 410, 'hfh': 48  # fundo do cabeçalho
        }

        arquivos[3][2] = arquivos[4][2] = arquivos[5][2] = arquivos[6][2] = {
            'x': 61, 'y': 479, 'w': 112, 'h': 80,  # logotipo
            'xf': 56, 'yf': 474, 'wf': 120, 'hf': 95,  # fundo do logotipo
            'xh': 181, 'yh': 521, 'wh': 362, 'hh': 48,  # cabeçalho horizontal
            'xfh': 181, 'yfh': 521, 'wfh': 410, 'hfh': 48,  # fundo do cabeçalho
        }

        arquivos[7][2] = {
            'x': 59, 'y': 482, 'w': 111, 'h': 85,  # logotipo
            'xf': 56, 'yf': 480, 'wf': 117, 'hf': 95,  # fundo do logotipo
            'xh': 176, 'yh': 527, 'wh': 362, 'hh': 48,  # cabeçalho horizontal
            'xfh': 176, 'yfh': 527, 'wfh': 410, 'hfh': 48,  # fundo do cabeçalho
        }

        arquivos[8][2] = {
            'x': 44, 'y': 478, 'w': 111, 'h': 85,  # logotipo
            'xf': 40, 'yf': 476, 'wf': 119, 'hf': 94,  # fundo do logotipo
            'xh': 165, 'yh': 521, 'wh': 362, 'hh': 48,  # cabeçalho horizontal
            'xfh': 165, 'yfh': 521, 'wfh': 410, 'hfh': 48,  # fundo do cabeçalho
        }

        arquivos[9][2] = {
            'x': 61, 'y': 479, 'w': 112, 'h': 80,  # logotipo
            'xf': 56, 'yf': 474, 'wf': 122, 'hf': 95,  # fundo do logotipo
            'xh': 181, 'yh': 522, 'wh': 362, 'hh': 48,  # cabeçalho horizontal
            'xfh': 181, 'yfh': 522, 'wfh': 390, 'hfh': 48,  # fundo do cabeçalho
        }

        arquivos[10][2] = arquivos[11][2] = {
            'x': 57, 'y': 493, 'w': 93, 'h': 68,  # logotipo
            'xf': 56, 'yf': 488, 'wf': 95, 'hf': 80,  # fundo do logotipo
            'xh': 155, 'yh': 513, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
            'xfh': 155, 'yfh': 513, 'wfh': 359, 'hfh': 57,  # fundo do cabeçalho
        }

        return arquivos

    def get_parametros_711(self):

        coordenadas = {
            'x': 57, 'y': 499, 'w': 93, 'h': 68,  # logotipo
            'xf': 56, 'yf': 493, 'wf': 95, 'hf': 80,  # fundo do logotipo
            'xh': 155, 'yh': 518, 'wh': 359, 'hh': 57,  # cabeçalho horizontal
            'xfh': 155, 'yfh': 518, 'wfh': 359, 'hfh': 57,  # fundo do cabeçalho
        }

        arquivos = [
            (
                '/home/leandro/Câmara/autografos/2020/711/aut_711.pdf',
                '/home/leandro/Câmara/autografos/2020/aut_711__completo.pdf',
                {}
            ),
        ]
        for i in range(1, 6):
            arquivos.append(
                (
                    f'/home/leandro/Câmara/autografos/2020/711/anexo/a{i}.pdf',
                    f'/home/leandro/Câmara/autografos/2020/711/anexo/a{i}_out.pdf',
                    coordenadas
                ),
            )

        return arquivos

    def run_autografo(self, arquivos=None, epigrafe='', partes_ou_completo='C'):

        def pagina_com_logotipo(v):
            logo_camara = '/home/leandro/Câmara/logo/logo_256.jpg'
            logo_horizontal = '/home/leandro/Câmara/logo/logo_horizontal.jpg'

            packet = io.BytesIO()
            try:
                can = canvas.Canvas(
                    packet, pagesize=landscape(A4))  # landscape(A4)

                #can.setFillColorRGB(255, 255, 0, 1)
                can.setFillColorCMYK(
                    0, 0, 255 if partes_ou_completo == 'P' else 0, 0, 1)
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
            for i, o, v in arquivos:

                ofile = PdfFileWriter()
                vo = o

                ifile = PdfFileReader(open(i, "rb"))

                if v:
                    xy = []
                    for num_page in range(ifile.getNumPages()):
                        xy.append(v)

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
        else:

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
