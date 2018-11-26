from django.core.management.base import BaseCommand
from django.db import connection, connections

from cmj.s3_to_cmj.models import _NormaJuridica, _Tramitacao,\
    _MateriaLegislativa


def replaceCaracteres(texto):

    autOld = "ãâáàäeêéèëiîíìïõôóòöuûúùüçÃÂÁÀÄEÊÉÈËIÎÍÌÏÕÔÓÒÖUÛÚÙÜÇ"
    autNew = "aaaaaeeeeeiiiiiooooouuuuucaaaaaeeeeeiiiiiooooouuuuuc"

    for o, n in zip(autOld, autNew):
        texto = texto.replace(o, n)

    return texto


def stopWords(texto):

    stops = ('"', "'", '?', '`', ',', '.', '§', '“', ':')

    for st in stops:
        texto = texto.replace(st, '')

    texto = texto.strip()

    stops = ('(', ')', ' \o ', ' \e ', ' \a ',  ' n ', 's ', 'S ', ' do ',
             ' da ', ' - ', '-', '.º',  'º',  '\r\n', '\t',
             '\r', '\n', '      ', '     ', '    ', '   ', '  ',
             '<b>', '</b>', '; ')

    for st in stops:
        texto = texto.replace(st, ' ')

    return texto


class Command(BaseCommand):

    def handle(self, *args, **options):
        """autografos = _NormaJuridica.objects.filter(
            tip_norma=27,
            ano_norma__lte=2017,
            checkcheck=False,
            ind_excluido=0
        ).order_by('num_norma')

        for a in autografos:

            check = True
            if not a.cod_materia:
                print(a.num_norma, 'não tem matéria vinculada')
                check = False

            vinculo = _VinculoNormaJuridica.objects.filter(
                cod_norma_referida=a.cod_norma,
                ind_excluido=0).first()

            if not vinculo:
                # Se autografo não tem vínvulo não checa
                print(a.num_norma, a.cod_materia, 'não norma vínculada')
                check = False
                continue

            norma = _NormaJuridica.objects.filter(
                ind_excluido=0,
                cod_norma=vinculo.cod_norma_referente).first()

            if not norma or a.cod_materia != norma.cod_materia:
                # se a matéria da norma vinculada ao autógrafo é diferente da
                # matéria vinculada a norma vinculada, não checa
                print(a.num_norma, a.cod_materia,
                      norma.num_norma, norma.cod_materia, 'materia do autografo diferente da matéria da norma')
                check = False

            trt = _Tramitacao.objects.filter(
                cod_materia=a.cod_materia,
                ind_excluido=0).order_by('cod_tramitacao').last()

            if not trt:
                print(a.cod_materia, 'Não tem tramitação')
                check = False
                continue

            if '{}.{}/{}'.format(
                    str(norma.num_norma)[0:-3],
                    str(norma.num_norma)[-3:],
                norma.ano_norma) not in trt.txt_tramitacao and\
                '{},{}/{}'.format(
                    str(norma.num_norma)[0:-3],
                    str(norma.num_norma)[-3:],
                norma.ano_norma) not in trt.txt_tramitacao and\
                '{}.{}'.format(
                    str(norma.num_norma)[0:-3],
                    str(norma.num_norma)[-3:]) not in trt.txt_tramitacao and\
                '{}'.format(norma.ano_norma) not in trt.txt_tramitacao and \
                '{}/{}'.format(
                    norma.num_norma,
                    norma.ano_norma) not in trt.txt_tramitacao:
                print(a.num_norma, a.cod_materia,
                      '{}.{}/{} não está em {}'.format(
                          str(norma.num_norma)[0:-3],
                          str(norma.num_norma)[-3:],
                          norma.ano_norma,
                          trt.txt_tramitacao)
                      )
                check = False

            if check:

                query = 'update norma_juridica set 
                     checkcheck=true where cod_norma={};'.format(a.cod_norma)

                with connections['s3'].cursor() as cursor:
                    cursor.execute(query)

                query = 'update materia_legislativa set 
                     checkcheck=true where cod_materia={};'.format(a.cod_materia)

                with connections['s3'].cursor() as cursor:
                    cursor.execute(query)"""

        print('----------------------------')

        ano_base = 2017
        return

        materias = _MateriaLegislativa.objects.filter(
            ano_ident_basica__lte=ano_base,
            checkcheck=False,
            ind_excluido=0
        ).order_by('ano_ident_basica', 'dat_apresentacao')

        cod_status = set()
        for mat in materias:

            check = True
            if not mat.num_ident_basica:
                print(mat.cod_materia, 'sem numero de indentificacao')
                check = False

            trt = _Tramitacao.objects.filter(
                cod_materia=mat.cod_materia,
                ind_excluido=0).order_by('cod_tramitacao').last()

            """if not trt and mat.tip_id_basica == 12:
                self.checkcheck(mat.cod_materia)
                continue"""

            if trt and trt.cod_status == 27:
                self.checkcheck(mat.cod_materia)
                continue

            norma = _NormaJuridica.objects.filter(
                ind_excluido=0,
                cod_materia=mat.cod_materia)

            if norma.count() != 1:
                check = False

            if norma.count() == 1:
                norma = norma[0]

                txt_norma = norma.txt_ementa
                txt_materia = mat.txt_ementa

                # self.checkcheck(mat.cod_materia)
                print('----------------')
                similar = self.verifica_similaridade(txt_materia, txt_norma)
                print(mat.cod_materia, similar)

                if similar == 100 and trt.cod_status == 44 and mat.tip_id_basica == 6:
                    self.checkcheck(mat.cod_materia)

            """
                    print(mat.cod_materia, mat.num_ident_basica,
                          mat.tip_id_basica, 'exatamente igual a norma')
            
            if trt and trt.cod_status:
                cod_status.add(trt.cod_status)

            if mat.tip_id_basica == 3 and trt and trt.cod_status != 4:
                self.checkcheck(mat.cod_materia)
            if mat.tip_id_basica == 2 and trt and trt.cod_status != 4:
                self.checkcheck(mat.cod_materia)

            if mat.tip_id_basica == 6:
                self.checkcheck(mat.cod_materia) 

            if trt and trt.cod_status == 14:
                self.checkcheck(mat.cod_materia) 
                print(mat.cod_materia, mat.num_ident_basica,
                      mat.tip_id_basica, 'status arquivada')
                       """

            if check:
                # self.checkcheck(mat.cod_materia)
                pass
        print(list(cod_status))

    def verifica_similaridade(self, w1, w2):

        w1 = stopWords(w1)
        w2 = stopWords(w2)

        w1 = replaceCaracteres(w1)
        w1 = replaceCaracteres(w1)
        w1 = replaceCaracteres(w1)
        w2 = replaceCaracteres(w2)
        w2 = replaceCaracteres(w2)
        w2 = replaceCaracteres(w2)

        w1 = w1.lower()
        w2 = w2.lower()

        w1 = w1 + ' ' * (len(w2) - len(w1))
        w2 = w2 + ' ' * (len(w1) - len(w2))

        print(w1)
        print(w2)

        count = 0

        for i, j in zip(w1, w2):
            if i == j:
                count = count + 1

        return int((count / float(len(w1))) * 100)

    def checkcheck(self, cod_materia):

        query = """update materia_legislativa set 
        checkcheck=true where cod_materia={};""".format(cod_materia)

        with connections['s3'].cursor() as cursor:
            cursor.execute(query)
