
from django.db import migrations
from django.contrib.postgres.operations import UnaccentExtension


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_remove_iaquotaslog_user'),
    ]

    operations = [
        UnaccentExtension(),
    ]
