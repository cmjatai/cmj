import logging

from django.core.cache import cache

from django.conf import settings
from django import template
from django.core.handlers.asgi import ASGIRequest
from django.db.models import Q
from django.shortcuts import render
from django.urls.base import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import yaml

from cmj.sigad.models import Classe, Documento
from cmj.utils import get_breadcrumb_classes

logger = logging.getLogger(__name__)

register = template.Library()


def breadcrumb_function(context):

    rcontext = {
        'classes': [],
        'request': context['request'],
        'user': context['user']
    }

    try:
        if 'breadcrumb_classes' in context:
            breadcrumb_classes = context.get('breadcrumb_classes', [])
            #if breadcrumb_classes:
            #    last = breadcrumb_classes[-1]
            #    breadcrumb_classes = list(filter(
            #        lambda x: not hasattr(x, 'perfil') or hasattr(
            #            x, 'perfil') and x.perfil != CLASSE_REDIRECT_VIEWS,
            #        breadcrumb_classes[:-1]))
            #    breadcrumb_classes.append(last)
        else:
            get_breadcrumb_classes(context, request=context['request'])
            breadcrumb_classes =  context.get('breadcrumb_classes', [])
        rcontext['classes'] = breadcrumb_classes
    except:
        pass
    filter_classes = list(filter(lambda x: hasattr(x, 'subtitle'), rcontext['classes']))
    context.update({'breadcrumb_subtitle': filter_classes[-1].subtitle if filter_classes else ''})
    return rcontext



@register.inclusion_tag('base_breadcrumb.html', takes_context=True)
def breadcrumb(context):
    """Renderiza o breadcrumb do Sigad

    O breadcrumb é renderizado a partir da variável
    breadcrumb_classes no contexto.
    """
    rcontext = breadcrumb_function(context)
    return rcontext


@register.inclusion_tag('menus/sigad/menu.html', takes_context=True)
def sigad_menu(context, field=None, parent=None):
    return sigad_run(context, field, parent)


def sigad_run(context, field, parent=None):
    params = {
        str(field): True,
        'parent': parent,
    }
    classes_publicas = Classe.objects.qs_classes_publicas().filter(**params)
    return {'classes': classes_publicas, 'field_name': field}


@register.inclusion_tag('menus/nav.html', takes_context=True)
def sigad_navbar(context, field=None):

    user = context['user']

    def encapsule_menu_em_dropdown_portal(menu):
        if user.is_anonymous or user.is_only_socialuser():
            return menu
        else:
            return [
                {
                    'title': _('Portal'),
                    'url': '',
                    'children': menu
                }
            ]


    if not user.is_superuser:
        menu = cache.get('portalcmj_menu_publico')
        if menu:
            return {
                'menu': encapsule_menu_em_dropdown_portal(menu)
            }

    raizes = sigad_run(context, field)['classes']
    params = {
        str(field): True,
    }
    def get_how_menu(classes):
        item_list = []
        for classe in classes:
            item = {
                'title': classe.apelido or classe.titulo,
                'children': [],
                'url': f'/{classe.absolute_slug}',
                'active': '',
            }
            item_list.append(item)
            item['children'] = get_how_menu(classe.childs.qs_classes_publicas().filter(**params))
            if item['title'].startswith('__'):
                item['title'] = ''
            if classe.url_redirect.startswith('__'):
                item['url'] = ''

        return item_list

    menu = get_how_menu(raizes)
    if not user.is_superuser:
        cache.set('portalcmj_menu_publico', menu, 600)

    menu = encapsule_menu_em_dropdown_portal(menu)

    return {'menu': menu}

@register.inclusion_tag('menus/menu.html', takes_context=True)
def menu(context, path=None, pk=None):
    return nav_run(context, path, pk)


@register.inclusion_tag('menus/subnav.html', takes_context=True)
def subnav(context, path=None, pk=None):
    return nav_run(context, path, pk)


@register.inclusion_tag('menus/nav.html', takes_context=True)
def navbar(context, path=None, pk=None):
    return nav_run(context, path, pk)


def nav_run(context, path=None, pk=None):
    """Renderiza sub navegação para objetos no padrão Mestre Detalhe

    Existem três possíveis fontes de busca do yaml
    com precedência enumerada abaixo:
        1) Se a variável path não é nula;
        2) Se existe no contexto a chave subnav_template_name;
        3) o path default: <app_name>/subnav.yaml

    Os campos esperados nos arquivos yaml são:
        title
        url
        check_permission - opcional. quando usado
            será realizado o teste de permissão para renderizá-lo.
    """
    menu = None

    if not pk:
        root_pk = context.get('root_pk', None)
        if not root_pk:
            obj = context.get('object', None)
            if obj:
                root_pk = obj.pk
    else:
        root_pk = pk

    if root_pk or 'subnav_template_name' in context or path:
        request = context['request']

        """
        As implementações das Views de Modelos que são dados auxiliares e
        de diversas app's estão concentradas em urls com prefixo 'sistema'.
        Essas Views não possuem submenu de navegação e são incompativeis com a
        execução deste subnav. Inicialmente, a maneira mais prática encontrada
        de isolar foi com o teste abaixo.
        """

        rm = request.resolver_match
        app_template = rm.app_name.rsplit('.', 1)[-1]

        if path:
            yaml_path = path
        elif 'subnav_template_name' in context:
            yaml_path = context['subnav_template_name']
        else:
            yaml_path = '%s/%s' % (app_template, 'subnav.yaml')

        if not yaml_path:
            return

            """
            Por padrão, são carragados dois Loaders,
            filesystem.Loader - busca em TEMPLATE_DIRS do projeto atual
            app_directories.Loader - busca em todas apps instaladas
            A função nativa abaixo busca em todos os Loaders Configurados.
            """
        try:
            yaml_template = template.loader.get_template(yaml_path)
        except:
            return

        try:
            # print(timezone.now())
            rendered = yaml_template.template.render(context)
            menu = yaml.full_load(rendered)
            resolve_urls_inplace(menu, root_pk, rm, context)
            # print(timezone.now())
        except Exception as e:
            logger.error(
                _('Erro na conversão do yaml %s. App: %s. Erro: %s') % (
                    yaml_path, rm.app_name, str(e)))

    return {'menu': menu}


def resolve_urls_inplace(menu, pk, rm, context):
    if isinstance(menu, list):
        list_active = ''
        for item in menu:
            # print(item)
            menuactive = resolve_urls_inplace(item, pk, rm, context)
            list_active = menuactive if menuactive else list_active
            if not isinstance(item, list):
                item['active'] = menuactive

        return list_active
    else:
        if 'url' in menu:

            url_name = menu['url']

            if 'check_permission' in menu and not context[
                    'request'].user.has_perm(menu['check_permission']):
                menu['url'] = ''
                menu['active'] = ''
            else:
                if ':' in url_name:
                    try:
                        menu['url'] = reverse('%s' % menu['url'],
                                              kwargs={'pk': pk})
                    except:
                        try:
                            menu['url'] = reverse('%s' % menu['url'])
                        except:
                            pass
                else:
                    try:
                        menu['url'] = reverse('%s:%s' % (
                            rm.app_name, menu['url']), kwargs={'pk': pk})
                    except:
                        try:
                            menu['url'] = reverse('%s:%s' % (
                                rm.app_name, menu['url']))
                        except:
                            pass

                menu['active'] = 'active'\
                    if context['request'].path == menu['url'] else ''
                if not menu['active']:
                    """
                    Se não encontrada diretamente,
                    procura a url acionada dentro do crud, caso seja um.
                    Serve para manter o active no subnav correto ao acionar
                    as funcionalidades diretas do MasterDetailCrud, como:
                    - visualização de detalhes, adição, edição, remoção.
                    """
                    try:
                        if 'view' in context:
                            view = context['view']
                            if hasattr(view, 'crud'):
                                urls = view.crud.get_urls()
                                for u in urls:
                                    if (u.name == url_name or
                                            'urls_extras' in menu and
                                            u.name in menu['urls_extras']):
                                        menu['active'] = 'active'
                                        break
                    except:
                        url_active = menu.get('url', '')
                        logger.warning(
                            f'Não foi possível definir se url {url_active} é a url ativa.')
        elif 'check_permission' in menu and not context[
                'request'].user.has_perm(menu['check_permission']):
            menu['active'] = ''
            del menu['children']

        if 'children' in menu:
            menu['active'] = resolve_urls_inplace(
                menu['children'], pk, rm, context)
        return menu['active']
