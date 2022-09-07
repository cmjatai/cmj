
from django.conf import settings
from django.db import connection
from django.db.models.signals import post_migrate
from django.db.utils import DEFAULT_DB_ALIAS, IntegrityError
from django.dispatch.dispatcher import receiver
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _
from sapl.compilacao.models import TipoDispositivo


def import_pattern():

    from sapl.compilacao.models import TipoTextoArticulado
    from sapl.compilacao.utils import get_integrations_view_names

    from django.contrib.contenttypes.models import ContentType
    from unipath import Path

    compilacao_app = Path(__file__).ancestor(1)
    # print(compilacao_app)
    with open(compilacao_app + '/compilacao_data_tables.sql', 'r') as f:
        lines = f.readlines()
        lines = [line.rstrip('\n') for line in lines]

        with connection.cursor() as cursor:
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                try:
                    cursor.execute(line)
                except IntegrityError as e:
                    if not settings.DEBUG:
                        print(
                            format_lazy(
                                '{}{}{}',
                                _('Ocorreu erro na importação: '),
                                line,
                                str(e)))
                except Exception as ee:
                    print(ee)

    integrations_view_names = get_integrations_view_names()

    def cria_sigla(verbose_name):
        verbose_name = verbose_name.upper().split()
        if len(verbose_name) == 1:
            verbose_name = verbose_name[0]
            sigla = ''
            for letra in verbose_name:
                if letra in 'BCDFGHJKLMNPQRSTVWXYZ':
                    sigla += letra
        else:
            sigla = ''.join([palavra[0] for palavra in verbose_name])
        return sigla[:3]

    for view in integrations_view_names:
        try:
            tipo = TipoTextoArticulado()
            tipo.sigla = cria_sigla(
                view.model._meta.verbose_name
                if view.model._meta.verbose_name
                else view.model._meta.model_name)
            tipo.descricao = view.model._meta.verbose_name
            tipo.content_type = ContentType.objects.get_by_natural_key(
                view.model._meta.app_label, view.model._meta.model_name)
            tipo.save()
        except IntegrityError as e:
            if not settings.DEBUG:
                print(format_lazy('{}{}',
                                  _('Ocorreu erro na criação tipo de ta: '),
                                  str(e)))


@receiver(post_migrate, dispatch_uid='init_compilacao_base')
def init_compilacao_base(app_config, verbosity=2, interactive=True,
                         using=DEFAULT_DB_ALIAS, **kwargs):

    if app_config.name != 'sapl.compilacao':
        return

    if not TipoDispositivo.objects.exists():

        print('')
        print(format_lazy('{}{}{}', '\033[93m\033[1m',
                          _('Iniciando Textos Articulados...'),
                          '\033[0m'))
        import_pattern()
