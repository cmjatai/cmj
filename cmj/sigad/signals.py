from django.db.models.signals import post_save, pre_delete
from django.dispatch.dispatcher import receiver
from reversion.revisions import create_revision
from reversion.signals import post_revision_commit, pre_revision_commit

from cmj.sigad.models import Documento, Revisao, CMSMixin


def save_revision_documents(sender, **kwargs):

    versions = list(kwargs.get('versions', []))

    if not versions:
        return

    for version in versions:
        if CMSMixin in type.mro(type(version.object)):
            with create_revision(False):
                Revisao.gerar_revisao(
                    version.object, version.revision.user)

post_revision_commit.connect(save_revision_documents, sender=create_revision)


@receiver(pre_delete, sender=Documento, dispatch_uid='documento_delete_signal')
def log_deleted_documento(sender, instance, using, **kwargs):
    print('passou log_deleted_documento pk = %s, parent = %s' % (
        instance.pk,
        instance.parent.pk if instance.parent else ''))
