from django.conf.urls import url, include

from cmj.cerimonial.views import StatusVisitaCrud, TipoTelefoneCrud,\
    TipoEnderecoCrud, TipoEmailCrud, ParentescoCrud, EstadoCivilCrud,\
    TipoAutoridadeCrud, TipoLocalTrabalhoCrud, NivelInstrucaoCrud, PessoaCrud,\
    TelefoneCrud, OperadoraTelefoniaCrud, EmailCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [

    url(r'^pessoa/', include(
        PessoaCrud.get_urls() + TelefoneCrud.get_urls() + EmailCrud.get_urls()
    )),

    url(r'^sistema/cerimonial/statusvisita/',
        include(StatusVisitaCrud.get_urls())),
    url(r'^sistema/cerimonial/tipotelefone/',
        include(TipoTelefoneCrud.get_urls())),
    url(r'^sistema/cerimonial/tipoendereco/',
        include(TipoEnderecoCrud.get_urls())),
    url(r'^sistema/cerimonial/tipoemail/',
        include(TipoEmailCrud.get_urls())),
    url(r'^sistema/cerimonial/parentesco/',
        include(ParentescoCrud.get_urls())),
    url(r'^sistema/cerimonial/estadocivil/',
        include(EstadoCivilCrud.get_urls())),
    url(r'^sistema/cerimonial/tipoautoridade/',
        include(TipoAutoridadeCrud.get_urls())),
    url(r'^sistema/cerimonial/tipolocaltrabalho/',
        include(TipoLocalTrabalhoCrud.get_urls())),
    url(r'^sistema/cerimonial/operadoratelefonia/',
        include(OperadoraTelefoniaCrud.get_urls())),
    url(r'^sistema/cerimonial/nivelinstrucao/',
        include(NivelInstrucaoCrud.get_urls())),
]
