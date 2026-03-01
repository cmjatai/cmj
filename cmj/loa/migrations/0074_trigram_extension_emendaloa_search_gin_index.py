from django.contrib.postgres.operations import TrigramExtension
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('loa', '0073_alter_arquivoprestacaocontaregistro_options_and_more'),
    ]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name='emendaloa',
            index=GinIndex(
                OpClass(
                    'search',
                    name='gin_trgm_ops',
                ),
                name='emendaloa_search_gin_trgm',
            ),
        ),
    ]
