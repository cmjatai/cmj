
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0103_statustramitacao_css_class'),
    ]

    operations = [
        migrations.RunSQL("""
            create or replace view materia_materiaemtramitacao as
            select m.id as id,
                   m.id as materia_id,
                   t.id as tramitacao_id,
                   t.unidade_tramitacao_destino_id as unidade_tramitacao_atual_id,
                   m.em_tramitacao as em_tramitacao
            from materia_materialegislativa m
            inner join materia_tramitacao t on (m.id = t.materia_id)
            where t.id = (select max(id) from materia_tramitacao where materia_id = m.id)
            order by m.id DESC
        """),
    ]
