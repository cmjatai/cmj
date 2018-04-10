import csv
import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmj.settings")
django.setup()


if __name__ == "__main__":

    from django.utils import formats
    from cmj.cerimonial.models import Processo, Contato, Telefone, Endereco
    from cmj.core.models import AreaTrabalho

    at = AreaTrabalho.objects.get(pk=6)
    print(at.nome)

    """processos = Processo.objects.filter(
        workspace=5).order_by('titulo').distinct('titulo').values_list('titulo', flat=True)
    """
    with open('/home/leandro/relatorio.csv', 'w') as cf:
        writer = csv.writer(cf, delimiter=',',
                            quotechar='"',
                            quoting=csv.QUOTE_MINIMAL)

        contatos = Contato.objects.filter(
            workspace=at).order_by(
            'endereco_set__bairro__nome',
            'endereco_set__endereco',
            'nome')

        excludes_fields = (
            'id', 'search', 'modified', 'owner', 'modifier', 'created'
        )
        contato_excludes_fields = (
            'workspace', 'perfil_user',  'ativo', 'observacoes',
            'nome_social', 'apelido', 'identidade_genero', 'tem_filhos',
            'quantos_filhos', 'nivel_instrucao', 'numero_sus',
            'titulo_eleitor', 'profissao', 'tipo_autoridade',
            'cargo', 'pronome_tratamento', 'nome_pai', 'nome_mae',
            'cpf', 'rg', 'rg_orgao_expedidor', 'rg_data_expedicao',
        )
        telefone_excludes_fields = (
            'contato', 'operadora', 'proprio', 'de_quem_e', 'preferencial',
            'permissao', 'tipo', 'created'
        )

        endereco_excludes_fields = (
            'contato', 'trecho', 'preferencial', 'tipo',
            'ponto_referencia', 'regiao_municipal',
            'distrito', 'observacoes', 'created'
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

        row_title.append('Telefones')

        for field in get_model_fields(Endereco):
            if campo_excluido(field, (excludes_fields, endereco_excludes_fields)):
                continue
            row_title.append(field.verbose_name)

        row_title.append('Data')
        row_title.append('Processos')
        row_title.append('Observações')

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

            telefones = ''
            for telefone in c.telefone_set.all():
                for field in get_model_fields(Telefone):
                    if campo_excluido(field, (excludes_fields, telefone_excludes_fields)):
                        continue

                    if telefones:
                        telefones += ' / '

                    if getattr(telefone, field.name):
                        telefones += str(getattr(telefone, field.name)).strip()

            row.append(telefones)

            for endereco in c.endereco_set.all():
                for field in get_model_fields(Endereco):
                    if campo_excluido(field, (excludes_fields, endereco_excludes_fields)):
                        continue
                    if getattr(endereco, field.name):
                        row.append(str(getattr(endereco, field.name)).strip())
                    else:
                        row.append('')

            titulo_processos = ''
            if c.processo_set.exists():
                pf = c.processo_set.order_by('data').first()
                row.append(formats.date_format(
                    pf.data, "DATE_FORMAT"))

                for p in c.processo_set.order_by('data'):
                    if titulo_processos:
                        titulo_processos += ' / '
                    titulo_processos += p.titulo
                    if p.status:
                        titulo_processos += ' (%s)' % p.status.descricao
                    if p.classificacoes.exists():
                        titulo_processos += ' (%s)' % ''.join(
                            p.classificacoes.values_list('descricao', flat=True
                                                         )
                        )
            else:
                row.append(formats.date_format(
                    c.created, "DATE_FORMAT"))

            row.append(titulo_processos)

            row.append(c.observacoes)

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
