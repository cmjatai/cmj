from django.core.exceptions import ValidationError


class EmendaLoaService:
    """Regras de negócio da Emenda Impositiva (docs/specs/loa/edicao-emenda.md)."""

    _instance = None

    # LOA-EMD-070: campos do model que a edição pode alterar, por perfil
    CAMPOS_BASE = frozenset(
        {
            "permite_juncao_coletiva",
            "prefixo_indicacao",
            "prefixo_finalidade",
            "finalidade",
            "bairro",
        }
    )
    CAMPOS_ESTRUTURAIS = frozenset({"tipo", "fase", "unidade", "entidade"})
    CAMPOS_OPERADOR = frozenset({"valor", "materia"})

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmendaLoaService, cls).__new__(cls)
        return cls._instance

    def campos_alteraveis(self, user, emenda, tipo=None):
        """Campos que ``user`` pode alterar em ``emenda`` (LOA-EMD-070 e 071).

        ``tipo`` é o tipo resultante da alteração; sem ele, vale o tipo gravado.
        Quem tem mais de um perfil soma as listas.
        """
        from cmj.loa.models import EmendaLoa

        tipo = emenda.tipo if tipo is None else int(tipo)
        campos = set()

        if user.has_perm("loa.add_emendaloa"):  # Operador da LOA e superusuário
            campos |= self.CAMPOS_BASE | self.CAMPOS_ESTRUTURAIS | self.CAMPOS_OPERADOR

        if user.has_perm("loa.emendaloa_full_editor"):  # editor contábil
            campos |= self.CAMPOS_BASE | self.CAMPOS_ESTRUTURAIS

        if user.operadorautor_set.exists():  # autor
            campos |= self.CAMPOS_BASE
            if emenda.fase <= EmendaLoa.PROPOSTA_LIBERADA:
                campos |= self.CAMPOS_ESTRUTURAIS
            if tipo == EmendaLoa.MODIFICATIVA:
                # o formulário exige o Valor Global da modificativa (LOA-EMD-022)
                campos.add("valor")

        return campos

    def campos_alterados(self, emenda, dados):
        """Campos do model cujo valor em ``dados`` difere do gravado (LOA-EMD-072).

        Chaves que não são campos do model são ignoradas (LOA-EMD-073).
        """
        campos_do_model = {f.name: f for f in emenda._meta.concrete_fields}

        alterados = set()
        for nome, valor in dados.items():
            field = campos_do_model.get(nome)
            if field is None:
                continue

            if field.is_relation:
                novo = getattr(valor, "pk", valor)
                novo = (
                    None if novo in ("", None) else field.target_field.to_python(novo)
                )
                atual = getattr(emenda, field.attname)
            else:
                novo = field.to_python(valor)
                atual = getattr(emenda, field.attname)

            if novo != atual:
                alterados.add(nome)

        return alterados

    def validar_alteracao(self, user, emenda, dados):
        """Recusa a alteração de campos que ``user`` não pode alterar (LOA-EMD-070 a 073).

        Levanta ``ValidationError`` citando os campos recusados.
        """
        from cmj.loa.models import EmendaLoa

        alterados = self.campos_alterados(emenda, dados)
        if not alterados:
            return

        tipo = dados.get("tipo", emenda.tipo)
        tipo = emenda.tipo if tipo in ("", None) else tipo
        negados = alterados - self.campos_alteraveis(user, emenda, tipo=tipo)
        if not negados:
            return

        nomes = sorted(
            str(EmendaLoa._meta.get_field(nome).verbose_name) for nome in negados
        )
        raise ValidationError(
            f'Você não tem permissão para alterar nesta Emenda: {", ".join(nomes)}.'
        )
