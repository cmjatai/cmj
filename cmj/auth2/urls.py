from django.conf.urls import url
from django.contrib.auth import views

from cmj.auth2.forms import LoginForm

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    url(r'^login/$',
        views.login, {'template_name': 'auth2/login.html',
                      'authentication_form': LoginForm,
                      'extra_context': {
                          'fluid': '-fluid'
                      }},
        name='login'),

    url(r'^logout/$', views.logout,
        {'next_page': '/login'}, name='logout', )
]
