# Generated by Django 5.2.1 on 2025-06-02 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0070_alter_anexado_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentoadministrativo',
            name='valor_estimado',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Valor Efetivo/Estimado'),
        ),
    ]
