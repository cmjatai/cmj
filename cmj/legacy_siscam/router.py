class LegacyRouter:

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'legacy_siscam':
            return 'legacy_siscam'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'legacy_siscam':
            return 'legacy_siscam'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'legacy_siscam' \
                and obj2._meta.app_label == 'legacy_siscam':
            return True
        return None

    def allow_migrate(self, db, model):
        if model._meta.app_label == 'legacy_siscam':
            return False
        return None
