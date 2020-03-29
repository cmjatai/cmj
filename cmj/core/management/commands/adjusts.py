
from datetime import datetime, timedelta
import logging
import os
import shutil
import stat
import subprocess
import time

from PIL import Image
from PyPDF4.generic import IndirectObject
from PyPDF4.pdf import PdfFileReader
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import F, Q
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
from fpdf.fpdf import FPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus.paragraph import Paragraph

from cmj.core.models import OcrMyPDF
from cmj.utils import signed_name_and_date_extract
from sapl.compilacao.models import Dispositivo
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class CompressPDF:

    quality = {
        0: '/default',
        1: '/prepress',
        2: '/printer',
        3: '/ebook',
        4: '/screen'
    }

    def compress(self, compress_level, file=None, new_file=None):

        try:
            initial_size = os.path.getsize(file)

            r = subprocess.call([
                'gs',
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/prepress',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                '-dAutoRotatePages=/None',
                '-dCompressPages=true',
                '-dColorImageResolution=96',
                #'-dColorImageDownsampleType=/Bicubic',
                '-sOutputFile={}'.format(new_file),
                file]
            )

            final_size = os.path.getsize(new_file)
            ratio = 1 - (final_size / initial_size)
            print("Compression by {0:.0%}.".format(ratio))
            print("Final file size is {0:.1f}MB".format(
                final_size / 1000000))
            return True

        except Exception as error:
            print('Caught this error: ' + repr(error))
        except subprocess.CalledProcessError as e:
            print("Unexpected error:".format(e.output))
            return False


class Command(BaseCommand):

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)
        # self.run_busca_desordem_de_dispositivos()

        # self.run_ajusta_datas_de_edicao_com_certidoes()
        # self.run_ajusta_datas_de_edicao_com_data_doc()
        # self.reset_id_model(TipoDispositivoRelationship)
        # self.delete_itens_tmp_folder()

        # self.run_checkcheck_olds()
        # self.run_insert_font_pdf_file__test3()

        # self.run_veririca_pdf_tem_assinatura()

        self.run_capture_fields_from_pdf()

    def run_capture_fields_from_pdf(self):
        models = (
            (NormaJuridica, 'ano__gte', 2019),
            (MateriaLegislativa, 'ano__gte',  2020),
            (DocumentoAcessorio, 'data__year__gte',  2014),
            (DocumentoAdministrativo, 'ano__gte',  2014),
            (DocumentoAcessorioAdministrativo,  'data__year__gte',  2014),
        )

        for m in models:
            qs = m.objects.filter(ano__gte=2010)
            for item in qs:
                if not hasattr(item, 'FIELDFILE_NAME') or not hasattr(item, 'metadata'):
                    break
                metadata = item.metadata
                for fn in m.FIELDFILE_NAME:  # fn -> field_name
                    ff = getattr(item, fn)  # ff -> file_field

                    if not ff.storage.exists(ff.name):
                        continue

                    original_absolute_path = '{}/original__{}'.format(
                        ff.storage.location,
                        ff.name)

                    file = open(original_absolute_path, "rb")
                    signs = signed_name_and_date_extract(file)
                    file.close()

                    if not metadata:
                        metadata = {'signs': {}}

                    if 'signs' not in metadata:
                        metadata['signs'] = {}

                    metadata['signs'][fn] = signs

                item.metadata = metadata
                item.save()

    def run_veririca_pdf_tem_assinatura(self):
        global sss
        sss = 1

        def tree_print(field_name, fields):
            global sss
            ss = " "
            print(ss * sss, field_name, '.............')
            if not isinstance(fields, dict):
                if field_name == '/Contents':
                    with open('/home/leandro/Downloads/content{}.ext'.format(sss), 'wb') as f:
                        f.write(fields)
                        f.close()
                    return
                else:
                    print(' ' * sss, fields)
                    return
            for field_name, value in fields.items():
                sss += 2
                tree_print(field_name, value)
                sss -= 2

        ifile = '/home/leandro/Downloads/portaria_23_duas_assinaturas.pdf'
        ifile = '/home/leandro/Downloads/Ofício Major sobre PLOE 13-2020.pdf'
        o_path = '/home/leandro/Downloads/'

        r = PdfFileReader(open(ifile, "rb"))

        fields = r.getFields()

        tree_print('file', fields)

        #self.get_all_images_sign(r, o_path)

    def get_all_images_sign(self, r, o_path):
        global img_count

        img_count = 0
        o_path = o_path + 'img{}{}'

        def busca_imagem(node):
            global img_count

            if isinstance(node, IndirectObject):
                node = node.getObject()

            if not isinstance(node, dict):
                return

            if '/Type' in node and node['/Type'] == '/XObject' and\
                    '/Subtype' in node and node['/Subtype'] == '/Image':
                size = (node['/Width'], node['/Height'])
                data = node.getData()

                if node['/ColorSpace'] == '/DeviceRGB':
                    mode = "RGB"
                elif node['/ColorSpace'] == '/DeviceGray':
                    return
                else:
                    mode = "P"

                try:
                    if '/Filter' in node:
                        if node['/Filter'] == '/FlateDecode':
                            img = Image.frombytes(mode, size, data)
                            img.save(o_path.format(img_count, ".png"))
                        elif node['/Filter'] == '/DCTDecode':
                            img = open(o_path .format(img_count, ".jpg"), "wb")
                            img.write(data)
                            img.close()
                        elif node['/Filter'] == '/JPXDecode':
                            img = open(o_path.format(img_count, ".jp2"), "wb")
                            img.write(data)
                            img.close()
                        elif node['/Filter'] == '/CCITTFaxDecode':
                            img = open(o_path.format(img_count, ".tiff"), "wb")
                            img.write(data)
                            img.close()
                    else:
                        img = Image.frombytes(mode, size, data)
                        img.save(o_path.format(img_count, ".png"))
                    img_count += 1
                except Exception as e:
                    print(e)

            for key, value in node.items():
                busca_imagem(value)

        pageNo = 0
        while (pageNo < r.numPages):
            page = r.getPage(pageNo)

            if '/Annots' not in page:
                pageNo += 1
                continue

            for annot in page['/Annots']:

                obj_annot = annot.getObject()
                if '/AP' not in obj_annot or '/N' not in obj_annot['/AP']:
                    continue

                node = obj_annot['/AP']['/N'].getObject()

                busca_imagem(node)

            pageNo += 1

    def get_all_images(self, r, o_path):
        pageNo = 0
        while (pageNo < r.numPages):
            page = r.getPage(pageNo)

            if '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].getObject()

                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        size = (xObject[obj]['/Width'],
                                xObject[obj]['/Height'])
                        data = xObject[obj].getData()

                        if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                            mode = "RGB"
                        else:
                            mode = "P"

                        if '/Filter' in xObject[obj]:
                            if xObject[obj]['/Filter'] == '/FlateDecode':
                                img = Image.frombytes(mode, size, data)
                                img.save(o_path + obj[1:] + ".png")
                            elif xObject[obj]['/Filter'] == '/DCTDecode':
                                img = open(o_path + obj[1:] + ".jpg", "wb")
                                img.write(data)
                                img.close()
                            elif xObject[obj]['/Filter'] == '/JPXDecode':
                                img = open(o_path + obj[1:] + ".jp2", "wb")
                                img.write(data)
                                img.close()
                            elif xObject[obj]['/Filter'] == '/CCITTFaxDecode':
                                img = open(o_path + obj[1:] + ".tiff", "wb")
                                img.write(data)
                                img.close()
                        else:
                            img = Image.frombytes(mode, size, data)
                            img.save(o_path + obj[1:] + ".png")
            else:
                print("No image found.")

            pageNo += 1

        pass

    def run_insert_font_pdf_file__test3(self):
        ifile = '/home/leandro/TEMP/4084__com_fonte__.pdf'
        pdf = open(ifile)

        for p in pdf:
            fl = p.getFontList()
            for f in fl:
                print(f)

    def run_insert_font_pdf_file__test2(self):
        helvetica_font = settings.FONTS_DIR.child('Helvetica.ttf')

        ifile = '/home/leandro/TEMP/4084.pdf'

        style = getSampleStyleSheet()
        width, height = A4
        c = canvas.Canvas(ofile, pagesize=A4)
        pdfmetrics.registerFont(TTFont("Helvetica", helvetica_font))

        cmj_string = '<font name="Helvetica" size="16">%s</font>'
        cmj_string = cmj_string % "CMJ DOC"

        p = Paragraph(cmj_string, style=style["Normal"])
        p.wrapOn(c, width, height)
        p.drawOn(c, 20, 750, mm)

        c.save()

    def run_insert_font_pdf_file__test1(self):
        helvetica_font = settings.FONTS_DIR.child('Helvetica.ttf')

        ifile = '/home/leandro/TEMP/4084.pdf'
        ofile = '/home/leandro/TEMP/4084__com_fonte.pdf'

        ppdf = FPDF()
        ppdf.add_font('helvetica', style='', fname=helvetica_font, uni=True)

        ppdf.set_font('helvetica')
        ppdf.output(ofile, 'F')

    def run_checkcheck_olds(self):
        MateriaLegislativa.objects.filter(
            ano__lte=2012).update(checkcheck=True)

    def run_invalida_checkcheck_projeto_com_norma_nao_viculada_a_autografo(self):
        materias = MateriaLegislativa.objects.filter(
            normajuridica__tipo_id=1,
            normajuridica__ano__gte=2014
        ).exclude(
            normajuridica__norma_relacionada__norma_relacionada__tipo_id=27)

        # print(materias.count())
        for m in materias:
            try:
                m.checkcheck = False
                m.save()
            except Exception as e:
                print(e)
            # print(m.normajuridica())

    def delete_itens_tmp_folder(self):
        list = os.scandir('/home/leandro/desenvolvimento/envs/cmj/tmp/')

        now = time.time()
        for i in list:
            age = now - os.stat(i.path)[stat.ST_MTIME]

            if age > 86400:
                if i.name.startswith('pymp') or\
                        i.name.startswith('com.github.ocrmypdf'):
                    shutil.rmtree(i.path, ignore_errors=True)

    def reset_id_model(self, model):

        query = """SELECT setval(pg_get_serial_sequence('"%(app_model_name)s"','id'),
                    coalesce(max("id"), 1), max("id") IS NOT null) 
                    FROM "%(app_model_name)s";
                """ % {
            'app_model_name': _get_registration_key(model)
        }

        with connection.cursor() as cursor:
            cursor.execute(query)
            # get all the rows as a list
            rows = cursor.fetchall()
            print(rows)

    def run_distibui_ocr_ao_longo_do_ano(self):
        ocrs = OcrMyPDF.objects.all().order_by('id')

        c = ocrs.count()
        d = timezone.now() - timedelta(days=365, seconds=120)
        i = 31536000 // c
        for o in ocrs:
            concluido_interval = o.concluido - o.created
            o.created = d
            o.concluido = d + concluido_interval
            o.save()

            d = d + timedelta(seconds=i)

    def run_import_check_check(self):
        from cmj.s3_to_cmj.models import S3MateriaLegislativa

        materias_antigas = S3MateriaLegislativa.objects.filter(
            checkcheck=1,
            ind_excluido=0)

        for m_old in materias_antigas:
            try:
                m_new = MateriaLegislativa.objects.get(pk=m_old.cod_materia)
            except:
                pass
            else:
                m_new.checkcheck = True
                m_new.save()
                print(m_new)

    def run_testa_ghostscript(self):
        m = MateriaLegislativa.objects.get(pk=13576)

        file_path = m.texto_original.file.name

        p = CompressPDF()
        p.compress(0, file_path, file_path + '__0__new.pdf')
        #p.compress(1, file_path, file_path + '__1__new.pdf')
        #p.compress(2, file_path, file_path + '__2__new.pdf')
        #p.compress(3, file_path, file_path + '__3__new.pdf')
        #p.compress(4, file_path, file_path + '__4__new.pdf')

    def run_ajusta_datas_de_edicao_com_certidoes(self):

        # Área de trabalho pública
        docs = DocumentoAdministrativo.objects.filter(
            workspace_id=22).order_by('-id')

        for d in docs:
            c = d.certidao

            if c:
                d.data_ultima_atualizacao = c.created
                d.save()
                continue

            print(d.epigrafe)

            if not d.documento_principal_set.exists():
                continue

            da = d.documento_principal_set.first()

            if da and da.documento_anexado.certidao:
                d.data_ultima_atualizacao = da.documento_anexado.certidao.created
                d.save()

    def run_ajusta_datas_de_edicao_com_data_doc(self):

        # Áreas de trabalho específicas
        docs = DocumentoAdministrativo.objects.filter(
            workspace_id=21).order_by('-id')

        for d in docs:

            #v = Version.objects.get_for_object(d)

            # if v.exists():
            #    d.data_ultima_atualizacao = v[0].revision.date_created
            # else:
            d.data_ultima_atualizacao = d.data
            d.save()

            """if not d.documento_principal_set.exists():
                continue

            da = d.documento_principal_set.first()

            if da and da.documento_anexado.certidao:
                d.data_ultima_atualizacao = da.documento_anexado.certidao.created
                d.save()"""

    def run_busca_desordem_de_dispositivos(self):
        init = datetime.now()

        nodelist = Dispositivo.objects.filter(
            dispositivo_pai__isnull=True).order_by('ta', 'ordem')

        def busca(nl):
            numero = []

            for nd in nl:

                busca(nd.dispositivos_filhos_set.all())

                if nd.contagem_continua:
                    continue

                if not numero:
                    numero = nd.get_numero_completo()
                    continue

                if nd.get_numero_completo() < numero:
                    print(nd.ta_id, nd.ordem, nd.id, ', '.join(
                        map(str, nd.get_parents_asc())))

                numero = nd.get_numero_completo()

        busca(nodelist)
