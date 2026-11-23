from django.db.models import Q


class AuditoriaService:
    """O que o registro de auditoria guarda de cada objeto
    (docs/specs/api/acesso.md).

    O registro guarda o objeto serializado por inteiro, menos os campos de
    credencial: eles não são gravados, e os registros antigos que os tenham
    são limpos por ``limpar_registros``.
    """

    CAMPOS_NAO_GUARDADOS = ("password",)

    @classmethod
    def sem_campos_nao_guardados(cls, obj):
        """O objeto serializado, sem os campos que a auditoria não guarda."""
        for item in obj if isinstance(obj, list) else []:
            fields = item.get("fields") if isinstance(item, dict) else None
            if isinstance(fields, dict):
                for campo in cls.CAMPOS_NAO_GUARDADOS:
                    fields.pop(campo, None)
        return obj

    @classmethod
    def registros_a_limpar(cls, queryset):
        """Registros de auditoria que ainda guardam algum desses campos."""
        q = Q()
        for campo in cls.CAMPOS_NAO_GUARDADOS:
            q |= Q(obj__0__fields__has_key=campo)
        return queryset.filter(q)

    @classmethod
    def limpar_registros(cls, queryset):
        """Retira esses campos dos registros já gravados e devolve quantos
        registros foram alterados. Os demais campos de cada registro ficam
        como estavam."""
        limpos = 0
        for registro in cls.registros_a_limpar(queryset).only("id", "obj").iterator():
            obj = cls.sem_campos_nao_guardados(registro.obj)
            limpos += queryset.model.objects.filter(pk=registro.pk).update(obj=obj)
        return limpos
