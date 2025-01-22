
from cmj.arq.models import ArqDoc
from cmj.diarios.models import DiarioOficial
from cmj.sigad.models import VersaoDeMidia, Documento
from cmj.utils import run_sql, time_of_period
from cmj.videos.models import Video
from sapl.compilacao.models import Dispositivo
from sapl.materia.models import MateriaLegislativa, Tramitacao, \
    DocumentoAcessorio, Proposicao
from sapl.norma.models import NormaJuridica, AnexoNormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import SessaoPlenaria, RegistroVotacao
import markdown as md

markstyles = '''<style>
.container-show{
    font-size: 18pt;
    padding-bottom: 4em;
    text-align: left;
    h1 {
        color: #00a;
    }
    h2 {
        margin-top: 1em;
    }
    p {
        text-indent: 1cm;
        margin: 5px 0;
        color: #045;
    }
    ul {
        margin: 1rem 0 0 0;
        ul {
            margin: 0;
        }
    }
    li {
        color: #045;
        p {
            margin: 0;
            text-indent: 0cm;
        }
        li {
            font-style: italic;
            color: #049;
        }
    }
}
</style>
'''
def get_fields_name(model):
    return tuple(
        map(
            lambda f: f.name,
            filter(
                lambda f: hasattr(f, 'name'), model._meta.get_fields()
            )
        )
    )


def get_size_models(models = [], s3 = 's3_aws'):
    size_total = {}
    for model, extra_sql in models:
        size = 0
        count_regs = 0
        sum_pages = 0
        FIELDFILE_NAME = getattr(model, 'FIELDFILE_NAME', tuple())

        sum__paginas = ', sum(_paginas)' if '_paginas' in get_fields_name(model) else ''

        for ffn in FIELDFILE_NAME:
            sql = f'''SELECT
                    count(id),
                    sum((metadata->'{s3}'->'{ffn}'->'size')::integer) + sum((metadata->'{s3}'->'{ffn}'->'original_size')::integer)
                    {sum__paginas}
                FROM {model._meta.db_table}
                { extra_sql if extra_sql else '' }
                ;'''
            # print(sql)
            r = run_sql(sql)
            if not count_regs:
                count_regs = r[0][0]
            size += (r[0][1] or 0)
            if len(r[0]) > 2:
                sum_pages += r[0][2]

        if not FIELDFILE_NAME:
            count_regs = model.objects.count()

        size_total[model] = {
            'size': size,
            'count': count_regs,
            'paginas': sum_pages
        }
    return size_total


def get_redessociais():
    videos_sessao = Video.objects.filter(videoparte_set__content_type__app_label = 'sessao').order_by('videoparte_set__content_type__app_label').distinct()
    videos_manha = Video.objects.filter(titulo__icontains = 'Manhã CMJ')

    video_count = Video.objects.count()
    video_sessao_count = videos_sessao.count()
    video_manha_count = videos_manha.count()
    video_duration = 0
    sessao_duration = 0
    manha_duration = 0

    likes_count = 0
    views_count = 0

    max_likes = 0
    video_max_likes = None
    max_views = 0
    video_max_views = None

    for v in Video.objects.all():

        j = v.json

        if not j or 'contentDetails' not in j or 'duration' not in j['contentDetails']:
            continue

        d = j['contentDetails']['duration']

        tp = time_of_period(d)[1]
        video_duration += tp

        if v in videos_sessao:
            sessao_duration += tp
        if v in videos_manha:
            manha_duration += tp

        s = j.get('statistics', {})
        if 'likeCount' in s:
            vc = int(s['likeCount'])
            likes_count += vc

            if vc > max_likes:
                video_max_likes = v
                max_likes = vc

        if 'viewCount' in s:
            vc = int(s['viewCount'])
            views_count += vc

            if vc > max_views:
                video_max_views = v
                max_views = vc

    size_models = get_size_models(
        models = [
            (VersaoDeMidia, ''),
        ]
    )

    mark0 = '# Publicações Institucionais no PortalCMJ e em Redes Sociais'

    mark1 = f'''
- **{ Documento.objects.filter(tipo=0).count() }** Notícias.
- **{ video_count }** Vídeos.
- **Imagens**
    - **{ Documento.objects.filter(tipo=10).count() }** Bancos de Imagens.
    - **{ Documento.objects.filter(tipo=20).count() }** Galerias de Imagens.
    - **{ size_models[VersaoDeMidia]['count'] }** Fotos.
    - **{ int(size_models[VersaoDeMidia]['size']/1024/1024/1024) } GB**.
---------------------
## [Telegram](http://t.me/cmjatai)

Matérias legislativas, notícias instituicionais e parlamentares, além de vídeos transmitidos e/ou adicionados no [Youtube](https://www.youtube.com/C%C3%A2maraMunicipalJata%C3%AD)
são enviados para o Canal da Câmara no [Telegram](http://t.me/cmjatai) de 10 a 60min após entrarem no PortalCMJ.
'''

    mark2 = f'''
## [Youtube](https://www.youtube.com/C%C3%A2maraMunicipalJata%C3%AD)

O PortalCMJ possui um algoritimo de integração com a API do Youtube
monitorando-o 24hs por dia (são mais de 10mil requisições em um só dia),
capturando número de curtidas, visualizações e novos vídeos.

Atualmente os números no Youtube são:

- Um total de **{ video_count }** Vídeos -> **{ video_duration // 3600 }** Horas.
- **{ video_sessao_count }** Sessões e/ou reuniões transmitidas -> **{ sessao_duration // 3600 }** Horas.
- **{ video_manha_count }** Programas Manhã CMJ -> **{ manha_duration // 3600 }** Horas.
---------------------

- **{views_count}** visualizações.
- **{likes_count}** likes.

---------------------

- Vídeo com maior número de likes:
    - {video_max_likes} ({max_likes} likes)

- Vídeo com maior número de visualizações:
    - {video_max_views} ({max_views} visualizações)
'''
    return (mark0, 12), (mark1, 4), (mark2, 8)


def get_estrutura_armazenamento():
    mark = f'''
# Estrutura de Armazenamento e Processamento

O PortalCMJ possui um servidor dedicado que conta com dois
processadores (Processador Intel® Xeon® E5-2620 v3) que totalizam 24 threads
trabalhando em conjunto com 32GB de memória, além das unidades de armazenamento
local que possuem 03 TeraBytes de espaço que, atualmente, com todos os registros
mencionados acima, totalizam em torno de 40% em uso da capacidade total.

## Cópias de Segurança

Como são armazenados os dados, matérias legislativas,
normas e documentos administrativos dentro do PortalCMJ?
Todo documento e/ou imagem adicionado são armazenados em cinco locais diferentes.
Esses procedimentos foram adotados para cumprir o que rege a Lei 4178/2020.


- **LOCAL 01:**
    Ao ser adicionado no PortalCMJ, um arquivo é colocado em disponibilidade imediata em dois formatos dentro do mesmo local:

    1. O original, sem adição de OCR e de selos de protocolo e de votação.
    2. Uma cópia de acesso imediato, já com OCR (se for o caso), e com os selos de protocolo e votação, se for este também o caso.


- **LOCAL 02:**
    Em no máximo 1h, é feita uma cópia dos recém adicionados e tratados no LOCAL 01. Essa cópia é enviada para uma Unidade de Armazenamento dedicada a este fim, dentro do prédio da CMJ, mas fora da sala do servidor central que armazena o LOCAL 01.

- **LOCAL 03:**
    Em no máximo 1h após o procedimento do LOCAL 02, é feita outra cópia, desta vez para nuvem. Na nuvem, as regras são rígidas:

    - uma vez tendo entrado um documento lá, ele só pode ser retirado e/ou alterado após 180 dias que lá chegou.
    - alterações nunca são definitivas, se um arquivo for alterado e enviado por 5 vezes, lá terá as 5 cópias guardadas.
    - para acessar um documento, não é possível o fazer imediatamente, só sendo possível, então, 48h após solicitar uma cópia.

    Estas regras dão segurança e tempo de reversão de qualquer ataque que lá venha ocorrer. Pois qualquer ordem lá, é comunicada via e-mail, e só executada após 48h.

- **LOCAL 04:**
    Todos os dias, de madrugada, um cópia é feita ao lado da cópia de LOCAL 01, dentro do mesmo equipamento, e está lá para disponibilidade imediata caso haja uma falha interna do equipamento principal.

- **LOCAL 05:**
    Em um dia da semana, aleatoriamente, é conectado manualmente um HD externo e rodado uma ordem de cópia de todo o conteúdo de LOCAL 04 para esse HD externo, que é imediatamente desligado após o término da cópia. Portanto um HD muito pouco utilizado, conectado apenas uma vez por semana, por algumas horas.

'''
    return mark,


def get_legislacao_municipal():
    size_models = get_size_models(
    models = [
        (NormaJuridica, ''),
        (AnexoNormaJuridica, ''),
        ]
    )

    mark1 = f'''
# Legislação Municipal
- **Normas**
    - **{ size_models[NormaJuridica]['count'] }** normas.
    - **{ int(size_models[NormaJuridica]['size']/1024/1024/1024) } GB**.
    - **{ size_models[NormaJuridica]['paginas']}** páginas.
-------------------
- **Anexos de Normas**
    - **{ size_models[AnexoNormaJuridica]['count'] }** anexos.
    - **{ int(size_models[AnexoNormaJuridica]['size']/1024/1024/1024) } GB**.
    - **{ size_models[AnexoNormaJuridica]['paginas']}** páginas.
'''

    mark2 = f'''
- **Dispostivos das Normas Compiladas**
    - **{ Dispositivo.objects.filter(ta__privacidade=0, ta__clone__isnull=True).count()- Dispositivo.objects.filter(ta__privacidade=0, ta__clone__isnull=False).count() }** dispositivos.
-------------------
O PortalCMJ possui o módulo de **Compilação de Leis**,
desenvolvido integralmente pela CMJ, disponibiliza a base de leis
do Município de Jataí e gerência os vínculos de vigência,
alteração, revogação e inclusão.
'''
    return (mark1, 5), (mark2, 7)


def get_arqdocs():
    size_models = get_size_models(
        models = [
            (ArqDoc, ''),
        ]
    )
    mark = f'''
# Documentos digitalizados do Arquivo Administrativo
- **ArqDocs**
    - **{ size_models[ArqDoc]['count'] }** itens.
    - **{ int(size_models[ArqDoc]['size']/1024/1024/1024) } GB**.
    - **{ size_models[ArqDoc]['paginas']}** páginas.

O PortalCMJ possui o **Módulo ARQ**, desenvolvido integralmente pela CMJ, responsável por tratar e indexar os documentos que estão sendo digitalizados do arquivo físico.
Este módulo possui alta capacidade de processamento em paralelo de OCR e conversão de PDFs para o formato de arquivamento PDF/A-2b.

Contando com uma estratégia de agendamento (gerenciado pela ferramenta _redis_ e _celery_), centenas de arquivos pode ser
digitalizados e adicionados diretamente na agenda e processamento. Este mecanismo tranfere
o processamento para o servidor do PortalCMJ e libera a máquina do usuário para dar continuidade em outras tarefas, ou mesmo
ser desligada.

Após catalogados e arquivados numa estrutura de classificação digital que espelha o arquivo físico, os arquivos digitais são
mapeados em uma ferramenta de indexação (_Solr_). Esta ferramenta é uma poderosa solução de busca, que leva em consideração
a semântica do texto na lingua portuguesa, vetoriza os termos em tokens e está a um passo de integração,
em um futuro breve, com alguma I.A. generativa.
'''
    return mark,


def get_materialegislativa():
    # código para calcular os números abaixo
    size_models = get_size_models(
        models = [
            (MateriaLegislativa, ''),
            (DocumentoAcessorio, ''),
            (Tramitacao, ''),
            (SessaoPlenaria, ''),
            (RegistroVotacao, ''),
            (NormaJuridica, 'where tipo_id=27'),
            (Proposicao, 'where content_type_id=81'),
            (DocumentoAdministrativo, 'where workspace_id = 21 and tipo_id = 150'),
        ]
    )

    size_outros_pareceres = get_size_models(
        models = [
            (DocumentoAdministrativo, 'where workspace_id = 21 and tipo_id in (120, 180, 170)'),
        ]
    )

    mark1 = f'''
# Processo Legislativo

- **Proposições Legislativas**
    - **{ size_models[Proposicao]['count'] }** proposições.
    - **{ int(size_models[Proposicao]['size']/1024/1024/1024) } GB**.
    - **{ size_models[Proposicao]['paginas']}** páginas.


Com a aprovação da Lei 4178/2020, foi instituído o
Processo Legislativo Eletrônico em que as proposições legislativas passaram a
serem assinadas com certificado digital e protocoladas diretamente no PortalCMJ,
sem a necessidade de impressão.
    '''

    mark2 = f'''
- **Matérias Legislativas**
    - **{ size_models[MateriaLegislativa]['count'] }** itens.
    - **{ int(size_models[MateriaLegislativa]['size']/1024/1024/1024) } GB**.
    - **{ size_models[MateriaLegislativa]['paginas']}** páginas.
-------------------
- **Tramitações**
    - **{ size_models[Tramitacao]['count'] }** Tramitações.
-------------------
- **Documentos Acessórios**
    - **{ size_models[DocumentoAcessorio]['count'] }** itens.
    - **{ int(size_models[DocumentoAcessorio]['size']/1024/1024/1024) } GB**.
    - **{ size_models[DocumentoAcessorio]['paginas']}** páginas.
    '''

    mark3 = f'''
- **Pareceres Jurídicos**
    - **{ size_models[DocumentoAdministrativo]['count'] }** Legislativos.
    - **{ size_outros_pareceres[DocumentoAdministrativo]['count'] }** Administrativos.
    - **{ int((size_models[DocumentoAdministrativo]['size'] + size_outros_pareceres[DocumentoAdministrativo]['size'])/1024/1024/1024) } GB**.
    - **{ size_models[DocumentoAdministrativo]['paginas'] + size_outros_pareceres[DocumentoAdministrativo]['paginas'] }** páginas.
-------------------
- **Sessões Plenárias**
    - **{ size_models[SessaoPlenaria]['count'] }** itens.
    - **{ int(size_models[SessaoPlenaria]['size']/1024/1024/1024) } GB**.
-------------------
- **Registros de Votação**
    - **{ size_models[RegistroVotacao]['count'] }** registros.
-------------------
- **Autógrafos**
    - **{ size_models[NormaJuridica]['count'] }** autógrafos.
    - **{ size_models[NormaJuridica]['paginas']}** páginas.
    '''

    return (mark1, 4), (mark2, 4), (mark3, 4)


def get_documentos_administrativos():
    size_models = get_size_models(
        models = [
            (DocumentoAdministrativo, 'where workspace_id=22'),
        ]
    )
    mark1 = f'''
# Documentos Administrativos
- **Documentos**
    - **{ size_models[DocumentoAdministrativo]['count'] }** itens.
    - **{ int(size_models[DocumentoAdministrativo]['size']/1024/1024/1024) } GB**.
    - **{ size_models[DocumentoAdministrativo]['paginas']}** páginas.
'''

    mark2 = '''
A Câmara possui um sistema de publicação de documentos administrativos
com certificação de publicação pelo departamento responsável com a finalidade
de dar segurança aos departamentos da CMJ como mecanismo de comprovação de
encaminhamento para publicação.

Todos os documentos publicados são catalogados e disponibilizados para pesquisa
integral em seu conteúdo.
'''
    return (mark1, 5), (mark2, 7)


def get_diarios_oficiais():
    size_diario_camara = get_size_models(
        models = [
            (DiarioOficial, 'where tipo_id=2'),
        ]
    )
    size_diario_prefeitura = get_size_models(
        models = [
            (DiarioOficial, 'where tipo_id=1'),
        ]
    )
    mark1 = f'''
# Diários Oficiais
- **Diários da Câmara de Jataí**
    - **{ size_diario_camara[DiarioOficial]['count'] }** itens.
    - **{ size_diario_camara[DiarioOficial]['paginas']}** páginas.
-----------------
- **Diários da Prefeitura de Jataí**
    - **{ size_diario_prefeitura[DiarioOficial]['count'] }** itens.
    - **{ size_diario_prefeitura[DiarioOficial]['paginas']}** páginas.
'''

    mark2 = '''
Desde 2013 e 2020, Prefeitura e Câmara, respectivamente, possuem Diário Oficial,
onde publicam todos atos administrativos, legislativos e normativos.
A Câmara, por publicar a Legislação de forma compilada e dar completude ao
processo legislativo, publica também, não só os diários oficiais do executivo
que possuem publicação de Leis, mas todos os seus diários, indexando esses textos
e disponibilizando-os no sistema de pesquisa em ["Pesquisa Geral"](http://localhost:9000/pesquisar/).
'''

    return (mark2, 6), (mark1, 6)


def get_():
    size_models = get_size_models(
        models = [
            ('model', ''),
        ]
    )
    mark1 = f'''
'''

    mark2 = '''
'''

    return (mark1, 5), (mark2, 7)


def get_numeros():

    mark = []

    mark.append(get_redessociais())
    mark.append(get_legislacao_municipal())
    mark.append(get_materialegislativa())
    mark.append(get_diarios_oficiais())
    mark.append(get_documentos_administrativos())
    mark.append(get_arqdocs())
    mark.append(get_estrutura_armazenamento())
    html = []
    for mt in mark:
        cols = []
        for m in mt:
            sm = ''
            if isinstance(m, tuple):
                m, sm = m
                sm = f'-{sm}'
            m = md.markdown(m)
            cols.append(f'<div class="col-md{sm}">{m}</div>')
        row = f'<div class="row page-break">{"".join(cols)}</div>'
        html.append(row)

    mdr = [f'{markstyles}<div class="container container-bi container-show">{h}</div>' for h in html]

    return ''.join(mdr)

