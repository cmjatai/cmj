from cmj.loa.models.m_loa import Loa


class LoaContextDataMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = context.get("path", "")
        context["path"] = f"{path} container-loa"

        if not hasattr(self, "loa"):
            self.loa = None
        if not hasattr(self, "object"):
            self.object = None

        if not self.loa and not self.object:
            try:
                loa = Loa.objects.get(pk=self.kwargs.get("pk", 0))
                self.loa = loa
            except Loa.DoesNotExist:
                pass

        if self.loa and self.loa.materia and not self.loa.materia.normajuridica():
            context["subnav_template_name"] = "loa/subnav_loa_em_tramitacao.yaml"
        elif (
            self.object
            and hasattr(self.object, "loa")
            and self.object.loa.materia
            and not self.object.loa.materia.normajuridica()
        ):
            context["subnav_template_name"] = "loa/subnav_loa_em_tramitacao.yaml"
        elif (
            self.object
            and hasattr(self.object, "materia")
            and self.object.materia
            and not self.object.materia.normajuridica()
        ):
            context["subnav_template_name"] = "loa/subnav_loa_em_tramitacao.yaml"

        return context
