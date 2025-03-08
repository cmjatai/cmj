
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import migrations
from rest_framework.authtoken.models import Token


def adiciona_token_de_usuarios(apps, schema_editor):
    for user in get_user_model().objects.all():
        Token.objects.get_or_create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_auto_20200520_2037'),
    ]

    operations = [
        migrations.RunPython(adiciona_token_de_usuarios) 
    ]
