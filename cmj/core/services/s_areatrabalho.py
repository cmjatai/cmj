from cmj.core.models import AreaTrabalho


class AreaTrabalhoService:
    """Quem alcança os registros de um model ligado a área de trabalho
    (docs/specs/api/acesso.md).

    Como nas telas, cada usuário alcança só os registros das áreas em que
    opera, qualquer que seja a permissão que tenha. Sem usuário autenticado,
    nada é alcançado.
    """

    @staticmethod
    def areas_do_operador(user):
        if not user or user.is_anonymous:
            return AreaTrabalho.objects.none()
        return AreaTrabalho.objects.filter(operadores=user)

    @classmethod
    def registros_do_operador(cls, user, queryset, campo="workspace"):
        return queryset.filter(**{f"{campo}__in": cls.areas_do_operador(user)})

    @classmethod
    def opera_na_area(cls, user, area):
        """Só o operador grava registro na área."""
        return bool(area and cls.areas_do_operador(user).filter(pk=area.pk).exists())
