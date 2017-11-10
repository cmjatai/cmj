"""import os


if __name__ == '__main__':

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "cmj.legacy_migration_settings")
    django.setup()"""
from sapl.protocoloadm.models import TramitacaoAdministrativo

if True:
    from sapl.base.models import Autor
    from sapl.norma.models import TipoVinculoNormaJuridica, NormaRelacionada

    from cmj.legacy import migration


def cmj_adjust_autor(new, old):
    print('cmj_adjust_autor', old.nom_autor)
    for args in [
            # essa ordem é importante
            (migration.Parlamentar, 'cod_parlamentar', 'nome_parlamentar'),
            (migration.Comissao, 'cod_comissao', 'nome'),
            (migration.Partido, 'cod_partido', 'nome')]:
        if migration.vincula_autor(new, old, *args):
            break


def cmj_adjust_normarelacionada(new, old):
    tipo = TipoVinculoNormaJuridica.objects.filter(sigla=old.tip_vinculo)
    print(len(tipo), old.tip_vinculo)
    assert len(tipo) == 1
    new.tipo_vinculo = tipo[0]


migration.AJUSTE_ANTES_SALVAR.update({
    Autor: cmj_adjust_autor,
    NormaRelacionada: cmj_adjust_normarelacionada,

})

migration.AJUSTE_DEPOIS_SALVAR.update({

})


def fill_cmj_vinculo_norma_juridica():
    lista = [('Z', 'Autógrafo da Norma ',
              'Autógrafo Transformado em Lei:'), ]
    lista_objs = [TipoVinculoNormaJuridica(
        sigla=item[0], descricao_ativa=item[1], descricao_passiva=item[2])
        for item in lista]
    TipoVinculoNormaJuridica.objects.bulk_create(lista_objs)


class DataMigrator(migration.DataMigrator):
    def migrate(self, obj, interativo):
        fill_cmj_vinculo_norma_juridica()
        super().migrate(obj, interativo)


def migrate(obj=migration.appconfs, interativo=True):
    dm = DataMigrator()
    dm.migrate(obj, interativo)


if __name__ == '__main__':
    migrate()
