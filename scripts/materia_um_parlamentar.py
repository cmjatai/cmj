import csv
import os


if __name__ == '__main__':

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")
    django.setup()

if True:
    from sapl.materia.models import MateriaLegislativa


if __name__ == '__main__':

    p = 'joão rosa'

    materias = MateriaLegislativa.objects.filter(
        autores__nome__icontains=p
    ).order_by('tipo__sequencia_regimental', '-ano', '-data_apresentacao')

    with open('/home/leandro/TEMP/{}.csv'.format(p), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=',',
                       quotechar='"', quoting=csv.QUOTE_MINIMAL)
        w.writerow([
            'DATA',
            'TIPO_NUMERO_ANO',
            'EMENTA'
        ])
        for m in materias:
            w.writerow([
                m.data_apresentacao.strftime('%d/%m/%Y'),
                '{} nº {}/{}'.format(m.tipo.sigla, m.numero, m.ano),
                m.ementa
            ])
