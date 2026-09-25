from cmj.loa.models.m_loa import Loa


class LoaContextDataMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = context.get("path", "")
        context["path"] = f"{path} container-loa"

        try:

            if self.model == Loa:
                if (
                    hasattr(self, "object")
                    and self.object
                    and self.object.materia
                    and not self.object.materia.normajuridica()
                ):
                    context["subnav_template_name"] = (
                        "loa/subnav_loa_em_tramitacao.yaml"
                    )
            elif self.crud.parent_field == "loa":
                obj = self.loa if hasattr(self, "loa") and self.loa else self.object

                # Ensure obj is a Loa instance
                if obj and hasattr(obj, "loa"):
                    obj = obj.loa

                if obj and obj.materia and not obj.materia.normajuridica():
                    context["subnav_template_name"] = (
                        "loa/subnav_loa_em_tramitacao.yaml"
                    )
        except Exception as e:
            # Optionally log the exception or handle it as needed
            pass

        return context
