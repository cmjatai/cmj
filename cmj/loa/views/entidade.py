from django.utils.translation import gettext_lazy as _

from cmj.loa.models import (
    Entidade,
)
from sapl.crud.base import RP_DETAIL, RP_LIST, CrudAux


class EntidadeCrud(CrudAux):
    model = Entidade
    public = [RP_LIST, RP_DETAIL]
    frontend = Entidade._meta.app_label

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ["nome_fantasia", ("cnes", "cpfcnpj"), "ativo"]

    class DetailView(CrudAux.DetailView):
        layout_key = "EntidadeDetail"

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

    class ListView(CrudAux.ListView):
        ordering = ("-ativo", "nome_fantasia")
