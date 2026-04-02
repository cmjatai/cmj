from django.utils.translation import gettext_lazy as _

from cmj.loa.models import Despesa, Loa, SubFuncao, UnidadeOrcamentaria
from cmj.loa.views.mixins import LoaContextDataMixin
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud


class DespesaCrud(MasterDetailCrud):
    model = Despesa
    parent_field = "loa"
    public = [RP_LIST, RP_DETAIL]
    ordered_list = False
    frontend = Loa._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

    class ListView(MasterDetailCrud.ListView):
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} despesa-list"
            return context


class UnidadeOrcamentariaCrud(MasterDetailCrud):
    model = UnidadeOrcamentaria
    parent_field = "loa"


class SubFuncaoCrud(MasterDetailCrud):
    model = SubFuncao
    parent_field = "loa"
