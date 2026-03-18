import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("loa", "0076_alter_prestacaocontaloa_options_and_more"),
    ]

    operations = [
        # 1. Renomear o campo FK emendaloa -> emendaloa_old
        #    (db_column permanece 'emendaloa_id', então não altera a tabela no banco)
        migrations.RenameField(
            model_name="registroajusteloa",
            old_name="emendaloa",
            new_name="emendaloa_old",
        ),
        migrations.AlterField(
            model_name="registroajusteloa",
            name="emendaloa_old",
            field=models.ForeignKey(
                blank=True,
                null=True,
                default=None,
                verbose_name="Emenda Impositiva (old)",
                related_name="registroajusteloa_old_set",
                db_column="emendaloa_id",
                on_delete=django.db.models.deletion.PROTECT,
                to="loa.emendaloa",
            ),
        ),
        # 2. Adicionar o novo campo ManyToManyField
        migrations.AddField(
            model_name="registroajusteloa",
            name="emendaloa",
            field=models.ManyToManyField(
                blank=True,
                verbose_name="Emendas Impositivas",
                related_name="registroajusteloa_set",
                to="loa.emendaloa",
            ),
        ),
    ]
