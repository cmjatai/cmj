from django.urls.conf import include, re_path

from . import views
from .apps import AppConfig

app_name = AppConfig.name


urlpatterns = [
    re_path(
        r"^checklist/template",
        include(
            views.ChecklistTemplateCrud.get_urls()
            + views.ChecklistSectionCrud.get_urls()
            + views.ChecklistItemCrud.get_urls()
            + views.ItemOptionCrud.get_urls(),
        ),
    ),
    re_path(
        r"^checklist/instance",
        include(
            views.ChecklistInstanceCrud.get_urls()
            + views.ChecklistItemResponseCrud.get_urls()
            + views.ChecklistItemAttachmentCrud.get_urls(),
        ),
    ),
]
