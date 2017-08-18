from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.core.files.base import File
from django.core.files.temp import NamedTemporaryFile
from django.db.models.aggregates import Max
from django.http.response import Http404
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from reversion.views import RevisionMixin
from sapl.parlamentares.models import Parlamentar

from cmj.sigad import models
from cmj.sigad.models import Documento, Midia, VersaoDeMidia, Revisao, Classe


class DocumentoPmImportView(RevisionMixin, TemplateView):

    template_name = 'path/pagina_inicial.html'

    def get_codigo_classe(self, parent):

        cod__max = Classe.objects.filter(
            parent=parent).order_by('codigo').aggregate(Max('codigo'))

        return cod__max['codigo__max'] + 1 if cod__max['codigo__max'] else 1

    def get_or_create_classe(
        self,
            titulo,
            parent=None,
            visibilidade=1,
            perfil=1):

        classe = Classe.objects.filter(
            titulo=titulo,
            parent=parent).first()
        if not classe:
            classe = Classe()
            classe.codigo = self.get_codigo_classe(parent)
            classe.titulo = titulo
            classe.visibilidade = visibilidade
            classe.perfil = perfil
            classe.parent = parent
            classe.owner = self.request.user

            classe.save()
        return classe

    def get(self, request, *args, **kwargs):

        import urllib3
        import json

        # Importa ultimas notícias cadastradas e adiciona como privado
        if not request.user.is_superuser:
            raise Http404()

        func = request.GET.get('func', 'noticias')

        if func == 'fotografia':
            http = urllib3.PoolManager()

            r = http.request('GET', ('http://localhost:8080/fotografia/'
                                     'evento.do?action=evento_lista_json'))

            fotografia = self.get_or_create_classe(
                'Fotografia', perfil=models.CLASSE_ESTRUTURAL)

            jdata = json.loads(r.data.decode('utf-8'))
            jdata = jdata[0:2]

            anos = {}
            for evento in jdata:
                data = datetime.strptime(
                    evento['data'], '%Y-%m-%d %H:%M:%S.%f')
                anos[str(data.year)] = True
            anos = list(anos.keys())
            anos.sort()

            pasta_ano = {}
            for ano in anos:
                pasta_ano[ano] = self.get_or_create_classe(
                    ano, parent=fotografia, perfil=models.CLASSE_DOCUMENTAL)
                pasta_ano[ano].documento_set.all().delete()

            for evento in jdata:
                data = datetime.strptime(
                    evento['data'], '%Y-%m-%d %H:%M:%S.%f')

                ano = str(data.year)
                old_path = ('/fotografia/evento.do?action=evento_view&id=%s' %
                            evento['id'])

                documento = Documento.objects.filter(
                    old_path=old_path).first()

                if not documento:
                    documento = Documento()
                    documento.old_path = old_path
                    documento.old_json = json.dumps(evento)
                    documento.titulo = evento['epigrafe']
                    documento.descricao = evento['ementa']
                    documento.public_date = data
                    documento.classe = pasta_ano[ano]
                    documento.tipo = Documento.TPD_DOC
                    documento.owner = request.user
                    documento.save()
                    Revisao.gerar_revisao(documento, request.user)

                ordem = 0
                for midia_id_import in evento['midias']:
                    ordem += 1
                    old_path_midia = ('/fotografia/'
                                      'midia.do?action=midia_view'
                                      '&escala=Real&idImage=%s'
                                      % midia_id_import)

                    image = Documento.objects.filter(
                        old_path=old_path_midia).first()
                    if image:
                        continue

                    image = Documento()
                    image.autor = 'Hélio Domingos'
                    image.visibilidade = models.STATUS_RESTRICT_USER
                    image.ordem = ordem
                    image.titulo = 'midia'
                    image.owner = request.user
                    image.parent = documento
                    image.tipo = Documento.TPD_IMAGE
                    image.classe = pasta_ano[ano]
                    image.save()
                    Revisao.gerar_revisao(image, request.user)

                    midia = Midia()
                    midia.documento = image
                    midia.save()

                    versao = VersaoDeMidia()
                    versao.midia = midia
                    versao.owner = request.user
                    versao.content_type = 'image/jpeg'
                    versao.alinhamento = models.ALINHAMENTO_JUSTIFY
                    versao.save()

                    # TODO implementar captura de fotos sem writeCredits
                    file = http.request(
                        'GET', 'http://187.6.249.155%s' % old_path_midia)

                    img_temp = NamedTemporaryFile(delete=True)
                    img_temp.write(file.data)
                    img_temp.flush()
                    versao.file.save("image.jpg", File(img_temp), save=True)

                    print(midia_id_import)

        elif func == 'noticias':
            http = urllib3.PoolManager()

            p = 1
            s = 100
            news = []
            while True:
                print(p)
                r = http.request('GET', ('www.camarajatai.go.gov.br'
                                         '/portal/json/jsonclient/json'
                                         '?page=%s&step=%s') % (
                    p, s))

                jdata = json.loads(r.data.decode('utf-8'))

                stop = False
                for n in jdata:
                    if Documento.objects.filter(old_path=n['path']).exists():
                        stop = True
                        break

                    news.append(n)
                    # print(n['date'])

                if stop or len(jdata) < s:
                    break
                p += 1
                # break

            news.reverse()

            for n in news:

                n_date = ' '.join(n['date'].lower().split()[:2])
                if len(n_date) == 10:
                    n_date += ' 00:00:00'

                n_effective = ' '.join(n['effective'].lower().split()[:2])
                if len(n_effective) == 10:
                    n_effective += ' 00:00:00'

                gmt = n['date'].rsplit(' ', 1)[-1]

                gmt = 2 if gmt == 'gmt-2' else 3 if gmt == 'gmt-3' else 0

                d = Documento()
                try:
                    d.created = datetime.strptime(
                        n_date, '%Y/%m/%d %H:%M:%S.%f') - timedelta(hours=gmt)
                except:
                    try:
                        d.created = datetime.strptime(
                            n_date, '%Y/%m/%d %H:%M:%S') - timedelta(hours=gmt)
                    except:
                        d.created = datetime.now()

                try:
                    d.public_date = datetime.strptime(
                        n_effective, '%Y/%m/%d %H:%M:%S.%f') - timedelta(hours=gmt)
                except:
                    try:
                        d.public_date = datetime.strptime(
                            n_effective, '%Y/%m/%d %H:%M:%S') - timedelta(hours=gmt)
                    except:
                        d.public_date = datetime.now()

                d.owner = request.user
                d.descricao = n['description']
                d.titulo = n['title']
                d.visibilidade = 0 if n['review_state'] == 'published' else 99
                d.old_path = n['path']
                d.old_json = json.dumps(n)
                d.classe_id = 1
                d.save()
                Revisao.gerar_revisao(d, request.user)

                ordem = 0
                if n['image']:
                    ordem += 1
                    image = Documento()
                    image.autor = n['image_caption']
                    image.visibilidade = 0
                    image.ordem = ordem
                    image.titulo = 'midia'
                    image.owner = request.user
                    image.parent = d
                    image.tipo = Documento.TPD_IMAGE
                    image.classe_id = 1
                    image.save()
                    Revisao.gerar_revisao(image, request.user)

                    midia = Midia()
                    midia.documento = image
                    midia.save()

                    versao = VersaoDeMidia()
                    versao.midia = midia
                    versao.owner = request.user
                    versao.content_type = 'image/jpeg'
                    versao.save()

                    file = http.request('GET', ('www.camarajatai.go.gov.br%s'
                                                ) % (n['image']))

                    img_temp = NamedTemporaryFile(delete=True)
                    img_temp.write(file.data)
                    img_temp.flush()
                    versao.file.save("image.jpg", File(img_temp), save=True)

                if n['text']:
                    ordem += 1
                    texto = Documento()
                    texto.texto = n['text']
                    texto.visibilidade = 0
                    texto.ordem = ordem
                    texto.owner = request.user
                    texto.parent = d
                    texto.tipo = Documento.TPD_TEXTO

                    texto.save()
                    Revisao.gerar_revisao(texto, request.user)

        elif func == 'imagens':

            docs = Documento.objects.exclude(
                old_json__icontains='"image": ""')
            print(docs.count())
            print(docs[100].slug)

        elif func == 'urls':

            # liga as notícias aos parlamentares
            url_parts = (
                (7, 1, 1, 'Adilson-Carvalho'),
                (165, 1, 1, 'carvalhinho/noticias/'),
                (12, 1, 1, 'Vereadores/gildenicio-santos/'),
                (8, 1, 1, '/Vereadores/Joao-Rosa/'),
                (168, 1, 1, '/Vereadores/david-pires/'),
                (167, 1, 1, '/Vereadores/katia-carvalho/'),
                (166, 1, 1, '/Vereadores/jose-prado-carapo/'),
                (14, 1, 1, '/Vereadores/thiago-maggioni/'),
                (2, 1, 1, '/Vereadores/mauro-bento-filho/'),
                (9, 1, 1, '/Vereadores/Marcos-Antonio/'),
                (13, 1, 1, 'vereadores-2013-2016/vinicius-luz/'),
                (11, 1, 1, 'vereadores-2013-2016/Nilton-Cesar-Soro/'),
                (1, 1, 1, 'vereadores-2013-2016/Geovaci-Peres/'),
                (16, 1, 1, 'vereadores-2013-2016/carlos-miranda/'),
                (6, 1, 1, 'vereadores-2013-2016/Genio-Euripedes/'),

                (152, 1, 1, 'Vereadores_2009-2012/Ediglan-Maia'),
                (6, 1, 1, 'Vereadores_2009-2012/Genio-Euripedes/'),
                (4, 1, 1, 'Vereadores_2009-2012/Vilma-Feitosa/'),
                (3, 1, 1, 'Vereadores_2009-2012/Nelson-Antonio/'),
                (5, 1, 1, 'Vereadores_2009-2012/Pr-Luiz-Carlos/'),


                (6, 1, 1, 'Vereadores_2005-2008/genio-euripedes'),
                (128, 1, 1, 'Vereadores_2005-2008/alcides-fazolino'),
                (157, 1, 1, 'Vereadores_2005-2008/abimael-silva'),
                (152, 1, 1, 'Vereadores_2005-2008/ediglan-maia'),
                (155, 1, 1, 'Vereadores_2005-2008/maria-jose'),
                (156, 1, 1, 'Vereadores_2005-2008/soraia-rodrigues'),
                (154, 1, 1, 'Vereadores_2005-2008/joao-wesley'),
                (158, 1, 1, 'Vereadores_2005-2008/andre-pires'),


                (0, 1, 3, '/portal/tv/cmj-noticias/'),
                (0, 1, 4, '/portal/tv/sessoes/'),
                (0, 1, 5, '/portal/tv/fala-vereador/'),
                (0, 1, 6, '/portal/tv/a-voz-da-comunidade/'),

                (0, 1, 9, '/portal/radio/momento-camara'),
            )

            for u in url_parts:
                docs = Documento.objects.filter(
                    classe=u[1],
                    # parlamentares__isnull=True,
                    old_path__contains=u[3])

                if u[0]:
                    parlamentar = Parlamentar.objects.get(pk=u[0])

                for doc in docs:
                    if u[0]:
                        doc.parlamentares.clear()
                        doc.parlamentares.add(parlamentar)

                    if u[1] != u[2]:
                        doc.classe_id = u[2]
                        doc.save()

            Documento.objects.filter(
                old_path__startswith='/portal/radio/programacao/').delete()

            Documento.objects.filter(
                old_path__startswith='/portal/videosdiversos/').delete()

            docs = Documento.objects.filter(
                classe=1,
                parlamentares__isnull=True).exclude(
                    old_path__startswith='/portal/noticias/noticias/')

            for doc in docs:
                print(doc.old_path)

            print(docs.count())

            for doc in Documento.objects.filter(parent__isnull=False):
                for child in doc.childs.view_childs():
                    child.classe_id = doc.classe_id
                    child.save()

        elif func == 'avatars':

            import os

            http = urllib3.PoolManager()

            for p in Parlamentar.objects.all():
                p.fotografia.delete()

                mypath = '%s/sapl/public/parlamentar/%s' % (
                    settings.MEDIA_ROOT, p.pk)

                print(p.nome_parlamentar)

                if os.path.exists(mypath):
                    onlyfiles = [
                        f for f in os.listdir(mypath)
                        if os.path.isfile(os.path.join(mypath, f))]

                    for f in onlyfiles:
                        os.remove(mypath + '/' + f)

                file = http.request(
                    'GET', ('sapl.camarajatai.go.gov.br/sapl/'
                            'sapl_documentos/parlamentar/fotos/'
                            '%s_foto_parlamentar') % (p.pk, ))

                img_temp = NamedTemporaryFile(delete=True)
                img_temp.write(file.data)
                img_temp.flush()
                p.fotografia.save("image.jpg", File(img_temp), save=True)

        return TemplateView.get(self, request, *args, **kwargs)
