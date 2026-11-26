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
    # LOA-EMD-080: depois da fase 12, o autor só altera a finalidade, além dos
    # valores por parlamentar e assinantes (validar_parlamentares)
    CAMPOS_AUTOR_APOS_LIBERACAO = frozenset({"finalidade"})

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

        if self.e_autor_da_emenda(user, emenda):  # autor (LOA-EMD-076)
            if emenda.fase <= EmendaLoa.PROPOSTA_LIBERADA:
                campos |= self.CAMPOS_BASE | self.CAMPOS_ESTRUTURAIS
            else:
                campos |= self.CAMPOS_AUTOR_APOS_LIBERACAO
            if tipo == EmendaLoa.MODIFICATIVA:
                # o fqormulário exige o Valor Global da modificativa (LOA-EMD-022)
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

    # ------------------------------------------------- autoria e parlamentares

    @staticmethod
    def autor_do_usuario(user):
        """Autor de que ``user`` é operador, ou None."""
        if not user or user.is_anonymous:
            return None
        operador = user.operadorautor_set.first()
        return operador.autor if operador else None

    def autor_da_emenda(self, emenda):
        """Autor do operador dono (``owner``) da emenda, ou None."""
        return self.autor_do_usuario(emenda.owner) if emenda.owner_id else None

    def e_autor_da_emenda(self, user, emenda):
        """``user`` opera o mesmo autor do dono da emenda (LOA-EMD-076).

        Operadores de outros parlamentares participantes (coautores) não contam. Dono
        sem autor não tem operador de autor que o represente.
        """
        autor = self.autor_da_emenda(emenda)
        return autor is not None and autor == self.autor_do_usuario(user)

    def pode_editar(self, user, emenda):
        """Permissão de edição da emenda pela API (LOA-EMD-005, LOA-EMD-076, LOA-EMD-085).

        Com ``change_emendaloa``, edita sempre. Sem ela, exige emenda sem matéria e,
        além disso, ``emendaloa_full_editor`` ou ser o autor do dono com a emenda até
        a fase 12 ou na fase 17.
        """
        from cmj.loa.models import EmendaLoa

        if not user or user.is_anonymous:
            return False
        if user.has_perm("loa.change_emendaloa"):
            return True
        if emenda.materia_id:
            return False
        if user.has_perm("loa.emendaloa_full_editor"):
            return True
        fase = (
            emenda.fase <= EmendaLoa.PROPOSTA_LIBERADA
            or emenda.fase == EmendaLoa.LIBERACAO_CONTABIL
        )
        return fase and self.e_autor_da_emenda(user, emenda)

    def ve_campos_internos(self, user, emenda):
        """Vê ``owner``, ``metadata`` e ``search`` da emenda na API (LOA-LST-091).

        Quem pode editar a emenda em alguma fase: ``change_emendaloa``,
        ``emendaloa_full_editor`` ou o autor do dono. Não depende da fase atual,
        para que a tela de edição continue lendo ``metadata.style``.
        """
        if not user or user.is_anonymous:
            return False
        if user.has_perm("loa.change_emendaloa") or user.has_perm(
            "loa.emendaloa_full_editor"
        ):
            return True
        return self.e_autor_da_emenda(user, emenda)

    def pode_ver_campos_internos(self, user):
        """Pode ver ``owner``, ``metadata`` e ``search`` de alguma emenda (LOA-LST-091).

        Quem tem uma das permissões de edição ou opera algum autor. Quem não passa
        aqui não vê esses campos em emenda nenhuma.
        """
        if not user or user.is_anonymous:
            return False
        if user.has_perm("loa.change_emendaloa") or user.has_perm(
            "loa.emendaloa_full_editor"
        ):
            return True
        return self.autor_do_usuario(user) is not None

    def parlamentar_protegido(self, emenda, user=None):
        """Parlamentar cujo valor não pode ser zerado nem desmarcado (LOA-EMD-079).

        É o parlamentar do autor do dono. Na criação, sem dono gravado, vale o de
        ``user``.
        """
        from sapl.parlamentares.models import Parlamentar

        autor = (
            self.autor_da_emenda(emenda) if emenda.pk else self.autor_do_usuario(user)
        )
        related = autor.autor_related if autor else None
        return related if isinstance(related, Parlamentar) else None

    def pode_alterar_parlamentares(self, user, emenda):
        """Autor do dono, Operador da LOA e superusuário (LOA-EMD-077)."""
        return user.has_perm("loa.add_emendaloa") or self.e_autor_da_emenda(
            user, emenda
        )

    def validar_parlamentares(self, user, emenda, valores):
        """Valida a alteração de valores por parlamentar ou de assinantes.

        ``valores`` mapeia parlamentar (instância ou id) para o valor resultante;
        valor vazio ou não positivo significa retirar o parlamentar da emenda.
        Levanta ``ValidationError`` (LOA-EMD-077 a 079).
        """
        if emenda.pk and not self.pode_alterar_parlamentares(user, emenda):
            raise ValidationError(
                "Você não tem permissão para alterar os parlamentares desta Emenda."
            )

        ids_da_loa = set(emenda.loa.parlamentares.values_list("id", flat=True))
        ids = {getattr(p, "pk", p) for p in valores}
        try:
            ids = {int(i) for i in ids}
        except (TypeError, ValueError):
            raise ValidationError("Parlamentar inválido.")
        if ids - ids_da_loa:
            raise ValidationError("O Parlamentar informado não pertence a esta LOA.")

        protegido = self.parlamentar_protegido(emenda, user)
        if protegido is None:
            return
        for p, valor in valores.items():
            if int(getattr(p, "pk", p)) == protegido.pk and not (valor and valor > 0):
                raise ValidationError(
                    f"O Parlamentar {protegido} é o autor desta Emenda e não pode "
                    "ser retirado nem ter o valor zerado."
                )

    # --------------------------------------------------------- emenda coletiva

    @staticmethod
    def e_coletiva(emenda):
        """Emenda coletiva: gerada por um agrupamento (LOA-AGR-071)."""
        return emenda.agrupamento_de_origem_id is not None

    def validar_fase_da_coletiva(self, emenda, destino):
        """A coletiva não volta para a fase 10 (LOA-FASE-072).

        Ela não tem autor para corrigi-la (LOA-FASE-071). Vale para todo perfil e
        para todo caminho: botão "Devolver para correção", PATCH e formulário.
        Levanta ``ValidationError``.
        """
        from cmj.loa.models import EmendaLoa

        if int(destino) != EmendaLoa.PROPOSTA or not self.e_coletiva(emenda):
            return
        if emenda.fase == EmendaLoa.PROPOSTA:
            return  # já está na 10: não é uma mudança de fase
        raise ValidationError(
            "A Emenda Coletiva não pode ser devolvida para correção: ela não tem "
            "autor para corrigi-la. Corrija-a na edição contábil ou cancele as "
            "Emendas Coletivas do agrupamento e devolva as emendas de origem."
        )

    # --------------------------------------------------------------- proposição

    def vira_proposicao(self, emenda):
        """A emenda pode ser registrada como Proposição Legislativa (LOA-FASE-070).

        Só a emenda cujo dono opera um autor: a proposição é desse autor. A de dono
        sem autor, como a coletiva sob o Operador da LOA, segue para a matéria sem
        proposição.
        """
        return self.autor_da_emenda(emenda) is not None

    # ------------------------------------------------------------------ criação

    @staticmethod
    def pode_criar(user):
        """Cria emenda quem tem ``add_emendaloa`` ou é operador de autor (LOA-EMD-082).

        A publicação da LOA não importa. A fase inicial segue LOA-FASE-051.
        """
        if not user or user.is_anonymous:
            return False
        return user.has_perm("loa.add_emendaloa") or user.operadorautor_set.exists()

    # ---------------------------------------------------------------- consulta

    @staticmethod
    def loas_visiveis(user, queryset=None):
        """LOAs que o usuário pode consultar (LOA-LST-003 e LOA-LST-006).

        É a regra da lista de LOAs: anônimo e conta comum só veem LOA
        publicada; operador de autor vê também a não publicada cuja matéria ainda
        não virou norma; quem tem ``loa.emendaloa_full_editor`` vê todas.
        """
        from django.db.models import Q

        from cmj.loa.models import Loa

        if queryset is None:
            queryset = Loa.objects.all()
        if user and not user.is_anonymous:
            if user.has_perm("loa.emendaloa_full_editor"):
                return queryset
            if user.operadorautor_set.exists():
                return queryset.filter(
                    Q(publicado=True) | Q(materia__normajuridica__isnull=True)
                ).distinct()
        return queryset.filter(publicado=True)

    @staticmethod
    def visiveis(user, queryset):
        """Emendas que o usuário pode consultar (LOA-LST-005 e LOA-LST-006): as
        das LOAs de ``loas_visiveis``."""
        if (
            user
            and not user.is_anonymous
            and user.has_perm("loa.emendaloa_full_editor")
        ):
            return queryset
        loas = EmendaLoaService.loas_visiveis(user)
        return queryset.filter(loa__in=loas.values("id"))

    # ---------------------------------------------------------------- documento

    @staticmethod
    def nome_documento(emenda, sufixo="", ext="pdf"):
        """Nome do arquivo do documento da emenda."""
        from django.utils.text import slugify

        if emenda.emendaloaparlamentar_set.count() > 1:
            nome_autor = "coletiva"
        else:
            operador = emenda.owner.operadorautor_set.first() if emenda.owner else None
            nome_autor = operador.autor.nome if operador else ""

        return "{}-{}-{:04d}-{}{}.{}".format(
            emenda.loa.ano,
            slugify(nome_autor),
            emenda.id,
            slugify(emenda.get_tipo_display()),
            sufixo,
            ext,
        )

    def documento_pdf(self, emenda, base_url):
        """PDF da emenda, o mesmo da action ``view`` da API (LOA-LST-019).

        Usa o estilo já presente em ``emenda.metadata`` e não grava nada.
        ``base_url`` resolve os endereços relativos do HTML: quem chama decide
        a origem, sem depender do ``Host`` da requisição.
        """
        from django.conf import settings
        from django.template.loader import render_to_string

        from cmj.utils.utils_report import make_pdf

        estilo = emenda.metadata.get("style") or {}
        context = {
            # O template numera artigos e parágrafos com view.art e view.paragrafo
            "view": _NumeracaoDispositivos(),
            "object": emenda,
            "lineHeight": str(estilo.get("lineHeight", 150) / 100.0),
            "base_url": settings.BASE_URL if not settings.DEBUG else "",
            "espacoAssinatura": str(estilo.get("espacoAssinatura", "") or ""),
        }
        template = render_to_string("loa/pdf/emendaloa_preview.html", context)
        return make_pdf(base_url=base_url, main_template=template)


class _NumeracaoDispositivos:
    """Contadores de artigo e parágrafo, novos a cada documento."""

    def __init__(self):
        self._art = 0
        self._paragrafo = 0

    @property
    def art(self):
        self._art += 1
        return self._art

    @property
    def paragrafo(self):
        self._paragrafo += 1
        return self._paragrafo
