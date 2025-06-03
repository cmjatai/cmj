import datetime
from django.apps import apps
import pandas as pd
from collections import defaultdict, OrderedDict
from random import randint, seed
from django.db import models
from django.db.models import F
from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import MediaDefiningClass
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.decorators import classonlymethod
from django.views import View


same_func = lambda x: x
getcolor = lambda label=None: (
    f"#{randint(32,255):02x}{randint(32,255):02x}{randint(32,255):02x}"
    if label is None
    else f"{seed(label) or ''}#{randint(32,255):02x}{randint(32,255):02x}"
    f"{randint(32,255):02x}"
)


class Dashcard(View, metaclass=MediaDefiningClass):
    TYPE_AREA = "area"
    TYPE_BAR = "bar"
    TYPE_BUBBLE = "bubble"
    TYPE_DOUGHNUT = "doughnut"
    TYPE_LINE = "line"
    TYPE_PIE = "pie"
    TYPE_POLARAREA = "polarArea"
    TYPE_RADAR = "radar"
    TYPE_SCATTER = "scatter"
    TYPE_HTML = "html"

    app_config = None

    http_method_names = ["get"]
    template_name = None
    template_html = None

    chart_type = TYPE_BAR
    chart_options = None
    title = ""
    model = None
    filterset = None
    filterable = True
    render_filterset = True
    label_field = None
    label_name = None
    grids = set()
    allow_export_formats = "_all_"

    @classonlymethod
    def get_url(cls, app_config, **initkwargs):
        dash_name = cls.__name__.lower()
        return path(
            f"{app_config.label}/{dash_name}",
            cls.as_view(app_config=app_config, **initkwargs),
            name=f"{app_config.label}_{dash_name}",
        )

    def __init__(self, app_config, **kwargs):
        self.app_config = app_config
        super().__init__(**kwargs)

    def __str__(self):
        return self.render()

    @property
    def dash_name(self):
        return self.__class__.__name__.lower()

    @property
    def url(self):
        return reverse(f"dash:{self.app_config.label}_{self.dash_name}")

    @property
    def export_formats(self):
        from .registry import Dashboard

        if self.allow_export_formats == "_all_":
            return Dashboard.EXPORT_TYPES
        if not isinstance(self.allow_export_formats, list):
            self.allow_export_formats = [self.allow_export_formats]
        return list(
            filter(
                lambda x: x[0] in self.allow_export_formats,
                Dashboard.EXPORT_TYPES,
            )
        )

    def get_filter(self, data=None, queryset=None):
        if not self.filterable:
            return None
        if self.filterset is None:
            return None
        return self.filterset(data=data, queryset=queryset)

    def apply_filters(self, request, queryset):
        filter = self.get_filter(data=request.GET, queryset=queryset)
        if filter is not None:
            queryset = filter.qs
        return queryset

    def get_queryset(self, request):
        if self.model is None or not issubclass(self.model, models.base.Model):
            raise ImproperlyConfigured("The model property must be defined")
        queryset = self.model.objects.all()
        queryset = self.apply_filters(request, queryset)
        return queryset

    def get_labels(self, request, queryset=None):
        if queryset is None:
            queryset = self.get_queryset(request)
        if isinstance(self.label_field, tuple):
            label_getter = self.label_field[1](self.label_field[0])
            fmt_func = (
                self.label_field[2] if len(self.label_field) > 2 else same_func
            )
        else:
            label_getter = F(self.label_field)
            fmt_func = same_func

        return [
            fmt_func(l)
            for l in queryset.annotate(label=label_getter)
            .order_by("label")
            .distinct("label")
            .values_list("label", flat=True)
        ]

    def get_dataset_color(self, dataset_label):
        """
        Override this method in subclasses to provide a background color
        value for each dataset.
        """
        return None

    def get_datasets(self, request, queryset=None):
        if queryset is None:
            queryset = self.get_queryset(request)
        if isinstance(self.label_field, tuple):
            label_getter = self.label_field[1](self.label_field[0])
            label_fmt = (
                self.label_field[2] if len(self.label_field) > 2 else same_func
            )
        else:
            label_getter = F(self.label_field)
            label_fmt = same_func
        datasets = []
        for ds in self.datasets:
            dataset = ds.copy()
            if "data_field" in dataset:
                data_field = dataset.pop("data_field")
                if isinstance(data_field, tuple):
                    data_getter = data_field[1](data_field[0])
                    fmt_func = (
                        data_field[2] if len(data_field) > 2 else same_func
                    )
                else:
                    data_getter = F(data_field)
                    fmt_func = same_func
            if "label_field" in dataset:
                label_field = dataset.pop("label_field")
                if isinstance(label_field, tuple):
                    ds_label_getter = label_field[1](label_field[0])
                    dl_formatter = (
                        label_field[3] if len(label_field) > 2 else same_func
                    )
                else:
                    ds_label_getter = F(label_field)
                    dl_formatter = same_func
                data_values = (
                    queryset.values(
                        ds_label=ds_label_getter, label=label_getter
                    )
                    .order_by("ds_label", "label")
                    .annotate(value=data_getter)
                )
                subdatasets = defaultdict(OrderedDict)
                for r in data_values:
                    subdatasets[r["ds_label"]][label_fmt(r["label"])] = (
                        fmt_func(r["value"])
                    )
                for label, values in subdatasets.items():
                    subdataset = dataset.copy()
                    subdataset.update(
                        {"label": dl_formatter(label), "data": values}
                    )
                    bgcolor = self.get_dataset_color(subdataset["label"])
                    if bgcolor is not None:
                        subdataset["backgroundColor"] = bgcolor
                    datasets.append(subdataset)
            else:
                data_values = (
                    queryset.values(label=label_getter)
                    .annotate(value=data_getter)
                    .order_by("label")
                )
                dataset["data"] = [fmt_func(r["value"]) for r in data_values]
                bgcolor = [
                    self.get_dataset_color(r["label"]) for r in data_values
                ]
                if any(bgcolor):
                    dataset["backgroundColor"] = bgcolor
                datasets.append(dataset)
        return datasets

    def get_prev_page(self, request=None, queryset=None):
        """
        Override this method in subclasses to provide a query value
        to get previous data page. None means no previous button.
        request and queryset params cannot be passed. Check if it is not None
        before using it.
        """
        return None

    def get_next_page(self, request=None, queryset=None):
        """
        Override this method in subclasses to provide a query value
        to get next data page. None means no next button.
        request and queryset params cannot be passed. Check if it is not None
        before using it.
        """
        return None

    def get_extra_context(self, request=None):
        """
        Override this method in subclasses to provide extra template context
        """
        return {}

    def render(self):
        if self.template_name:
            template_names = [self.template_name]
        else:
            default_name = 'dashboard_card' if self.grids else 'dashcard'
            template_names = [
                f"dashboard/{self.app_config.label}/{self.dash_name}.html",
                f"dashboard/{self.app_config.label}/{default_name}.html",
                f"dashboard/{default_name}.html",
            ]

        context = {
            "card": self,
            "filter": self.get_filter(),
            "render_filterset": self.render_filterset,
            "previous_page": self.get_prev_page(),
            "next_page": self.get_next_page(),
        }

        context.update(self.get_extra_context())
        return render_to_string(template_names, context)

    def chartdata(self, request, queryset=None):
        if queryset is None:
            queryset = self.get_queryset(request)
        labels = self.get_labels(request, queryset)
        datasets = self.get_datasets(request, queryset)
        config = {
            "type": self.chart_type,
            "data": {"labels": labels, "datasets": datasets},
            "querystr": request.GET.urlencode(),
        }
        if self.chart_type == Dashcard.TYPE_HTML:
            context = config.pop("data")
            context["label_name"] = self.label_name
            config["html"] = self.html(request, context=context)
        prev_page = self.get_prev_page(request, queryset)
        next_page = self.get_next_page(request, queryset)
        if prev_page is not None:
            config["previous_page"] = prev_page
        if next_page is not None:
            config["next_page"] = next_page
        if self.chart_options:
            config["options"] = self.chart_options
        return config

    def to_dataframe(self, request):
        queryset = self.get_queryset(request)
        labels = self.get_labels(request, queryset)
        data = self.get_datasets(request, queryset)

        if self.label_name:
            cols = [self.label_name] + labels
            k_label = self.label_name
        elif any(["label" in ds for ds in data]):
            cols = ["label"] + labels
            k_label = "label"
        else:
            cols = labels

        flat_data = []

        for ds in data:
            fds = dict()
            if "label" in ds:
                fds[k_label] = ds["label"]
            if isinstance(ds["data"], dict):
                fds.update(ds["data"])
            else:
                fds.update(zip(labels, ds["data"]))
            flat_data.append(fds)

        df = pd.DataFrame(flat_data, columns=cols)

        if df.shape[0] <= 1:  # shape[0] diz o número de linhas do dataframe
            df = df.transpose()

        return df

    def export_data(self, request, fmt):
        formats = self.export_formats
        fmt_tuple = list(filter(lambda x: x[0] == fmt, formats))
        if not fmt_tuple:
            fmt_tuple = formats  # Default to CSV
        fmt, label, contenttype = fmt_tuple[0]

        df = self.to_dataframe(request)

        filename = f"{self.dash_name}-{datetime.date.today():%Y-%m-%d}.{fmt}"
        response = HttpResponse(
            headers={
                "Content-Type": contenttype,
                "Content-Disposition": f'attachment; filename="{filename}"',
            }
        )

        if fmt == "csv":
            df.to_csv(response)
        elif fmt == "xlsx":
            df.to_excel(response)
        elif fmt == "html":
            df.to_html(response, na_rep="")
        elif fmt == "json":
            df.to_json(response, orient="records")
        else:
            df.to_string(response, na_rep="")

        return response

    def html(self, request, context):
        if self.template_html:
            template_names = [self.template_html]
        else:
            default_name = 'dashboard_card_html' if self.grids else 'dashcard_html'
            template_names = [
                f"dashboard/{self.app_config.label}/{self.dash_name}.html",
                f"dashboard/{self.app_config.label}/{default_name}.html",
                f"dashboard/{default_name}.html",
            ]

        return render_to_string(
            request=request, template_name=template_names, context=context
        )

    def get(self, request):
        export = request.GET.get("export", None)
        if export is None:
            data = self.chartdata(request)
            return JsonResponse(data)
        else:
            return self.export_data(request, fmt=export)


class GridDashboard(View, metaclass=MediaDefiningClass):
    """
    Classe base para dashboards que utilizam filtro compartilhado
    entre os cards.
    Pode ser utilizada para dashboards que possuem cards com filtros
    diferentes, mas que compartilham o mesmo conjunto de filtros.
    """
    cards = []
    grid = {}
    template_name = None
    filterset = None
    render_filterset = True
    app_config = None

    kwargs = {}

    def __call__(self, *args, **kwds):
        self.kwargs.update(kwds)
        return self

    def get_filter(self, data=None, queryset=None):
        if self.filterset is None:
            return None
        data = data or {}
        data.update(self.kwargs)
        #self.kwargs = {}  # Clear kwargs after using them
        filter = self.filterset(data=data, queryset=queryset)
        return filter

    def apply_filters(self, request, queryset):
        filter = self.get_filter(data=request.GET, queryset=queryset)
        if filter is not None:
            queryset = filter.qs
        return queryset

    def __init__(self, app_config=None, **kwargs):
        if app_config is None:
            if self.app_config is None:
                raise ImproperlyConfigured(
                    "The app_config property must be defined"
                )
            app_config = apps.get_app_config(self.app_config)
        self.app_config = app_config
        self.cards = defaultdict(dict)
        super().__init__(**kwargs)

    def __str__(self):
        return self.render()

    @property
    def dashboard_name(self):
        return self.__class__.__name__.lower()

    def get_extra_context(self, request=None):
        """
        Override this method in subclasses to provide extra template context
        """
        return {}

    def render(self):
        if self.template_name:
            template_names = [self.template_name]
        else:
            template_names = [
                f"dashboard/{self.app_config.label}/{self.dashboard_name}.html",
                f"dashboard/{self.app_config.label}/dashboard.html",
                f"dashboard/dashboard.html",
            ]

        context = {
            "dash": self,
            "rows": self.grid['rows'],
            "cards": {k: v[1] for k, v in self.cards.items()},
            "filter": self.get_filter(),
            'render_filterset': self.render_filterset,
            #"previous_page": self.get_prev_page(),
            #"next_page": self.get_next_page(),
        }

        context.update(self.get_extra_context())
        return render_to_string(template_names, context)

