from django.http.response import HttpResponse
from django.views.generic.base import TemplateView
from sapl.crud.base import Crud

from cmj.core.models import Cep, TipoLogradouro, Logradouro, RegiaoMunicipal,\
    Distrito, Bairro, Trecho


CepCrud = Crud.build(Cep, 'cep')
RegiaoMunicipalCrud = Crud.build(RegiaoMunicipal, 'regiao_municipal')
DistritoCrud = Crud.build(Distrito, 'distrito')
BairroCrud = Crud.build(Bairro, 'bairro')
TipoLogradouroCrud = Crud.build(TipoLogradouro, 'tipo_logradouro')
LogradouroCrud = Crud.build(Logradouro, 'logradouro')
TrechoCrud = Crud.build(Trecho, 'trecho')


class ImportCepView(TemplateView):

    def get(self, request, *args, **kwargs):
        # arquivo de origem: http://www.republicavirtual.com.br/cep/

        import yaml

        ceps = yaml.load(open('/home/leandro/Downloads/go.yml', 'r'))

        # return HttpResponse(data[:-1000])
        return HttpResponse('%s' % (len(ceps)))
        return TemplateView.get(self, request, *args, **kwargs)
