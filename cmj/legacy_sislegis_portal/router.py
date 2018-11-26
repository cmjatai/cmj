class LegacyRouter:

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'legacy_sislegis_portal':
            return 'legacy_sislegis_portal'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'legacy_sislegis_portal':
            return 'legacy_sislegis_portal'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'legacy_sislegis_portal' \
                and obj2._meta.app_label == 'legacy_sislegis_portal':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'legacy_sislegis_portal':
            return False
        return None
