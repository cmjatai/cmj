import re

from django.contrib import messages
from django.db.models import Case, Value, When
from django.shortcuts import redirect
from django.urls import reverse
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
            # LOA-AGR-012: reabrir a criação (recarregar, abrir duas vezes) reaproveita
            # o último agrupamento com o nome padrão que continua vazio
            if (
                ultimo_agrupamento
                and re.fullmatch(rf"{nome_base}( \d+)?", ultimo_agrupamento.nome)
                and ultimo_agrupamento.esta_vazio()
            ):
                self.object = ultimo_agrupamento
                return redirect(self.update_url)

            if ultimo_agrupamento:
                numero = 1
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
                transf = ""
                if e.fase == e.TRANSFORMADA_EM_COLETIVA:
                    transf += "<em>Transformada em coletiva</em>"
                entidade = str(e.entidade) + "<br>" if e.entidade else ""
                src = f"""
                    <strong>{e.unidade}</strong><br>
                    - {f"{entidade}" if entidade else ""}
                    - <strong>{", ".join(str(p) for p in e.parlamentares.all())}</strong>
                    - {e}<br>
                    {transf}
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

        def form_valid(self, form):
            response = super().form_valid(form)
            # LOA-AGR-083: avisa, sem bloquear, que emendas que permitem junção
            # foram liberadas sem virar coletiva
            n = getattr(form, "liberadas_sem_juncao", 0)
            if n:
                messages.info(
                    self.request,
                    _(
                        "{} emenda(s) que permitem junção em emenda coletiva "
                        "foram liberadas individualmente, sem junção."
                    ).format(n),
                )
            return response

        def get_success_url(self):
            return reverse(
                "cmj.loa:agrupamento_detail",
                kwargs={"pk": self.object.pk},
            )

    class DetailView(LoaContextDataMixin, MasterDetailCrud.DetailView):
        layout_key = "AgrupamentoDetail"

        def hook_despesas(self, obj, verbose_name, field_display):
            str_regs = []
            for rc in obj.agrupamentoregistrocontabil_set.order_by("-percentual"):
                src = f"{rc.str_percentual}% - {rc.despesa}"
                str_regs.append(src)
            src = "".join(map(lambda x: f"<li>{x}</li>", str_regs))

            return verbose_name, f"<ul>{src}</ul>"

        def hook_emendas(self, obj, verbose_name, field_display):
            str_regs = []

            total_emendas = obj.emendas(manager="all_objects").count()
            for i, e in enumerate(obj.emendas(manager="all_objects").all()):
                entidade = str(e.entidade) + "<br>" if e.entidade else ""
                # se for o ultimo não colocar a linha divisória
                src = f"""
                    <strong>{e.unidade}</strong> <a href="{reverse('cmj.loa:emendaloa_detail', kwargs={'pk': e.pk})}" target="_blank" class="btn btn-sm btn-primary"><i class="fa fa-external-link"></i></a><br>
                    - {f"{entidade}" if entidade else ""}
                    - {e}<br>
                    <small class="text-muted">{e.get_fase_display()}</small><br>
                    {'' if i == total_emendas - 1 else '<hr class="divider">'}
                """
                str_regs.append(src)
            src = "".join(
                map(lambda x: f"<li style='padding: 1rem 0;'>{x}</li>", str_regs)
            )

            return (
                "Emendas Substituídas/Classificadas",
                f'<ul style="line-height: 1.4;">{src}</ul>',
            )

        def hook_emendas_coletivas(self, obj, verbose_name, field_display):
            str_regs = []

            # retire o link do e e coloque em um icone afrente do da unidade para abrir em blank
            # substituao por fa-link para indicar que é um link externo

            total_emendas_coletivas = obj.emendas_coletivas_geradas.count()
            for i, e in enumerate(obj.emendas_coletivas_geradas.all()):
                entidade = str(e.entidade) + "<br>" if e.entidade else ""
                src = f"""
                    <strong>{e.unidade}</strong> <a href="{reverse('cmj.loa:emendaloa_detail', kwargs={'pk': e.pk})}" target="_blank" class="btn btn-sm btn-primary"><i class="fa fa-external-link"></i></a><br>
                    - {f"{entidade}" if entidade else ""}
                    - {e}<br>
                    <small class="text-muted">{e.get_fase_display()}</small><br>
                    {'' if i == total_emendas_coletivas - 1 else '<hr class="divider">'}
                """
                str_regs.append(src)
            src = "".join(
                map(lambda x: f"<li style='padding: 1rem 0;'>{x}</li>", str_regs)
            )

            return (
                "Emendas Coletivas Geradas",
                f'<ul style="line-height: 1.2;">{src}</ul>',
            )
