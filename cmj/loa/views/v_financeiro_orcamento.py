from django.utils.translation import gettext_lazy as _

from cmj.loa.models import Despesa, Loa, SubFuncao, UnidadeOrcamentaria
from cmj.loa.views.v_mixins import LoaContextDataMixin
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud


class DespesaCrud(MasterDetailCrud):
    model = Despesa
    parent_field = "loa"
    public = [RP_LIST, RP_DETAIL]
    ordered_list = False
    frontend = Loa._meta.app_label

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 1

        def get_context_data(self, **kwargs):
            self.loa = Loa.objects.get(pk=self.kwargs["pk"])
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} despesa-list"
            return context


class UnidadeOrcamentariaCrud(MasterDetailCrud):
    model = UnidadeOrcamentaria
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass


class SubFuncaoCrud(MasterDetailCrud):
    model = SubFuncao
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass
