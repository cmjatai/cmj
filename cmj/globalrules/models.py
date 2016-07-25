from django.apps import apps
from django.contrib.auth.management import _get_all_permissions
from django.core import exceptions
from django.db import models, router
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from sapl.settings import SAPL_APPS

from cmj.settings import CMJ_APPS


app_configs = list(apps.get_app_configs())

for ac in app_configs:

    if ac.name not in CMJ_APPS and ac.name not in SAPL_APPS:
        continue

    app_models = ac.get_models()

    for m in app_models:
        permissions = (
            ("list_" + m._meta.model_name,
             string_concat(
                 _('Visualizaçao da lista de'), ' ',
                 m._meta.verbose_name_plural)),
            ("detail_" + m._meta.model_name,
             string_concat(
                 _('Visualização dos detalhes de'), ' ',
                 m._meta.verbose_name_plural)),
        )
        m._meta.permissions = tuple(
            set(list(permissions) + list(m._meta.permissions)))


def create_proxy_permissions(
        app_config, verbosity=2, interactive=True,
        using=DEFAULT_DB_ALIAS, **kwargs):
    if not app_config.models_module:
        return

    try:
        Permission = apps.get_model('auth', 'Permission')
    except LookupError:
        return

    if not router.allow_migrate_model(using, Permission):
        return

    from django.contrib.contenttypes.models import ContentType

    permission_name_max_length = Permission._meta.get_field('name').max_length

    # This will hold the permissions we're looking for as
    # (content_type, (codename, name))
    searched_perms = list()
    # The codenames and ctypes that should exist.
    ctypes = set()
    for klass in app_config.get_models():
        opts = klass._meta
        if opts.proxy:
            # Force looking up the content types in the current database
            # before creating foreign keys to them.
            app_label, model = opts.app_label, opts.model_name

            try:
                ctype = ContentType.objects.db_manager(
                    using).get_by_natural_key(app_label, model)
            except:
                ctype = ContentType.objects.db_manager(
                    using).create(app_label=app_label, model=model)
        else:
            ctype = ContentType.objects.db_manager(using).get_for_model(klass)

        ctypes.add(ctype)
        for perm in _get_all_permissions(klass._meta, ctype):
            searched_perms.append((ctype, perm))

    # Find all the Permissions that have a content_type for a model we're
    # looking for.  We don't need to check for codenames since we already have
    # a list of the ones we're going to create.
    all_perms = set(Permission.objects.using(using).filter(
        content_type__in=ctypes,
    ).values_list(
        "content_type", "codename"
    ))

    perms = [
        Permission(codename=codename, name=name, content_type=ct)
        for ct, (codename, name) in searched_perms
        if (ct.pk, codename) not in all_perms
    ]
    # Validate the permissions before bulk_creation to avoid cryptic database
    # error when the name is longer than 255 characters
    for perm in perms:
        if len(perm.name) > permission_name_max_length:
            raise exceptions.ValidationError(
                'The permission name %s of %s.%s '
                'is longer than %s characters' % (
                    perm.name,
                    perm.content_type.app_label,
                    perm.content_type.model,
                    permission_name_max_length,
                )
            )
    Permission.objects.using(using).bulk_create(perms)
    if verbosity >= 2:
        for perm in perms:
            print("Adding permission '%s'" % perm)


models.signals.post_migrate.connect(
    receiver=create_proxy_permissions,
    dispatch_uid="django.contrib.auth.management.create_permissions")

