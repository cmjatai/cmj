
from cmj.core.views_estatisticas import get_redessociais
from sapl.relatorios.view_reports.mixins import RelatorioMixin
from django.views.generic import TemplateView
import markdown as md

markstyles = '''<style>
.container-show{
    font-size: 18pt;
    padding-bottom: 4em;
    text-align: left;
    h1 {
        color: red;
    }
    h2 {
        margin-top: 1em;
    }
    p {
        text-indent: 1cm;
        margin: 5px 0;
        color: #045;
    }
    ul {
        margin: 1rem 0 0 0;
        ul {
            margin: 0;
        }
    }
    li {
        color: #045;
        p {
            margin: 0;
            text-indent: 0cm;
        }
        li {
            font-style: italic;
            color: #049;
        }
    }
}
</style>
'''
class View(RelatorioMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['numeros'] = self.get_numeros()
        return context

    def get_numeros(self):

        mark = []

        mark.append(get_redessociais())
        html = []
        for mt in mark:
            cols = []
            for m in mt:
                sm = ''
                if isinstance(m, tuple):
                    m, sm = m
                    sm = f'-{sm}'
                m = md.markdown(m)
                cols.append(f'<div class="col-md{sm}">{m}</div>')
            row = f'<div class="row page-break">{"".join(cols)}</div>'
            html.append(row)

        mdr = [f'{markstyles}<div class="container container-bi container-show">{h}</div>' for h in html]

        return ''.join(mdr)