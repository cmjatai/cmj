from django.urls.base import reverse_lazy
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from cmj.loa.forms.f_prestacaoconta import (
    PrestacaoContaLoaForm,
    PrestacaoContaRegistroForm,
)
from cmj.loa.models import PrestacaoContaLoa, PrestacaoContaRegistro
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud


class PrestacaoContaRegistroCrud(MasterDetailCrud):
    model = PrestacaoContaRegistro
    parent_field = "prestacao_conta__loa"
    public = [RP_LIST, RP_DETAIL]
    frontend = PrestacaoContaRegistro._meta.app_label
    link_return_to_parent_field = True
    ListView = None  # Disable ListView

    class BaseMixin(MasterDetailCrud.BaseMixin):

        @property
        def cancel_url(self):
            if self.object:
                return self.detail_url
            return reverse_lazy(
                "cmj.loa:prestacaocontaloa_detail", kwargs={"pk": self.kwargs["pk"]}
            )

    class CreateView(MasterDetailCrud.CreateView):
        form_class = PrestacaoContaRegistroForm

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = PrestacaoContaLoa.objects.get(pk=self.kwargs["pk"]).loa
            return initial

        def get_success_url(self):
            return reverse_lazy(
                "cmj.loa:prestacaocontaregistro_detail", kwargs={"pk": self.object.id}
            )

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = PrestacaoContaRegistroForm
        layout_key = "PrestacaoContaRegistroUpdate"

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = self.object.prestacao_conta.loa
            return initial

        def get_success_url(self):
            return reverse_lazy(
                "cmj.loa:prestacaocontaregistro_detail", kwargs={"pk": self.object.id}
            )

    class DetailView(MasterDetailCrud.DetailView):
        layout_key = "PrestacaoContaRegistroDetail"

        # def hook_registro_ajuste__descricao(self, obj, verbose_name='', field_display=''):
        #    if not obj.registro_ajuste:
        #        return '', ''
        #    field_display = f'R$ {obj.registro_ajuste.str_valor} - {obj.registro_ajuste.descricao}'
        #    return 'Descrição do Registro de Ajuste', field_display

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} prestacaocontaregistro-detail"

            title = f"""{self.object.prestacao_conta}<br><small>({self.object.prestacao_conta.loa})</small>"""
            context["title"] = title.replace("\n", "")
            return context

        def hook_registro_ajuste(self, obj, verbose_name="", field_display=""):
            if not obj.registro_ajuste:
                return "", ""
            url = reverse_lazy(
                "cmj.loa:registroajusteloa_detail",
                kwargs={"pk": obj.registro_ajuste.id},
            )
            field_display = f"{obj.registro_ajuste.oficio_ajuste_loa.epigrafe} - R$ {obj.registro_ajuste.str_valor}"
            field_display = (
                f'<a href="{url}">{field_display}</a> - {obj.registro_ajuste.descricao}'
            )
            return "Registro de Ajuste Técnico Vinculado", field_display

        def hook_prestacao_conta_data_envio(
            self, obj, verbose_name="", field_display=""
        ):
            url = reverse_lazy(
                "cmj.loa:prestacaocontaloa_detail",
                kwargs={"pk": obj.prestacao_conta.id},
            )
            field_display = f"""<a href="{url}">
            {obj.prestacao_conta.data_envio}
            </a>"""
            return "Data de Envio da Prestação de Contas", field_display

        def hook_prestacao_conta(self, obj, verbose_name="", field_display=""):
            data_envio = formats.date_format(
                obj.prestacao_conta.data_envio, "SHORT_DATE_FORMAT"
            )
            url = reverse_lazy(
                "cmj.loa:prestacaocontaloa_detail",
                kwargs={"pk": obj.prestacao_conta.id},
            )
            field_display = f"""<a href="{url}">
            {data_envio} - {obj.prestacao_conta}
            </a>"""
            return "Este Registro Pertence à Prestação de Contas", field_display

        def hook_arquivoprestacaocontaregistro_set(
            self, obj, verbose_name="", field_display=""
        ):
            arquivos = []

            qs_arquivos = obj.arquivoprestacaocontaregistro_set.order_by("-id")
            for arquivo in qs_arquivos:
                arq_template = f"""
                    <a class="d-flex align-items-center" href="{arquivo.arquivo.url}">
                        <i class="fa-solid fa-file-pdf fa-2x "></i>
                        <span class="pb-3">{arquivo.descricao}</span>
                    </a>
                """
                arquivos.append(f"<tr><td>{arq_template}</td></tr>")

            return (
                "Arquivos deste Registro de Prestação de Contas",
                f"""
                <div class="container-table m-0 mx-n3">
                    <table class="table table-form table-bordered table-hover w-100">
                        {"".join(arquivos)}
                    </table>
                </div>
                """,
            )

    class DeleteView(MasterDetailCrud.DeleteView):

        def get_success_url(self):
            if self.object.registro_ajuste:
                return reverse_lazy(
                    "cmj.loa:registroajusteloa_detail",
                    kwargs={"pk": self.object.registro_ajuste.id},
                )
            elif self.object.emendaloa:
                return reverse_lazy(
                    "cmj.loa:emendaloa_detail", kwargs={"pk": self.object.emendaloa.id}
                )
            else:
                return reverse_lazy(
                    "cmj.loa:prestacaocontaloa_detail",
                    kwargs={"pk": self.object.prestacao_conta.id},
                )


class PrestacaoContaLoaCrud(MasterDetailCrud):
    model = PrestacaoContaLoa
    parent_field = "loa"
    model_set = "prestacaocontaregistro_set"
    public = [RP_LIST, RP_DETAIL]
    frontend = PrestacaoContaLoa._meta.app_label

    class ListView(MasterDetailCrud.ListView):
        ordering = "-data_envio"
        paginate_by = 25

        def get(self, request, *args, **kwargs):
            if not request.user.has_perm("cmj.loa.add_prestacaocontaloa"):
                self.template_name = "loa/prestacaocontaloa_list_public.html"
            return super().get(request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} prestacaocontaloa-list"
            return context

    class CreateView(MasterDetailCrud.CreateView):
        def get_success_url(self):
            return self.update_url

    class UpdateView(MasterDetailCrud.UpdateView):
        layout_key = "PrestacaoContaLoaUpdate"
        form_class = PrestacaoContaLoaForm

    class DetailView(MasterDetailCrud.DetailView):
        layout_key = "PrestacaoContaLoaDetail"
        template_name = "loa/prestacaocontaloa_detail.html"
        paginate_by = 100

        @property
        def list_field_names_set(self):
            return (
                "emendaloa_registro_ajuste",
                "descricao",
                "situacao",
                "detalhamento",
            )  #

        def get_queryset(self):
            qs = (
                super()
                .get_queryset()
                .order_by(
                    "situacao",
                    "emendaloa__materia__numero",
                    "registro_ajuste__oficio_ajuste_loa__epigrafe",
                )
            )
            return qs

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} prestacaocontaloa-detail"
            title = f"""{self.object}<br><small>({self.object.loa})</small>"""
            context["title"] = title.replace("\n", "")
            return context

        def hook_header_descricao(self):
            return "Itens da Prestação de Contas"

        def hook_descricao(self, obj, verbose_name="", field_display=""):
            descricao = []
            if obj.emendaloa:
                descricao.append(f"{obj.emendaloa}")
            if obj.registro_ajuste:
                descricao.append(
                    f"R$ {obj.registro_ajuste.str_valor} - {obj.registro_ajuste.descricao}"
                )
            # add link para descrição
            url = reverse_lazy(
                "cmj.loa:prestacaocontaregistro_detail", kwargs={"pk": obj.id}
            )
            return verbose_name, f'<a href="{url}">{"<br>".join(descricao)}</a>'

        def hook_header_emendaloa_registro_ajuste(self):
            return "Emenda Impositiva / Registro de Ajuste Técnico"

        def hook_emendaloa_registro_ajuste(
            self, obj, verbose_name="", field_display=""
        ):
            links = []

            if obj.emendaloa:
                url_emenda = reverse_lazy(
                    "cmj.loa:emendaloa_detail", kwargs={"pk": obj.emendaloa.id}
                )
                links.append(f"""
                    <a href="{url_emenda}">
                        {obj.emendaloa.materia.epigrafe_short}
                    </a>
                """)

            if obj.registro_ajuste:
                url_ajuste = reverse_lazy(
                    "cmj.loa:registroajusteloa_detail",
                    kwargs={"pk": obj.registro_ajuste.id},
                )
                links.append(f"""
                    <a href="{url_ajuste}">
                        {obj.registro_ajuste.oficio_ajuste_loa.epigrafe}
                    </a>
                """)

            return verbose_name, "<br>".join(links)

        def hook_arquivoprestacaocontaloa_set(
            self, obj, verbose_name="", field_display=""
        ):
            arquivos = []

            qs_arquivos = obj.arquivoprestacaocontaloa_set.order_by("-id")
            for arquivo in qs_arquivos:
                arq_template = f"""
                    <a class="d-flex align-items-center" href="{arquivo.arquivo.url}">
                        <i class="fa-solid fa-file-pdf fa-2x "></i>
                        <span class="p-2">{arquivo.descricao}</span>
                    </a>
                """
                arquivos.append(f"<tr><td>{arq_template}</td></tr>")

            return (
                "Arquivos da Prestação de Contas",
                f"""
                <div class="container-table m-0 mx-n3">
                    <table class="table table-form table-bordered table-hover w-100">
                        {"".join(arquivos)}
                    </table>
                </div>
                """,
            )
