from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


GROUP_SOCIAL_USERS = _('Usuários de Login Social')

GROUP_WORKSPACE_USERS = _('Operadores de Área de Trabalho')
GROUP_WORKSPACE_MANAGERS = _('Gestores de Área de Trabalho')


class Rules:

    def associar(self, g, model, tipo):
        for t in tipo:
            content_type = ContentType.objects.get_by_natural_key(
                app_label=model._meta.app_label, model=model._meta.model_name)

            codename = (t[1:] + model._meta.model_name)\
                if t[0] == '.' and t[-1] == '_' else t

            p = Permission.objects.get(
                content_type=content_type,
                codename=codename)
            g.permissions.add(p)
        g.save()

    def _config_group(self, group, rules):
        g = Group.objects.get_or_create(name=group)[0]
        try:
            for model, perms in rules:
                self.associar(g, model, perms)
        except Exception as e:
            print(group, e)

    def config_groups(self, group_rules):
        for group, rules in group_rules:
            self._config_group(group, rules)

    def groups_add_user(self, user, groups_name):
        if not isinstance(groups_name, list):
            groups_name = [groups_name, ]
        for group_name in groups_name:
            if not group_name or user.groups.filter(name=group_name).exists():
                continue
            g = Group.objects.get_or_create(name=group_name)[0]
            user.groups.add(g)

    def groups_remove_user(self, user, groups_name):
        if not isinstance(groups_name, list):
            groups_name = [groups_name, ]
        for group_name in groups_name:
            if not group_name or not user.groups.filter(
                    name=group_name).exists():
                continue
            g = Group.objects.get_or_create(name=group_name)[0]
            user.groups.remove(g)

    def group_social_users_add_user(self, user):
        if user.groups.filter(name=GROUP_SOCIAL_USERS).exists():
            return

        g = Group.objects.get_or_create(name=GROUP_SOCIAL_USERS)[0]
        user.groups.add(g)
        user.save()

rules = Rules()
