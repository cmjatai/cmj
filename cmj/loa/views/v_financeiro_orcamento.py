from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from cmj.loa.forms.f_financeiro_orcamento import (
    AcaoForm,
    DespesaFilterSet,
    DespesaForm,
    FonteForm,
    FuncaoForm,
    NaturezaForm,
    OrgaoForm,
    ProgramaForm,
    SubFuncaoForm,
    UnidadeOrcamentariaForm,
)
from cmj.loa.models import (
    Acao,
    Despesa,
    Fonte,
    Funcao,
    Loa,
    Natureza,
    Orgao,
    Programa,
    SubFuncao,
    UnidadeOrcamentaria,
)
from cmj.loa.views.v_mixins import LoaContextDataMixin
from cmj.utils import decimal2str
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud


class DespesaCrud(MasterDetailCrud):
    model = Despesa
    parent_field = "loa"
    public = [RP_LIST, RP_DETAIL]
    ordered_list = False
    frontend = Loa._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        list_field_names = [
            "dotacao",
            "valor_materia",
        ]

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        form_class = DespesaForm

    class ListView(LoaContextDataMixin, FilterView, MasterDetailCrud.ListView):
        paginate_by = 100
        filterset_class = DespesaFilterSet

        def get(self, request, *args, **kwargs):
            self.loa = Loa.objects.get(pk=self.kwargs["pk"])
            return FilterView.get(self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} despesa-list"
            return context

        def get_queryset(self):
            return Despesa.objects.filter(loa=self.loa).select_related(
                "orgao",
                "unidade",
                "funcao",
                "subfuncao",
                "programa",
                "acao",
                "natureza",
                "fonte",
            )

        def hook_header_dotacao(self, *args, **kwargs):
            return _("Despesas")

        def hook_header_valor_materia(self, *args, **kwargs):
            return _("Valor das Despesas (R$)")

        def hook_dotacao(self, obj, *args, **kwargs):
            dotacao = f"""
                <div class="dotacao courier">
                    <strong>Orgão:</strong> {obj.orgao} -
                    <strong>Unidade:</strong> {obj.unidade}<br>
                    <strong>Função:</strong> {obj.funcao} -
                    <strong>Subfunção:</strong> {obj.subfuncao}<br>
                    <strong>Programa:</strong> {obj.programa} -
                    <strong>Ação:</strong> {obj.acao}<br>
                    <strong>Natureza:</strong> {obj.natureza}<br>
                    <strong>Fonte:</strong> {obj.fonte}
                </div>
                """
            return dotacao, args[1]

        def hook_valor_materia(self, obj, *args, **kwargs):
            return decimal2str(obj.valor_materia), args[1], "text-right"


class OrgaoCrud(MasterDetailCrud):
    model = Orgao
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 100

        def hook_codigo(self, obj, *args, **kwargs):
            return obj.codigo or "sem código", args[1]

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = OrgaoForm


class UnidadeOrcamentariaCrud(MasterDetailCrud):
    model = UnidadeOrcamentaria
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 100
        ordering = [
            "orgao__especificacao",
            "especificacao",
        ]

        def hook_codigo(self, obj, *args, **kwargs):
            return obj.codigo or "sem código", args[1]

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = UnidadeOrcamentariaForm

        def form_valid(self, form):
            try:
                return super().form_valid(form)
            except ValueError as e:
                form.add_error(None, str(e))
                return super().form_invalid(form)


class FuncaoCrud(MasterDetailCrud):
    model = Funcao
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 100

        def hook_codigo(self, obj, *args, **kwargs):
            return obj.codigo or "sem código", args[1]

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = FuncaoForm


class SubFuncaoCrud(MasterDetailCrud):
    model = SubFuncao
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 100

        def hook_codigo(self, obj, *args, **kwargs):
            return obj.codigo or "sem código", args[1]

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = SubFuncaoForm


class ProgramaCrud(MasterDetailCrud):
    model = Programa
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 100

        def hook_codigo(self, obj, *args, **kwargs):
            return obj.codigo or "sem código", args[1]

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = ProgramaForm


class AcaoCrud(MasterDetailCrud):
    model = Acao
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 100

        def hook_codigo(self, obj, *args, **kwargs):
            return obj.codigo or "sem código", args[1]

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = AcaoForm


class NaturezaCrud(MasterDetailCrud):
    model = Natureza
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 100

        def hook_codigo(self, obj, *args, **kwargs):
            return obj.codigo or "sem código", args[1]

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = NaturezaForm


class FonteCrud(MasterDetailCrud):
    model = Fonte
    parent_field = "loa"

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        pass

    class ListView(LoaContextDataMixin, MasterDetailCrud.ListView):
        paginate_by = 100

        def hook_codigo(self, obj, *args, **kwargs):
            return obj.codigo or "sem código", args[1]

    class UpdateView(LoaContextDataMixin, MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = FonteForm
