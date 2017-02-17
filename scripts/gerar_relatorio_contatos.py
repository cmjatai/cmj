import csv
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmj.settings")
django.setup()


from cmj.cerimonial.models import Processo, Contato, Telefone, Endereco
from cmj.core.models import AreaTrabalho


if __name__ == "__main__":

    at = AreaTrabalho.objects.get(pk=3)
    print(at.nome)

    """processos = Processo.objects.filter(
        workspace=5).order_by('titulo').distinct('titulo').values_list('titulo', flat=True)
    """
    with open('/home/leandro/relatorio_geovaci.csv', 'w') as cf:
        writer = csv.writer(cf, delimiter=',',
                            quotechar='"',
                            quoting=csv.QUOTE_MINIMAL)

        contatos = Contato.objects.filter(
            workspace=at).order_by(
            'endereco_set__bairro__nome',
            'endereco_set__endereco',
            'nome')

        excludes_fields = (
            'id', 'search', 'created', 'modified', 'owner', 'modifier',
        )
        contato_excludes_fields = (
            'workspace', 'perfil_user', 'observacoes', 'ativo',
            'nome_social', 'apelido', 'identidade_genero', 'tem_filhos',
            'quantos_filhos', 'nivel_instrucao', 'numero_sus',
            'titulo_eleitor', 'profissao', 'tipo_autoridade',
            'cargo', 'pronome_tratamento',
        )
        telefone_excludes_fields = (
            'contato', 'operadora', 'proprio', 'de_quem_e', 'preferencial',
            'permissao', 'tipo'
        )

        endereco_excludes_fields = (
            'contato', 'trecho', 'preferencial', 'tipo',
            'ponto_referencia', 'regiao_municipal',
            'distrito', 'observacoes'
        )

        def get_model_fields(model):
            return model._meta.fields

        def campo_excluido(field, exclude_lists):
            for lista in exclude_lists:
                if field.name in lista:
                    return True
            return False

        row_title = []
        for field in get_model_fields(Contato):
            if campo_excluido(field, (excludes_fields, contato_excludes_fields)):
                continue
            row_title.append(field.verbose_name)

        row_title.append('Telefone 1')
        row_title.append('Telefone 2')

        for field in get_model_fields(Endereco):
            if campo_excluido(field, (excludes_fields, endereco_excludes_fields)):
                continue
            row_title.append(field.verbose_name)

        writer.writerow(row_title)

        for c in contatos:
            row = []

            for field in get_model_fields(Contato):
                if campo_excluido(field, (excludes_fields, contato_excludes_fields)):
                    continue
                if getattr(c, field.name):
                    row.append(str(getattr(c, field.name)))
                else:
                    row.append('')

            for telefone in c.telefone_set.all():
                for field in get_model_fields(Telefone):
                    if campo_excluido(field, (excludes_fields, telefone_excludes_fields)):
                        continue
                    if getattr(telefone, field.name):
                        row.append(str(getattr(telefone, field.name)).strip())
                    else:
                        row.append('')

            if c.telefone_set.count() == 0:
                row.append('')
                row.append('')
            elif c.telefone_set.count() == 1:
                row.append('')

            for endereco in c.endereco_set.all():
                for field in get_model_fields(Endereco):
                    if campo_excluido(field, (excludes_fields, endereco_excludes_fields)):
                        continue
                    if getattr(endereco, field.name):
                        row.append(str(getattr(endereco, field.name)).strip())
                    else:
                        row.append('')

            writer.writerow(row)

        cf.close()
        """for c in contatos:
            end = c.endereco_set.first()
            endereco = end.endereco if end else ''
            bairro = end.bairro.nome if end and end.bairro else ''
            cep = end.cep if end and end.cep else ''
            cidade = end.municipio.nome if end and end.municipio else ''

            telefones = ' / '.join(map(lambda x: str(x),
                                       list(c.telefone_set.all())
                                       )) if c.telefone_set.exists() else ''
            writer.writerow([
                str(c.nome),
                bairro,
                endereco,
                cep,
                cidade,
                telefones])
        cf.close()"""
