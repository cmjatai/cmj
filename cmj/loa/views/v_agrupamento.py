from django.db.models import Case, Value, When
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from cmj.loa.forms.f_agrupamento import AgrupamentoForm
from cmj.loa.models import Agrupamento, Loa
from cmj.loa.views.v_mixins import LoaContextDataMixin
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud


class AgrupamentoCrud(MasterDetailCrud):
    model = Agrupamento
    parent_field = "loa"
    public = [RP_LIST, RP_DETAIL]
    frontend = Agrupamento._meta.app_label
    ordered_list = False

    class BaseMixin(MasterDetailCrud.BaseMixin):
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

    class CreateView(LoaContextDataMixin, MasterDetailCrud.CreateView):
        permission_required = ("loa.emendaloa_full_editor",)
        layout_key = "AgrupamentoCreate"

        def get(self, request, *args, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs["pk"])
            # captura o padrão do nome e incrementa número
            nome_base = "Novo Agrupamento"
            ultimo_agrupamento = (
                Agrupamento.objects.filter(loa=self.loa, nome__startswith=nome_base)
                .order_by("-id")
                .first()
            )
            if ultimo_agrupamento:
                numero = 1
                import re

                match = re.search(r"(\d+)$", ultimo_agrupamento.nome)
                if match:
                    numero = int(match.group(1)) + 1
                nome = f"{nome_base} {numero}"
            else:
                nome = nome_base

            self.object = Agrupamento.objects.create(loa=self.loa, nome=nome)
            return redirect(self.update_url)

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 100
        ordered_list = False

        def get_queryset(self):
            qs = (
                super()
                .get_queryset()
                .annotate(
                    has_no_emendas=Case(
                        When(agrupamentoemendaloa_set__isnull=True, then=Value(0)),
                        default=Value(1),
                    )
                )
            )
            return qs.order_by(
                "has_no_emendas",
                "agrupamentoemendaloa_set__emendaloa__unidade__especificacao",
            ).distinct()

        def hook_despesas(self, obj, ss, url):
            str_regs = []
            for rc in obj.agrupamentoregistrocontabil_set.order_by("-percentual"):
                src = f"{rc.str_percentual}% - {rc.despesa}"
                str_regs.append(src)
            src = "".join(map(lambda x: f"<li>{x}</li>", str_regs))

            return f"<ul>{src}</ul>", ""

        def hook_emendas(self, obj, ss, url):
            str_regs = []
            for e in obj.emendas(manager="all_objects").all():
                entidade = str(e.entidade) + "<br>" if e.entidade else ""
                src = f"""
                    - <strong>{e.unidade}</strong><br>
                    - {f"{entidade}" if entidade else ""}
                    - <strong>{", ".join(str(p) for p in e.parlamentares.all())}</strong>
                    - {e}<br>
                    <hr class="divider">
                """
                str_regs.append(src)
            src = "".join(map(lambda x: f"<li>{x}</li>", str_regs))

            return f"""<div class="emendas-list"><ul>{src}</ul></div>""", ""

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
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

        def hook_emendas(self, obj, verbose_name, field_display):
            str_regs = []
            for e in obj.emendas(manager="all_objects").all():
                entidade = str(e.entidade) + "<br>" if e.entidade else ""
                src = f"""
                  {e.unidade}<br>
                  {entidade}
                   {e}
                """
                str_regs.append(src)
            src = "".join(map(lambda x: f"<li>{x}</li>", str_regs))

            return verbose_name, f"<ul>{src}</ul>"
