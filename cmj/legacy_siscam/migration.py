import re

from django.utils import timezone
from sapl.parlamentares.models import Municipio

from cmj.cerimonial.models import Contato, Email, Telefone, Endereco,\
    Dependente, Processo
from cmj.core.models import AreaTrabalho, User, Distrito, RegiaoMunicipal,\
    Trecho, Cep, Bairro
from cmj.legacy_siscam.models import Pessoa, Visitas


router_usuario_areatrabalho = (
    (21, 6),
    (26, 1),
    (41, 2),
    (22, 3),
    (37, 4),
    (28, 5),
    (25, 7),
    (39, 8),
    (40, 9),
    (38, 10),
    (42, 11),
)

router_parentesco = {
    0: 1,
    1: 1,
    2: 3,
    3: 3,
    4: 2,
    5: 2,
    6: 6,
    7: 6,
    8: 8,
    9: 8,
    10: 12,
    11: 12,
    12: 10,
    13: 10,
    14: 5,
    15: 5,
    16: 9,
    17: 9,
    18: 14,
    19: 15,
    20: 16,
    21: 17,
    22: 18,
}


def validateEmail(email):
    if len(email) > 6:
        if re.match('\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', email) != None:
            return True
    return False


def generate_sql_for_visitas():

    visitas = Visitas.objects.raw(
        """select * from "Visitas" where excluido = false order by assunto""")

    wa = []
    wd = []
    reg = re.compile(
        '[\s\w\d.,*"\-º\/°;!:\(\)“”–]*[^\s\w\d.,*"\-º\/°;!:\(\)“”–]+[\s\w\d.,*"\-º\/°;!:\(\)“”–]*')
    for v in visitas:
        ass = list(
            filter((lambda x: reg.match(x)), re.split('\s+', v.assunto)))
        desc = list(
            filter((lambda x: reg.match(x)), re.split('\s+', v.descricao)))

        if not len(ass) and not len(desc):
            continue

        ass = list(
            map((lambda x: re.split('[\s\d.*,"\-º\/°;!:\(\)“”–]', x)), ass))
        ass = sum(ass, [])

        desc = list(
            map((lambda x: re.split('[\s\d.*,"\-º\/°;!:\(\)“”–]', x)), desc))
        desc = sum(desc, [])

        ass = list(
            filter((lambda x: len(x) > 0), ass))
        desc = list(
            filter((lambda x: len(x) > 0), desc))

        wa += ass
        wd += desc

    words = list(set(wa + wd))

    words.sort()

    file = open("/sistemas/update_visitas.sql", "w")
    for w in words:
        correcao = input("Corrija: %s:" % w)
        if not correcao:
            continue
        if str(correcao) == '0':
            break
        if '�' in w and len(correcao) == 1:
            correcao = w.replace('�', correcao, 1)

        if '?' in w:
            w = w.replace('?', '\\?')
        sql = """update "Visitas" set assunto = regexp_replace(assunto, E'%s', '%s', 'g'), descricao = regexp_replace(descricao, E'%s', '%s', 'g') where assunto ~ E'%s' or descricao ~ E'%s';\n""" % (
            w, correcao, w, correcao, w, w)
        file.write(sql)
    file.close()


def migrate_siscam():
    # generate_sql_for_visitas()
    # return

    Processo.objects.all().delete()
    Contato.objects.all().delete()
    pessoas = Pessoa.objects.order_by('id')  # .filter(excluido=False)

    # for p in pessoas.filter(cidade__icontains='�'):
    #    print(p.cidade)

    trecho75800000 = Trecho.objects.filter(cep__numero='75800-000')
    cep75800000 = Cep.objects.filter(numero='75800-000')

    if trecho75800000.exists():
        trecho75800000 = trecho75800000[0]
    else:
        if not cep75800000.exists():
            cep75800000 = Cep()
            cep75800000.numero = '75800-000'
            cep75800000.save()

        trecho75800000 = Trecho()
        trecho75800000.municipio = Municipio.objects.get(pk=5211909)
        trecho75800000.save()
        trecho75800000.cep.add(cep75800000)

    contador_contato = 21900
    for upk, apk in router_usuario_areatrabalho:

        w = AreaTrabalho.objects.get(pk=apk)
        owner = User.objects.get(pk=1)

        print('--------------------', w.nome)
        contato = None
        for p in pessoas.filter(alteradopor_id=upk):

            if p.pk % 256 == 0 and p.excluido:
                contato = None
                continue

            if p.pk % 256 != 0 and not contato:
                continue

            if p.pk % 256 == 0 and p.nome and p.nome != 'null':
                contador_contato += 1
                print(contador_contato, p.pk, p.nome)
                alteradoem = timezone.make_aware(
                    p.alteradoem,
                    timezone.get_current_timezone())

                # importa cadastro de pessoa como um contato válido
                contato = Contato()
                contato.owner = owner
                contato.modifier = owner
                contato.workspace = w

                contato.cpf = p.cpf
                contato.nome = p.nome
                contato.rg = p.rg\
                    if p.rg and p.rg.lower() != 'null' else ''
                contato.rg_orgao_expedidor = p.orgaorg\
                    if p.orgaorg and p.orgaorg.lower() != 'null' else ''
                contato.rg_data_expedicao = p.dataexprg

                if p.numsus and\
                        p.numsus.lower() != 'null' and len(p.numsus) < 100:
                    contato.numero_sus = p.numsus
                elif p.numsus and len(p.numsus) >= 100:
                    contato.observacoes = p.numsus
                else:
                    contato.numero_sus = ''

                contato.nome_pai = p.nomepai\
                    if p.nomepai and p.nomepai.lower() != 'null' else ''
                contato.nome_mae = p.nomemae\
                    if p.nomemae and p.nomemae.lower() != 'null' else ''

                contato.naturalidade = p.naturalidade\
                    if p.naturalidade and \
                    p.naturalidade.lower() != 'null' else ''
                contato.data_nascimento = p.datanascimento
                contato.ativo = p.ativo if p.ativo else False
                contato.sexo = p.sexo if p.sexo else ''

                if p.estadocivil in '12345':
                    contato.estado_civil_id = int(p.estadocivil)

                contato.created = alteradoem
                contato.modified = alteradoem
                contato.save()
                if p.email and p.email != 'null':
                    email = Email()
                    email.email = p.email
                    email.contato = contato
                    email.owner = owner
                    email.modifier = owner
                    email.created = alteradoem
                    email.modified = alteradoem
                    email.save()

                if p.telefonefixo and p.telefonefixo\
                    not in ['NAO TEM',
                            'NAO SABE',
                            'NAO TEM NA FICHA',
                            'SEM FONE',
                            '-',
                            ''
                            'null'
                            ]:
                    telefone = Telefone()
                    telefone.telefone = p.telefonefixo
                    telefone.tipo_id = 8
                    telefone.contato = contato
                    telefone.owner = owner
                    telefone.modifier = owner
                    telefone.created = alteradoem
                    telefone.modified = alteradoem
                    telefone.save()

                if p.telefonecelular and p.telefonecelular\
                    not in ['NAO TEM',
                            'NAO SABE',
                            'NAO TEM NA FICHA',
                            'SEM FONE',
                            '-',
                            ''
                            'null'
                            ]:
                    telefone = Telefone()
                    telefone.telefone = p.telefonecelular
                    telefone.tipo_id = 7
                    telefone.contato = contato
                    telefone.owner = owner
                    telefone.modifier = owner
                    telefone.created = alteradoem
                    telefone.modified = alteradoem
                    telefone.save()

                if p.logradouro and p.logradouro != 'null':
                    endereco = Endereco()
                    endereco.contato = contato
                    endereco.uf = p.estado if p.estado else ''

                    if p.bairro and p.bairro != 'null':
                        bairro = Bairro.objects.get_or_create(
                            nome=p.bairro)
                        endereco.bairro = bairro[0]

                    endereco.complemento = p.complemento\
                        if p.complemento and \
                        p.complemento.lower() != 'null' else ''
                    endereco.endereco = p.logradouro

                    endereco.distrito = Distrito.objects.first()
                    endereco.regiao_municipal = RegiaoMunicipal.objects.first()

                    if len(p.cep) == 8:
                        endereco.cep = p.cep[:5] + '-' + p.cep[-3:]
                    else:
                        endereco.cep = '75800-000'

                    trecho = Trecho.objects.filter(cep__numero=endereco.cep)
                    endereco.trecho = trecho[0] if trecho.exists() else None

                    mun = Municipio.objects.filter(nome=p.cidade, uf=p.estado)
                    endereco.municipio = mun[0] if mun.exists() else None

                    endereco.owner = owner
                    endereco.modifier = owner

                    endereco.created = alteradoem
                    endereco.modified = alteradoem
                    endereco.save()

                if p.empresa:

                    pass

                visitas = Visitas.objects.filter(idpessoa=p, excluido=False)

                if visitas.exists():
                    for v in visitas:

                        v_alteradoem = timezone.make_aware(
                            v.alteradoem,
                            timezone.get_current_timezone())

                        processo = Processo()
                        processo.data = v.data
                        processo.titulo = v.assunto
                        processo.descricao = v.descricao
                        processo.observacoes = v.observacao
                        processo.workspace = w
                        processo.status_id = v.status_id
                        processo.owner = owner
                        processo.modifier = owner
                        processo.created = v_alteradoem
                        processo.modified = v_alteradoem
                        processo.save()

                        processo.contatos.add(contato)

            else:

                if not contato:
                    continue

                if p.excluido:
                    continue

                d = Dependente()
                d.contato = contato
                d.parentesco_id = router_parentesco[p.parentesco]
                d.nome = p.nome
                d.sexo = p.sexo
                d.data_nascimento = p.datanascimento
                d.owner = owner
                d.modifier = owner
                d.created = alteradoem
                d.modified = alteradoem
                d.save()


def aqui():

    print('aqui.')
