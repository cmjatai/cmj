from django.db.models import Q
from django.urls.base import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from cmj.loa.forms.f_financeiro_execucao import EmpenhoFilterSet, EmpenhoForm
from cmj.loa.models import Empenho, Loa
from cmj.loa.views.v_mixins import LoaContextDataMixin
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud


class EmpenhoCrud(MasterDetailCrud):
    model = Empenho
    public = [RP_LIST, RP_DETAIL]
    frontend = Empenho._meta.app_label
    parent_field = "orgao__loa"
    ordered_list = False

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        ordered_list = False

        @property
        def verbose_name(self):
            return _("Empenho do Orçamento Impositivo")

        @property
        def verbose_name_plural(self):
            return _("Empenhos do Orçamento Impositivo")

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = EmpenhoForm

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} empenho-update"
            return context

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = self.object.orgao.loa
            initial["emendas"] = self.object.empenhoemendaajuste_set.filter(
                emendaloa__isnull=False
            ).values_list("emendaloa__pk", flat=True)
            initial["ajustes"] = self.object.empenhoemendaajuste_set.filter(
                ajuste__isnull=False
            ).values_list("ajuste__pk", flat=True)
            return initial

        def get(self, request, *args, **kwargs):
            return MasterDetailCrud.UpdateView.get(self, request, *args, **kwargs)

    class DetailView(MasterDetailCrud.DetailView):
        layout_key = "EmpenhoDetail"

        def hook_numero_licitacao(self, empenho, verbose_name="", display_field=""):
            if not empenho.numero_licitacao:
                return "", ""
            return verbose_name, display_field

        def hook_empenhoemendaajuste_set(
            self, empenho, verbose_name="", display_field=""
        ):
            emendas_ajustes = []

            for ea in empenho.empenhoemendaajuste_set.order_by(
                "emendaloa__materia__numero", "ajuste__oficio_ajuste_loa__loa__ano"
            ):
                if ea.emendaloa:
                    emendas_ajustes.append(
                        f"""
                        <li>
                        <a href="{reverse_lazy('cmj.loa:emendaloa_detail', kwargs={'pk': ea.emendaloa.pk})}">
                            {ea.emendaloa.materia.epigrafe_short}
                        </a> - {ea.emendaloa.ementa_format}
                        </li>
                        """
                    )
                elif ea.ajuste:
                    emendas_ajustes.append(
                        f"""
                        <li>
                        <a href="{reverse_lazy('cmj.loa:registroajusteloa_detail', kwargs={'pk': ea.ajuste.pk})}">
                            {ea.ajuste.oficio_ajuste_loa}
                        </a> - {ea.ajuste.descricao}
                        </li>
                        """
                    )

            if not emendas_ajustes:
                return (
                    _(
                        "Nenhuma emenda impositiva ou ajuste cadastrado para este empenho."
                    ),
                    "",
                )

            return (
                _("Emendas Impositivas e Ajustes"),
                "<ul>" + "".join(emendas_ajustes) + "</ul>",
            )

    class ListView(FilterView, MasterDetailCrud.ListView):
        filterset_class = EmpenhoFilterSet
        layout_key = "EmpenhoList"
        paginate_by = 25
        ordering = "-codigo"

        def get_queryset(self):
            qs = super().get_queryset()

            if self.request.user.has_perm("loa.change_empenho"):
                return (
                    qs.filter(orgao__loa=self.loa)
                    .distinct()
                    .order_by("-empenhoemendaajuste_set", "-codigo")
                )

            return qs.filter(
                Q(empenhoemendaajuste_set__ajuste__oficio_ajuste_loa__loa=self.loa)
                | Q(empenhoemendaajuste_set__emendaloa__loa=self.loa)
            ).distinct()

        def get(self, request, *args, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs["pk"])
            return FilterView.get(self, request, *args, **kwargs)

        def hook_header_detail(self):
            return "Processo / Fornecedor"

        def hook_detail(self, empenho, *args, **kwargs):
            return f"""
                Processo: {empenho.processo} - {'Modalidade: ' if empenho.modalidade else ''}{empenho.modalidade} - {'Número de Licitação: ' if empenho.numero_licitacao else ''}{empenho.numero_licitacao}<br>
                Dotação: {empenho.dotacao}<br>
                {empenho.cpfcnpj}<br>{empenho.nome}
                {("<hr>" + str(empenho.unidade)) if empenho.unidade and self.request.user.has_perm("loa.change_empenho") else ""}
                {("<br>" + empenho.historico) if empenho.historico and self.request.user.has_perm("loa.change_empenho") else ""}
            """

        def hook_header_emendas_ajustes(self):
            return "Emendas Impositivas e Ajustes"

        def hook_emendas_ajustes(self, empenho, *args, **kwargs):
            emendas_ajustes = []

            for ea in empenho.empenhoemendaajuste_set.all():
                if ea.emendaloa:
                    emendas_ajustes.append(
                        f"""
                        <li>
                        <a href="{reverse_lazy('cmj.loa:emendaloa_detail', kwargs={'pk': ea.emendaloa.pk})}">
                            {ea.emendaloa.materia.epigrafe_short}
                        </a></li>
                        """
                    )
                elif ea.ajuste:
                    emendas_ajustes.append(
                        f"""
                        <li>
                        <a href="{reverse_lazy('cmj.loa:registroajusteloa_detail', kwargs={'pk': ea.ajuste.pk})}">
                            Ajuste à LOA {ea.ajuste.oficio_ajuste_loa.loa.ano} - {ea.ajuste.get_tipo_display()}
                        </a>
                        </li>
                        """
                    )

            if not emendas_ajustes:
                return _(
                    "Nenhuma emenda impositiva ou ajuste cadastrado para este empenho."
                )

            return (f"<ul>{''.join(emendas_ajustes)}</ul>", "", "")
