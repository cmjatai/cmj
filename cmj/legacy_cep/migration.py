
from itertools import islice

from django.apps import apps
from django.db import transaction
from sapl.parlamentares.models import Municipio

from cmj.core.models import Cep, TipoLogradouro, RegiaoMunicipal, Distrito,\
    Bairro, Logradouro, Trecho


# BASE ######################################################################
#  apps to be migrated, in app dependency order (very important)
model_dict = apps.all_models['legacy_cep']


class DataMigrator:

    def __init__(self):
        pass

    def migrate(self, pini, pfim):

        rm = RegiaoMunicipal.objects.filter(nome='Sede do Município')

        if rm.exists():
            rm = rm[0]
        else:
            rm = RegiaoMunicipal()
            rm.nome = 'Sede do Município'
            rm.tipo = 'AU'
            rm.save()

        dt = Distrito.objects.filter(nome='Sede')
        if dt.exists():
            dt = dt[0]
        else:
            dt = Distrito()
            dt.nome = 'Sede'
            dt.save()

        if pini == -1:
            for uf_model in model_dict.keys():
                print(list(model_dict.keys()).index(uf_model), uf_model)
            return

        for uf_model in list(islice(model_dict, pini, pfim)):
            if uf_model in ['ceplogindex', 'cepunico']:
                continue

            uf_upper = uf_model.upper()

            model = model_dict[uf_model]
            print(uf_upper)

            municipio = None
            bairro = None
            logradouro = None
            tl = None
            for item in model.objects.order_by(
                    'cidade', 'bairro', 'tp_logradouro', 'logradouro').all():

                if not municipio or\
                        municipio.uf != uf_upper or\
                        municipio.nome != item.cidade:
                    if municipio:
                        print (municipio.uf,
                               uf_upper, municipio.nome, item.cidade)
                    municipio = Municipio.objects.order_by(
                        'nome', 'uf').filter(
                        nome=item.cidade,
                        uf=uf_upper).first()
                    if municipio:
                        print('O-', municipio.nome)

                if not municipio:
                    municipio = Municipio()
                    municipio.nome = item.cidade
                    municipio.uf = uf_upper
                    municipio.regiao = ''
                    municipio.save()
                    print('C-', municipio.nome)

                str_cep = item.cep.replace('-', '')
                try:
                    cep = Cep.objects.get(numero=str_cep)
                except:
                    cep = Cep()
                    cep.numero = str_cep
                    cep.save()

                if not bairro or bairro.nome != item.bairro:
                    bairro = Bairro.objects.filter(
                        nome=item.bairro).first()

                if not bairro:
                    bairro = Bairro()
                    bairro.nome = item.bairro
                    bairro.save()

                if not tl or tl.nome != item.tp_logradouro:
                    tl = TipoLogradouro.objects.filter(
                        nome=item.tp_logradouro).first()

                if not tl:
                    tl = TipoLogradouro()
                    tl.nome = item.tp_logradouro
                    tl.save()

                if not logradouro or logradouro.nome != item.logradouro:
                    logradouro = Logradouro.objects.filter(
                        nome=item.logradouro).first()

                if not logradouro:
                    logradouro = Logradouro()
                    logradouro.nome = item.logradouro
                    logradouro.save()

                trechos = Trecho.objects.filter(logradouro=logradouro,
                                                bairro=bairro,
                                                distrito=dt,
                                                regiao_municipal=rm,
                                                lado='AL')
                if not trechos.exists():
                    trecho = Trecho()
                    trecho.municipio = municipio
                    trecho.logradouro = logradouro
                    trecho.tipo = tl
                    trecho.bairro = bairro
                    trecho.distrito = dt
                    trecho.regiao_municipal = rm
                    trecho.lado = 'AL'
                    trecho.numero_final = None
                    trecho.numero_inicial = None
                    trecho.save()

                    trecho.cep.add(cep)
                    trecho.save()


def migrate(pini, pfim):
    dm = DataMigrator()
    dm.migrate(pini, pfim)
