"""Corpos JSON padrão das respostas de erro do v8.

O cliente HTTP do frontend converte estes corpos em ``HttpError``. Os códigos
de status ficam com as views.
"""

from django.forms.forms import NON_FIELD_ERRORS


def _corpo_validacao(campos, gerais):
    return {
        "detail": "Corrija os campos indicados.",
        "errors": campos,
        "non_field_errors": gerais,
    }


def erro_validacao(form):
    """Corpo do erro de validação (status 400) a partir de um formulário Django."""
    campos = {
        campo: [str(mensagem) for mensagem in mensagens]
        for campo, mensagens in form.errors.items()
        if campo != NON_FIELD_ERRORS
    }
    gerais = [str(mensagem) for mensagem in form.non_field_errors()]
    return _corpo_validacao(campos, gerais)


def erro_corpo_invalido():
    """Corpo do erro (status 400) para requisição cujo corpo não é um objeto JSON."""
    return _corpo_validacao({}, ["O corpo da requisição não é um objeto JSON válido."])


def nao_autenticado():
    """Corpo da resposta 401."""
    return {"detail": "Autenticação necessária.", "code": "nao_autenticado"}


def sem_permissao():
    """Corpo da resposta 403."""
    return {
        "detail": "Você não tem permissão para acessar este recurso.",
        "code": "sem_permissao",
    }


def nao_encontrado():
    """Corpo da resposta 404."""
    return {"detail": "Não encontrado."}
