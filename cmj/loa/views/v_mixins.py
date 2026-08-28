class LoaContextDataMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = context.get("path", "")
        context["path"] = f"{path} container-loa"

        if (
            hasattr(self, "loa")
            and self.loa.materia
            and not self.loa.materia.normajuridica()
        ):
            context["subnav_template_name"] = "loa/subnav_loa_em_tramitacao.yaml"
        elif (
            hasattr(self, "object")
            and self.object
            and hasattr(self.object, "loa")
            and self.object.loa.materia
            and not self.object.loa.materia.normajuridica()
        ):
            context["subnav_template_name"] = "loa/subnav_loa_em_tramitacao.yaml"
        elif (
            hasattr(self, "object")
            and self.object
            and hasattr(self.object, "materia")
            and self.object.materia
            and not self.object.materia.normajuridica()
        ):
            context["subnav_template_name"] = "loa/subnav_loa_em_tramitacao.yaml"

        return context
