from django.utils.translation import gettext_lazy as _

from cmj.loa.forms.f_entidade import EntidadeLoaForm
from cmj.loa.models import Entidade
from cmj.loa.models.m_entidade import EntidadeLoa
from cmj.loa.models.m_loa import Loa
from cmj.loa.views.v_mixins import LoaContextDataMixin
from sapl.crud.base import RP_DETAIL, RP_LIST, Crud, MasterDetailCrud


class EntidadeCrud(Crud):
    model = Entidade
    public = [RP_LIST, RP_DETAIL]
    frontend = Entidade._meta.app_label

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ["nome_fantasia", ("cnes", "cpfcnpj"), "ativo"]

    class DetailView(Crud.DetailView):
        layout_key = "EntidadeDetail"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context["subnav_template_name"] = "loa/subnav_entidade.yaml"
            return context

        def hook_metadata__import_fields(self, obj, verbose_name="", field_display=""):

            import_fields = obj.metadata.get("import_fields", {})

            if not import_fields:
                return verbose_name, "Nenhum campo de importação definido."

            lines = []
            for k, v in import_fields.items():
                if v:
                    lines.append(f"<li><strong>{k}:</strong> {v}</li>")

            return (
                _("Dados importados da base do CNES"),
                f'<ul class="monospace">{"".join(lines)}</ul>',
            )

    class ListView(Crud.ListView):
        ordering = ("-ativo", "nome_fantasia")
        paginate_by = 50

        def get_queryset(self):
            qs = super().get_queryset()
            if not self.request.user.is_superuser:
                qs = qs.filter(ativo=True)
            return qs

        def hook_cpfcnpj(self, obj, *args, **kwargs):
            descr = args[0] if args else ""
            if descr.startswith(" / "):
                descr = descr[3:]
                d = descr.replace("0", "")
                if not d:
                    return "", ""
                return f" / CNPJ: {descr}", ""
            return f"CNPJ: {args[0]}", ""

        def hook_cnes(self, obj, *args, **kwargs):
            if not args or not args[0]:
                return "", ""
            return f"CNES: {args[0]}", ""


class EntidadeLoaCrud(MasterDetailCrud):
    model = EntidadeLoa
    parent_field = "loa"
    frontend = EntidadeLoa._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        list_field_names = [
            "entidade",
        ]

    class CreateView(LoaContextDataMixin, MasterDetailCrud.CreateView):
        form_class = EntidadeLoaForm

        def get_success_url(self):
            return self.update_url

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = Loa.objects.get(pk=self.kwargs.get("pk"))
            initial["user"] = self.request.user
            return initial

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        form_class = EntidadeLoaForm

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = self.object.loa
            initial["user"] = self.request.user
            return initial
