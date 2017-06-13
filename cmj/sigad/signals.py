from django.db.models.signals import post_save
from reversion.revisions import create_revision
from reversion.signals import post_revision_commit
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
