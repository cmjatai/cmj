from django import apps
from django.db.models.signals import post_save, post_delete, post_migrate
from django.db.utils import DEFAULT_DB_ALIAS
from django.dispatch.dispatcher import receiver
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.globalrules'
    label = 'globalrules'
    verbose_name = _('Regras e Permissões para o Portal')


@receiver(post_migrate, dispatch_uid='update_groups_cmj')
def update_groups_cmj(app_config, verbosity=2, interactive=True,
                      using=DEFAULT_DB_ALIAS, **kwargs):

    if app_config != AppConfig and not isinstance(app_config, AppConfig):
        return

    from cmj.globalrules.map_rules import rules_patterns
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    class Rules:

        def __init__(self, rules_patterns):
            self.rules_patterns = rules_patterns

        def associar(self, g, model, tipo):
            for t in tipo:
                content_type = ContentType.objects.get_by_natural_key(
                    app_label=model._meta.app_label,
                    model=model._meta.model_name)

                codename = (t[1:] + model._meta.model_name)\
                    if t[0] == '.' and t[-1] == '_' else t

                p = Permission.objects.get(
                    content_type=content_type,
                    codename=codename)
                g.permissions.add(p)
            g.save()

        def _config_group(self, group_name, rules_list):
            if not group_name:
                return

            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()

            try:
                print(' ', group_name)
                for model, perms, perms_publicas in rules_list:
                    self.associar(group, model, perms)
            except Exception as e:
                print(group_name, e)

        def update_groups(self):
            print('')
            print(
                format_lazy(
                    '{}{}{}', '\033[93m\033[1m',
                    _('Atualizando grupos do Portal CMJ:'),
                    '\033[0m'))
            for rules_group in self.rules_patterns:
                group_name = rules_group['group']
                rules_list = rules_group['rules']
                self._config_group(group_name, rules_list)

    rules = Rules(rules_patterns)
    rules.update_groups()
