from django.urls.conf import re_path, include

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns = [
    #url(r'^video/', include(urlpatterns_sigad))

]
