from django.urls.conf import re_path
from django.views.generic.base import TemplateView

from cmj.urls import urlpatterns as original_patterns

ptrn = [
    re_path(r"^zzzz$", TemplateView.as_view(template_name="index.html"), name="zzzz")
]
urlpatterns = original_patterns + ptrn
