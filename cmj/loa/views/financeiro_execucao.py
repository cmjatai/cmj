from django.db.models import Q
from django.urls.base import reverse_lazy
from django.utils.translation import gettext_lazy as _

from cmj.loa.models import Empenho, Loa
from cmj.loa.views.mixins import LoaContextDataMixin
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud


class EmpenhoCrud(MasterDetailCrud):
    model = Empenho
    public = [RP_LIST, RP_DETAIL]
    frontend = Empenho._meta.app_label
    parent_field = "orgao__loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        @property
        def verbose_name(self):
            return _("Empenho do Orçamento Impositivo")

        @property
        def verbose_name_plural(self):
            return _("Empenhos do Orçamento Impositivo")

    class DetailView(MasterDetailCrud.DetailView):
        layout_key = "EmpenhoDetail"

        def hook_empenhoemendaajuste_set(
            self, empenho, verbose_name="", display_field=""
        ):
            emendas_ajustes = []

            for ea in empenho.empenhoemendaajuste_set.all():
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

    class ListView(MasterDetailCrud.ListView):
        layout_key = "EmpenhoList"
        paginate_by = 25
        ordering = "-codigo"

        def get_queryset(self):
            qs = super().get_queryset()
            return qs.filter(
                Q(empenhoemendaajuste_set__ajuste__oficio_ajuste_loa__loa=self.loa)
                | Q(empenhoemendaajuste_set__emendaloa__loa=self.loa)
            ).distinct()

        def get(self, request, *args, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs["pk"])
            return super().get(request, *args, **kwargs)

        def hook_header_detail(self):
            return "Processo / Fornecedor"

        def hook_detail(self, empenho, *args, **kwargs):
            return f"""
                Processo: {empenho.processo} - {'Modalidade: ' if empenho.modalidade else ''}{empenho.modalidade} - {'Número de Licitação: ' if empenho.numero_licitacao else ''}{empenho.numero_licitacao}<br>
                Dotação: {empenho.dotacao}<br>
                {empenho.cpfcnpj}<br>{empenho.nome}
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
