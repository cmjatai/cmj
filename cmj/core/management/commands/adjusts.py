
from datetime import datetime, timedelta, date
import json
import logging
import os
from pickle import FALSE

from django.apps.registry import apps
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.db.models.fields.files import FileField
from django.db.models.signals import post_delete, post_save
from django.utils import timezone

from cmj.core.models import OcrMyPDF
from cmj.diarios.models import DiarioOficial
from cmj.signals import Manutencao
from sapl.compilacao.models import Dispositivo, TextoArticulado,\
    TipoDispositivo
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio,\
    Tramitacao
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.forms import pega_ultima_tramitacao_adm
from sapl.protocoloadm.models import DocumentoAdministrativo, Protocolo,\
    DocumentoAcessorioAdministrativo, TramitacaoAdministrativo,\
    StatusTramitacaoAdministrativo
from sapl.sessao.models import SessaoPlenaria


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):
        m = Manutencao()
        m.desativa_auto_now()
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        self.organiza_docs_adms()

        # self.count_registers(full=False)

        # self.run_busca_desordem_de_dispositivos()

        # self.run_ajusta_datas_de_edicao_com_certidoes()
        # self.run_ajusta_datas_de_edicao_com_data_doc()
        # self.delete_itens_tmp_folder()

        # self.run_checkcheck_olds()
        # self.run_insert_font_pdf_file__test3()

        # self.run_veririca_pdf_tem_assinatura()

        # self.run_capture_fields_from_pdf()
        # self.associa_tipo_conteudo_gerado__e__conteudo_gerado()

        # self.ajuste_metadata_com_set_values()
        # with
        # open('/home/leandro/desenvolvimento/envs/cmj_media_local/media/original__sapl/private/materialegislativa/2020/17709/teste.pdf',
        # 'rb') as f:

        # with
        # open('/home/leandro/Downloads/requerimento_cpi-_2020_major_2_32.pdf',
        # 'rb') as f:

        # with
        # open('/home/leandro/Downloads/plol_-_processos_eletronicos_-2020.pdf',
        # 'rb') as f:
        # with open('/home/leandro/TEMP/teste.pdf', 'rb') as f:
        #    signed_name_and_date_extract(f)

        # self.ajuste_metadata_com_set_values()
        # self.run_liga_norma_a_diario()

        # veiculo_publicacao='',
        # with transaction.atomic():
        #    reset_id_model(AuditLog)

    def organiza_docs_adms(self):
        print('organiza_docs_adms')
        for d in DocumentoAdministrativo.objects.filter(
                workspace_id=22,
                # tramitacaoadministrativo__isnull=True,
                # anexo_de__isnull=True,
                # anexados__isnull=False,
                id=5346
        ).distinct().order_by('-id'):
            print(d.id, d)

    def vincular_materia_norma(self):

        for n in NormaJuridica.objects.filter(
                tipo__origem_processo_legislativo=True,
                materia__isnull=True
        ):
            print(n)

    def count_registers(self, full=True):

        print('--------- CountRegisters ----------')

        for app in apps.get_app_configs():
            for m in app.get_models():
                count = m.objects.all().count()
                if full or count > 100000:
                    print(count, m, app)

    def ajuste_metadata_com_set_values(self):
        for app in apps.get_app_configs():

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            print(app)

            for m in app.get_models():
                model_exec = False

                for f in m._meta.get_fields():
                    dua = f
                    print(dua)
                    if hasattr(dua, 'auto_now') and dua.auto_now:
                        #print(m, 'auto_now deve ser desativado.')
                        # continue  # auto_now deve ser desativado
                        print(m, 'desativando auto_now')
                        dua.auto_now = False

                    if not isinstance(f, FileField):
                        continue

                    # se possui FileField, o model então
                    # deve possuir FIELDFILE_NAME
                    assert hasattr(m, 'FIELDFILE_NAME'), '{} não possui FIELDFILE_NAME'.format(
                        m._meta.label)

                    # se possui FileField, o model então
                    # deve possuir metadata
                    assert hasattr(m, 'metadata'), '{} não possui metadata'.format(
                        m._meta.label)

                    # o campo field deve estar em FIELDFILE_NAME
                    assert f.name in m.FIELDFILE_NAME, '{} não está no FIELDFILE_NAME de {}'.format(
                        f.name,
                        m._meta.label)

                    model_exec = True

                if not model_exec:
                    continue

                print(m, m.objects.all().count())

                # if m != DocumentoAdministrativo:
                #    continue

                for i in m.objects.all().order_by('-id'):  # [:500]:

                    if not hasattr(i, 'metadata'):
                        continue

                    metadata = i.metadata if i.metadata else {}
                    for fn in i.FIELDFILE_NAME:

                        ff = getattr(i, fn)
                        if not ff:
                            continue

                        if not os.path.exists(ff.path):
                            print('Arquivo registrado mas não existe', i.id, i)
                            continue

                        if not metadata:
                            continue

                        if 'signs' not in metadata:
                            continue

                        if fn not in metadata['signs']:
                            continue

                        if not metadata['signs'][fn]:
                            print(i)
                            i.save()

    def associa_tipo_conteudo_gerado__e__conteudo_gerado(self):

        protocolos = Protocolo.objects.all()

        count = 0
        for p in protocolos:
            if p.tipo_documento:
                p.tipo_conteudo_protocolado = p.tipo_documento
                p.conteudo_protocolado = p.documentoadministrativo_set.first()
                p.save()

            elif p.tipo_materia:
                p.tipo_conteudo_protocolado = p.tipo_materia

                materia = MateriaLegislativa.objects.filter(
                    numero_protocolo=p.numero,
                    ano=p.ano).first()

                if materia:
                    p.conteudo_protocolado = materia
                p.save()

    def run_insere_ementa_em_textos_articulados_que_o_cadastro_esqueceu(self):
        for t in TextoArticulado.objects.exclude(dispositivos_set__tipo_dispositivo=2):
            dsps = t.dispositivos_set.order_by('ordem')
            if not dsps.exists():
                continue
            tipo_ementa = TipoDispositivo.objects.get(pk=2)
            articulacao = dsps[0]
            ordem = articulacao.criar_espaco(1)
            ementa = Dispositivo.new_instance_based_on(
                articulacao, tipo_ementa)
            ementa.ordem = ordem
            ementa.texto = t.ementa
            ementa.save()

    def run_capture_fields_from_pdf(self):
        models = (
            (NormaJuridica, 'ano__gte', 2020, 'data_ultima_atualizacao'),
            (MateriaLegislativa, 'ano__gte',  2020, 'data_ultima_atualizacao'),
            (DocumentoAdministrativo, 'ano__gte', 2020, 'data_ultima_atualizacao'),
            (DocumentoAcessorio, 'data__year__gte',
             2020, 'data_ultima_atualizacao'),
            (DocumentoAcessorioAdministrativo,  'data__year__gte',  2020, ''),
            (SessaoPlenaria,  'data_inicio__year__gte',
             2020, 'data_ultima_atualizacao'),
            (DiarioOficial,  'data__year__gte', 2020, 'data_ultima_atualizacao'),
        )

        for model in models:
            m = model[0]

            if model[3]:
                dua = m._meta.get_field(model[3])
                if hasattr(dua, 'auto_now') and dua.auto_now:
                    #print(m, 'auto_now deve ser desativado.')
                    # continue  # auto_now deve ser desativado
                    print(m, 'desativando auto_now')
                    dua.auto_now = False

            params = {
                model[1]: model[2]
            }

            qs = m.objects.filter(**params)
            for item in qs:
                print(item)
                item.save()  # o pre_save fará a caputra da assinatura
                # LEMBRAR QUE auto_now DEVE SER DESATIVADO
                """if not hasattr(item, 'FIELDFILE_NAME') or not hasattr(item, 'metadata'):
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
                item.save()"""

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
