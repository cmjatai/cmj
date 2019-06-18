from cmj.crud.base import CrudAux
from cmj.diarios.models import TipoDeDiario


TipoDiarioCrud = CrudAux.build(TipoDeDiario, None, 'tipodiario')
