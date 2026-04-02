from decimal import Decimal

from django.urls.base import reverse_lazy
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from cmj.loa.forms import OficioAjusteLoaForm, RegistroAjusteLoaForm
from cmj.loa.models import Loa, OficioAjusteLoa, RegistroAjusteLoa
from cmj.loa.views.mixins import LoaContextDataMixin
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud


class OficioAjusteLoaCrud(MasterDetailCrud):
    model = OficioAjusteLoa
    parent_field = "loa"
    model_set = "registroajusteloa_set"
    public = [RP_LIST, RP_DETAIL]
    frontend = OficioAjusteLoa._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        ordered_list = False
        list_field_names = ["registros"]

    class CreateView(MasterDetailCrud.CreateView):
        form_class = OficioAjusteLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = Loa.objects.get(pk=self.kwargs["pk"])
            return initial

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = OficioAjusteLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = self.object.loa
            return initial

    class ListView(MasterDetailCrud.ListView):
        ordering = "epigrafe"
        paginate_by = 25

        def hook_header_registros(self):
            return "Registros de Ajuste Técnico"

        def hook_registros(self, obj, field_display="", url=""):
            ajustes = []

            url = reverse_lazy("cmj.loa:oficioajusteloa_detail", kwargs={"pk": obj.id})

            epigrafe = (
                f'<h2><a class="text-nowrap" href="{url}">{obj.epigrafe}</a></h2>'
            )
            ajustes.append(epigrafe)

            parlamentares = " - ".join(map(lambda x: str(x), obj.parlamentares.all()))
            ajustes.append(f"<h4><strong>Parlamentares:</strong> {parlamentares}</h4>")

            registros = obj.registroajusteloa_set.all()

            registros_positivos = []
            registros_negativos = []
            registros_zero = []

            for r in registros:
                if r.soma_valor > Decimal("0.00"):
                    registros_positivos.append(r)
                elif r.soma_valor < Decimal("0.00"):
                    registros_negativos.append(r)
                else:
                    registros_zero.append(r)

            registros = (
                list(registros_positivos)
                + list(registros_negativos)
                + list(registros_zero)
            )

            for ajuste in registros:
                url = reverse_lazy(
                    "cmj.loa:registroajusteloa_detail", kwargs={"pk": ajuste.id}
                )

                a_str = f"R$ {ajuste.str_valor}"
                if ajuste.soma_valor < Decimal("0.00"):
                    a_str = f'<span class="text-danger">{a_str}</span>'
                elif ajuste.soma_valor == Decimal("0.00"):
                    a_str = f'<span class="text-danger">R$ 0,00</span>'

                emendas_do_ajuste = ajuste.emendaloa.all()
                emendas_epigrafe = []
                for emenda in emendas_do_ajuste:
                    emendas_epigrafe.append(emenda.materia.epigrafe_short)

                emendas_epigrafe = ", ".join(emendas_epigrafe)
                emenda_epigrafe = f'<strong>Emendas:</strong> {emendas_epigrafe if emendas_epigrafe else "Ajuste sem ligação com emenda impositiva."}<br>'
                unidade_orcamentaria = f'<strong>Unidade Orçamentária:</strong> {ajuste.unidade.especificacao if ajuste.unidade else ""}<br>'

                entidade = (
                    f"<strong>Entidade:</strong> {ajuste.entidade.nome_fantasia}<br>"
                    if ajuste.entidade
                    else ""
                )

                a_str = f"""
                    <tr>
                        <td align="right">
                            <a href="{url}">
                                <strong style="white-space: nowrap">
                                    {a_str}
                                </strong>
                            </a>
                        </td>
                        <td>
                          {unidade_orcamentaria}
                            {entidade}
                          {emenda_epigrafe}
                          <small>
                            <em>{ajuste.descricao}</em>
                          </small>
                        </td>
                    </tr>
                """

                ajustes.append(a_str)

            return f'<table class="w-100">{"".join(ajustes)}</table>', ""

    class DetailView(MasterDetailCrud.DetailView):
        template_name = "loa/oficioajusteloa_detail.html"
        paginate_by = 100

        @property
        def list_field_names_set(self):
            return "descricao", "str_valor", "tipo"  # , 'emendaloa'

        def hook_header_str_valor(self):
            return "Valor (R$)"

        def hook_str_valor(self, obj, verbose_name="", field_display=""):
            return verbose_name, f'{field_display if field_display != "0" else "0,00"}'

        def hook_descricao(self, obj, verbose_name="", field_display=""):

            emenda_epigrafe = (
                obj.emendaloa.materia.epigrafe_short if obj.emendaloa else ""
            )
            emenda_epigrafe = f'<strong>Emenda:</strong> {emenda_epigrafe if emenda_epigrafe else "Ajuste sem ligação com emenda impositiva."}<br>'
            unidade_orcamentaria = f'<strong>Unidade Orçamentária:</strong> {obj.unidade.especificacao if obj.unidade else ""}<br>'

            return (
                verbose_name,
                f"{emenda_epigrafe}{unidade_orcamentaria}<em>{field_display}</em>",
            )

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} oficioajusteloa-detail"
            return context


class RegistroAjusteLoaCrud(MasterDetailCrud):
    model = RegistroAjusteLoa
    parent_field = "oficio_ajuste_loa__loa"
    public = [RP_LIST, RP_DETAIL]
    frontend = RegistroAjusteLoa._meta.app_label

    class DetailView(MasterDetailCrud.DetailView):

        layout_key = "RegistroAjusteLoaDetail"

        @property
        def detail_list_url(self):
            return reverse_lazy(
                "cmj.loa:oficioajusteloa_detail",
                kwargs={"pk": self.object.oficio_ajuste_loa_id},
            )

        def hook_emendaloa(self, obj, verbose_name="", field_display=""):
            if not obj.emendaloa.exists():
                return "", ""

            displays = []
            for emenda in obj.emendaloa.all():
                url = reverse_lazy("cmj.loa:emendaloa_detail", kwargs={"pk": emenda.id})
                displays.append(
                    f'<li><a href="{url}">{emenda.materia.epigrafe_short} - {emenda.indicacao}<br>{emenda.finalidade_format}</a></li>'
                )

            field_display = "<ul>" + "".join(displays) + "</ul>"
            return verbose_name, field_display

        def hook_oficio_ajuste_loa(self, obj, verbose_name="", field_display=""):
            url = reverse_lazy(
                "cmj.loa:oficioajusteloa_detail",
                kwargs={"pk": obj.oficio_ajuste_loa.id},
            )
            field_display = f'<a href="{url}">{obj.oficio_ajuste_loa.epigrafe}</a>'
            return verbose_name, field_display

        def hook_prestacaocontaregistro_set(
            self, obj, verbose_name="", field_display=""
        ):
            pcs = []

            for pc in obj.prestacaocontaregistro_set.all():
                pc_url = reverse_lazy(
                    "cmj.loa:prestacaocontaregistro_detail", kwargs={"pk": pc.id}
                )
                pcs.append(
                    f"""<li>
                        <span class="badge badge-secondary p-2">{formats.date_format(pc.prestacao_conta.data_envio, "SHORT_DATE_FORMAT")}</span>
                        <span class="badge badge-secondary p-2">{pc.situacao}</span>
                        <a href="{ pc_url}" class="d-inline-block p-2 font-weight-bold">
                        {pc.prestacao_conta}
                        </a>
                        <span class="text-gray d-block">{pc.detalhamento}</span>
                    </li>"""
                )

            return (
                verbose_name,
                f"""
                <ul>
                    {"".join(pcs)}
                </ul>
                """,
            )

        def hook_empenhoemendaajuste_set(
            self, ajuste, verbose_name="", field_display=""
        ):
            empenhos = []
            for eea in ajuste.empenhoemendaajuste_set.all():
                empenho = eea.empenho
                url = reverse_lazy("cmj.loa:empenho_detail", kwargs={"pk": empenho.id})
                empenhos.append(
                    f"""
                    <li>
                        <a href="{url}">
                            {empenho.codigo}</a> |
                            Data: {formats.date_format(empenho.data, "SHORT_DATE_FORMAT")} |
                            Valor Empenhado: R$ {empenho.str_valor_empenhado} | {empenho.nome}
                    </li>"""
                )
            return (
                "Empenhos do Registro de Ajuste",
                f'<ul class="small courier">{"".join(empenhos)}</ul>',
            )

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = RegistroAjusteLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial["oficioajusteloa"] = self.object.oficio_ajuste_loa
            return initial

        @property
        def cancel_url(self):
            return reverse_lazy(
                "cmj.loa:oficioajusteloa_detail",
                kwargs={"pk": self.object.oficio_ajuste_loa.id},
            )

    class CreateView(MasterDetailCrud.CreateView):
        form_class = RegistroAjusteLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial["oficioajusteloa"] = OficioAjusteLoa.objects.get(
                pk=self.kwargs["pk"]
            )
            return initial

        @property
        def cancel_url(self):
            return reverse_lazy(
                "cmj.loa:oficioajusteloa_detail", kwargs={"pk": self.kwargs["pk"]}
            )

        def get_success_url(self):
            return reverse_lazy(
                "cmj.loa:oficioajusteloa_detail", kwargs={"pk": self.kwargs["pk"]}
            )

    class DeleteView(MasterDetailCrud.DeleteView):

        def get_success_url(self):
            return reverse_lazy(
                "cmj.loa:oficioajusteloa_detail",
                kwargs={"pk": self.object.oficio_ajuste_loa.id},
            )
