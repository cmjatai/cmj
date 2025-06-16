import inspect
from importlib import import_module
from collections import defaultdict, OrderedDict
from django import forms
from django.apps import apps
from django.forms.widgets import MediaDefiningClass, Media
from django.utils.module_loading import module_has_submodule
from django.utils.safestring import mark_safe
from .dashboard import Dashcard, GridDashboard

DEFAULT_CHARTJS_URL = (
    "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"
)


class Dashboard(metaclass=MediaDefiningClass):
    EXPORT_TYPES = (
        ("csv", "CSV", "text/csv"),
        ("xlsx", "Planilha Excel", "application/vnd.ms-excel"),
        ("html", "Tabela em HTML", "text/html"),
        ("json", "Json", "application/json"),
        ("txt", "Texto plano", "text/plain"),
    )

    def __init__(self):
        dash_apps = defaultdict(dict)

        dash_grids = defaultdict(dict)

        dash_lists = defaultdict(dict)

        is_dashs = (
            lambda obj: isinstance(obj, type)
            and issubclass(obj, GridDashboard)
            and obj is not GridDashboard
        )
        is_dash_card = (
            lambda obj: isinstance(obj, type)
            and issubclass(obj, Dashcard)
            and obj is not Dashcard
        )
        for app_config in apps.get_app_configs():
            if module_has_submodule(app_config.module, "dashboards"):
                dash_module = import_module(f"{app_config.name}.dashboards")
                for name, klass in inspect.getmembers(dash_module, is_dash_card):
                    obj = klass(app_config)
                    dash_apps[app_config].update({klass: obj})
                    dash_lists[name].update({klass: obj})

        for app_config in apps.get_app_configs():
            if module_has_submodule(app_config.module, "dashboards"):
                dash_module = import_module(f"{app_config.name}.dashboards")
                for name, klass in inspect.getmembers(dash_module, is_dashs):
                    dash_grid = klass(app_config)
                    dash_grids[name] = dash_grid

                    for card in klass.cards:
                        card.filterset = dash_grid.filterset if card.filterset is None else card.filterset
                        card.grids.add(dash_grid)
                        obj = tuple(dash_lists[card.__name__].items())[0]
                        dash_grid.cards.update({obj[1].dashcard_name: obj})

        ordered_apps = OrderedDict()

        for app in sorted(dash_apps, key=lambda x: x.verbose_name):
            ordered_apps[app] = OrderedDict()
            for card in sorted(dash_apps[app], key=lambda x: dash_apps[app][x].title):
                ordered_apps[app][card] = dash_apps[app][card]

        self.dash_apps = ordered_apps
        self.dash_grids = dash_grids

    def get_urls(self):
        return [
            Dashclass.get_url(app)
            for app, dashes in self.dash_apps.items()
            for Dashclass in dashes.keys()
        ]

    @property
    def urls(self):
        return self.get_urls(), "dash", "dash"

    @property
    def media(self):
        from django.conf import settings

        url = getattr(settings, "CHARTJS_URL", DEFAULT_CHARTJS_URL)
        media = Media(js=[url, "js/dashboard.js"])
        for app, dashes in self.dash_apps.items():
            for dash in dashes.values():
                media += dash.media
        return media


dashboard = Dashboard()
