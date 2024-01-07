from sapl.crud.base import Crud
from sapl.painelset.models import PainelSET, Tela, ComponenteBase


class PainelSETCrud(Crud):
    model = PainelSET


class ComponenteBaseCrud(Crud):
    model = ComponenteBase


class TelaCrud(Crud):
    model = Tela
