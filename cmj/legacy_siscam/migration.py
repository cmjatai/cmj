import re

from sapl.parlamentares.models import Municipio

from cmj.cerimonial.models import Contato, Email, Telefone, Endereco
from cmj.core.models import AreaTrabalho, User, Distrito, RegiaoMunicipal,\
    Trecho, Cep
from cmj.legacy_siscam.models import Pessoa


router_usuario_areatrabalho = (
    (26, 1),
    (41, 2),
    (22, 3),
    (37, 4),
    (28, 5),
    (21, 6),
    (25, 7),
    (39, 8),
    (40, 9),
    (38, 10),
    (42, 11),
)

router_parentesco = {
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


def migrate_siscam():

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
                print(p.pk, p.nome)
                # importa cadastro de pessoa como um contato válido
                contato = Contato()
                contato.owner = owner
                contato.modifier = owner
                contato.workspace = w

                contato.cpf = p.cpf
                contato.nome = p.nome
                contato.rg = p.rg\
                    if p.rg and p.rg != 'null' else ''
                contato.rg_orgao_expedidor = p.orgaorg\
                    if p.orgaorg and p.orgaorg != 'null' else ''
                contato.rg_data_expedicao = p.dataexprg
                contato.numero_sus = p.numsus\
                    if p.numsus and p.numsus != 'null' else ''

                contato.nome_pai = p.nomepai\
                    if p.nomepai else ''
                contato.nome_mae = p.nomemae\
                    if p.nomemae and p.nomemae != 'null' else ''

                contato.naturalidade = p.naturalidade\
                    if p.naturalidade and p.naturalidade != 'null' else ''
                contato.data_nascimento = p.datanascimento
                contato.ativo = p.ativo if p.ativo else False
                contato.sexo = p.sexo if p.sexo else ''

                if p.estadocivil in '12345':
                    contato.estado_civil_id = int(p.estadocivil)

                contato.save()
                if p.email and p.email != 'null':
                    email = Email()
                    email.email = p.email
                    email.contato = contato
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
                    telefone.save()

                if p.logradouro and p.logradouro != 'null':
                    endereco = Endereco()
                    endereco.contato = contato
                    endereco.uf = p.estado if p.estado else ''
                    endereco.bairro = p.bairro\
                        if p.bairro and p.bairro != 'null' else ''
                    endereco.complemento = p.complemento\
                        if p.complemento and p.complemento != 'null' else ''
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

                    endereco.save()

                if p.empresa:

                    pass

            else:
                # importa cadastro de pessoa como um dependente do ult contato
                pass


def aqui():

    print('aqui.')
