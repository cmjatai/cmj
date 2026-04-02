from django.utils.translation import gettext_lazy as _

from cmj.loa.forms import AgrupamentoForm
from cmj.loa.models import Agrupamento, Loa
from cmj.loa.views.mixins import LoaContextDataMixin
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud


class AgrupamentoCrud(MasterDetailCrud):
    model = Agrupamento
    parent_field = "loa"
    public = [RP_LIST, RP_DETAIL]
    frontend = Agrupamento._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

        @property
        def create_url(self):
            url = super().create_url
            if self.request.user.has_perm("loa.emendaloa_full_editor"):
                url = self.resolve_url("create", args=(self.kwargs["pk"],))
            return url

        @property
        def update_url(self):

            url = super().update_url
            if self.request.user.has_perm("loa.emendaloa_full_editor"):
                url = self.resolve_url("update", args=(self.object.id,))

            return url

        @property
        def delete_url(self):

            url = super().delete_url
            if self.request.user.has_perm("loa.emendaloa_full_editor"):
                url = self.resolve_url("delete", args=(self.object.id,))

            return url

        @property
        def cancel_url(self):
            url = self.resolve_url("detail", args=(self.kwargs["pk"],))
            return url

    class DeleteView(MasterDetailCrud.DeleteView):
        permission_required = ("loa.emendaloa_full_editor",)

    class CreateView(MasterDetailCrud.CreateView):
        permission_required = ("loa.emendaloa_full_editor",)
        layout_key = "AgrupamentoCreate"

        def get_success_url(self):
            return self.update_url

    class ListView(MasterDetailCrud.ListView):
        def hook_despesas(self, obj, ss, url):
            str_regs = []
            for rc in obj.agrupamentoregistrocontabil_set.order_by("-percentual"):
                src = f"{rc.str_percentual}% - {rc.despesa}"
                str_regs.append(src)
            src = "".join(map(lambda x: f"<li>{x}</li>", str_regs))

            return f"<ul>{src}</ul>", ""

    class UpdateView(MasterDetailCrud.UpdateView):
        permission_required = ("loa.emendaloa_full_editor",)
        layout_key = None
        form_class = AgrupamentoForm

        def get_context_data(self, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs["root_pk"])
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} agrupamento-update"
            return context

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = self.object.loa
            initial["user"] = self.request.user
            return initial

    class DetailView(MasterDetailCrud.DetailView):

        def hook_despesas(self, obj, verbose_name, field_display):
            str_regs = []
            for rc in obj.agrupamentoregistrocontabil_set.order_by("-percentual"):
                src = f"{rc.str_percentual}% - {rc.despesa}"
                str_regs.append(src)
            src = "".join(map(lambda x: f"<li>{x}</li>", str_regs))

            return verbose_name, f"<ul>{src}</ul>"
