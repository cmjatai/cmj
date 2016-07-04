from cmj.legacy_siscam.models import Pessoa


executar = True


def migrate_siscam():

    if not exec:
        return

    executar = False

    pessoas = Pessoa.objects

    print(pessoas.count())
