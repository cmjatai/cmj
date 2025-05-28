from .dashboard import FilterBaseDashboard, Dashcard, getcolor

default_app_config = 'dashboard.apps.DashboardConfig'

__all__ = ["Dashcard", "getcolor", "FilterBaseDashboard"]


# TODO: django-dashboard foi adicionado ao projeto,
# até a criação do dashboard com vários cards e filtro global.
# Depois de implementado, retornar para o projeto original e commitar em:
# https://github.com/LeandroJatai/django-dashboard