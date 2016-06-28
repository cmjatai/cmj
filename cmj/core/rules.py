
from django.utils.translation import ugettext_lazy as _

menu_dados_auxiliares = "menu_dados_auxiliares"
menu_tabelas_auxiliares = "menu_tabelas_auxiliares"
menu_contatos = "menu_contatos"

MENU_PERMS_FOR_USERS = (
    (menu_dados_auxiliares, _('Mostrar Menu Dados Auxiliares')),
    (menu_tabelas_auxiliares, _('Mostrar Menu de Tabelas Auxiliares')),
    (menu_contatos, _('Mostrar Menu de Cadastro de Contatos'))
)


search_trecho = 'search_trecho'
SEARCH_TRECHO = (
    (search_trecho, _('Consultar base de Trechos.')),
)


rules_patterns = []
