from django.db import migrations


def forwards(apps, schema_editor):
    """Copia os dados do FK emendaloa_old para o M2M emendaloa."""
    RegistroAjusteLoa = apps.get_model("loa", "RegistroAjusteLoa")

    registros = RegistroAjusteLoa.objects.filter(
        emendaloa_old__isnull=False
    ).select_related("emendaloa_old")

    for registro in registros.iterator():
        registro.emendaloa.add(registro.emendaloa_old)


def backwards(apps, schema_editor):
    """Reverte: copia o primeiro item do M2M de volta para o FK."""
    RegistroAjusteLoa = apps.get_model("loa", "RegistroAjusteLoa")

    for registro in RegistroAjusteLoa.objects.all().iterator():
        primeira_emenda = registro.emendaloa.first()
        if primeira_emenda:
            registro.emendaloa_old = primeira_emenda
            registro.save(update_fields=["emendaloa_old"])


class Migration(migrations.Migration):

    dependencies = [
        ("loa", "0077_registroajusteloa_emendaloa_m2m_schema"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
