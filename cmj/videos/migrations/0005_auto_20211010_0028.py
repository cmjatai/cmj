# Generated by Django 2.2.24 on 2021-10-10 03:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0004_videoparte_fieldname'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='execucao',
            field=models.PositiveIntegerField(default=0, verbose_name='Execução'),
        ),
        migrations.AlterField(
            model_name='videoparte',
            name='video',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='videoparte_set', to='videos.Video', verbose_name='Vídeo'),
        ),
    ]
