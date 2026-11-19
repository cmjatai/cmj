from django.db import migrations

LEGADO = "IAGenaiBase"
NOVO = "IAChatService"


def autoriza_chat_service(apps, schema_editor):
    """Copia a autorização do chat da chave legada para a nova.

    A chave legada fica, para a versão anterior (blue/green) seguir achando cota.
    """
    IAQuota = apps.get_model("core", "IAQuota")
    for quota in IAQuota.objects.filter(servicos_autorizados__contains=[LEGADO]):
        if NOVO not in quota.servicos_autorizados:
            quota.servicos_autorizados = [*quota.servicos_autorizados, NOVO]
            quota.save(update_fields=["servicos_autorizados"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_alter_iaquota_servicos_chat"),
    ]

    operations = [
        # Sem reversão de dados: remover a chave nova não é necessário para voltar.
        migrations.RunPython(autoriza_chat_service, migrations.RunPython.noop),
    ]
