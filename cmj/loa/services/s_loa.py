from decimal import ROUND_DOWN, Decimal

from django.db.models import Exists, OuterRef, Q
from django.db.models.aggregates import Sum

from cmj.utils import quantize
from sapl.parlamentares.models import Legislatura, Mandato


class LoaService:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LoaService, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def _legislatura_do_ano(ano):
        return Legislatura.objects.filter(
            data_inicio__year__lte=ano, data_fim__year__gte=ano
        ).first()

    @staticmethod
    def _com_mandato_na(legislatura):
        if not legislatura:
            return set()
        return set(
            Mandato.objects.filter(legislatura=legislatura).values_list(
                "parlamentar_id", flat=True
            )
        )

    def legislatura_do_projeto(self, loa):
        """LOA-CRUD-069: a legislatura que elaborou o projeto da LOA, a do ano
        anterior ao da LOA. Só difere da legislatura do ano da LOA na LOA do
        primeiro ano de uma legislatura."""
        return self._legislatura_do_ano(loa.ano - 1) or self._legislatura_do_ano(
            loa.ano
        )

    def legislatura_de_referencia(self, loa):
        """LOA-CRUD-067: a legislatura cujos mandatos valem para a LOA. É a que
        contém o ano da LOA. A exceção é a LOA do primeiro ano de uma
        legislatura enquanto a RCL definitiva não é lançada: até lá valem os
        parlamentares originais, os da legislatura do projeto."""
        legislatura = self._legislatura_do_ano(loa.ano)
        rcl_definitiva = loa.rcl_previa != loa.receita_corrente_liquida
        if (
            legislatura
            and legislatura.data_inicio.year == loa.ano
            and not rcl_definitiva
        ):
            return self.legislatura_do_projeto(loa)
        return legislatura

    def parlamentares_com_mandato(self, loa):
        """LOA-CRUD-067: ids dos parlamentares com mandato, de titular ou de
        suplente, na legislatura de referência da LOA. É o que separa ativos
        de inativos no detalhe da LOA, e não o campo ``ativo`` do cadastro: quem
        ficou sem mandato numa legislatura pode voltar a ter em outra."""
        return self._com_mandato_na(self.legislatura_de_referencia(loa))

    def parlamentares_originais(self, loa):
        """LOA-CRUD-069: ids dos parlamentares com mandato na legislatura do
        projeto. São eles que dividem a disponibilidade da LOA, mesmo quando a
        legislatura seguinte tem outro número de parlamentares."""
        return self._com_mandato_na(self.legislatura_do_projeto(loa))

    def parlamentares_elegiveis(self, ano):
        """LOA-CRUD-020: ids dos parlamentares que podem ser vinculados a uma
        LOA do ano: os que têm mandato na legislatura do projeto ou na do ano
        da LOA."""
        return self._com_mandato_na(
            self._legislatura_do_ano(ano - 1)
        ) | self._com_mandato_na(self._legislatura_do_ano(ano))

    def disponibilidades(self, loa):
        """A disponibilidade de cada parlamentar vinculado à LOA, sem gravar:
        ``{parlamentar_id: (saude, diversos)}``. Quem não entra na divisão fica
        fora do resultado e mantém o que tem.

        LOA-CRUD-027: a disponibilidade da LOA é dividida igualmente entre os
        vinculados. LOA-CRUD-070: na LOA do primeiro ano de uma legislatura,
        depois da RCL definitiva, o parlamentar original fica com a sua parte
        da prévia, e a diferença para a RCL definitiva, somada aos impedimentos
        de quem não tem mandato na legislatura nova, é dividida entre os que
        têm."""
        from cmj.loa.models import EmendaLoa, EmendaLoaParlamentar

        def parte(valor, quantidade):
            return quantize(valor / Decimal(quantidade), rounding=ROUND_DOWN)

        vinculados = list(
            loa.loaparlamentar_set.values_list("parlamentar_id", flat=True)
        )
        if not vinculados:
            return {}

        do_projeto = self.legislatura_do_projeto(loa)
        do_ano = self._legislatura_do_ano(loa.ano)
        originais = self._com_mandato_na(do_projeto) & set(vinculados)
        novos = self._com_mandato_na(do_ano) & set(vinculados)
        virada = bool(do_projeto and do_ano and do_projeto.pk != do_ano.pk)
        rcl_definitiva = loa.rcl_previa != loa.receita_corrente_liquida

        if not (virada and rcl_definitiva and originais and novos):
            # na LOA de virada, até a RCL definitiva, dividem os originais
            entre = originais if virada and originais else vinculados
            return {
                p: (
                    parte(loa.disp_saude, len(entre)),
                    parte(loa.disp_diversos, len(entre)),
                )
                for p in entre
            }

        tipos = (
            (EmendaLoa.SAUDE, loa.perc_disp_saude, loa.disp_saude),
            (EmendaLoa.DIVERSOS, loa.perc_disp_diversos, loa.disp_diversos),
        )
        so_originais = originais - novos
        resultado = {p: [] for p in originais | novos}
        for tipo, percentual, disp in tipos:
            previa = parte(loa.rcl_previa * percentual, 100)
            previa_por_original = parte(previa, len(originais))
            # LOA-CRUD-065: a junção não passa pelo manager de EmendaLoa; o
            # filtro de fase já deixa de fora a transformada em coletiva
            impedimentos = dict(
                EmendaLoaParlamentar.objects.filter(
                    parlamentar_id__in=so_originais,
                    emendaloa__loa=loa,
                    emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO,
                    emendaloa__tipo=tipo,
                )
                .values_list("parlamentar_id")
                .annotate(Sum("valor"))
            )
            a_dividir = (
                disp
                - previa_por_original * len(originais)
                + sum(impedimentos.values(), Decimal("0.00"))
            )
            por_novo = parte(a_dividir, len(novos))
            for p in resultado:
                valor = Decimal("0.00")
                if p in originais:
                    valor += previa_por_original - impedimentos.get(p, Decimal("0.00"))
                if p in novos:
                    valor += por_novo
                resultado[p].append(valor)
        return {p: tuple(v) for p, v in resultado.items()}

    # ------------------------------------- responsável pelas Emendas Coletivas

    # as permissões do Operador da LOA (EmendaLoa.edita_em_qualquer_fase)
    PERMISSOES_RESPONSAVEL_COLETIVAS = (
        "loa.add_emendaloa",
        "loa.change_emendaloa",
        "loa.emendaloa_full_editor",
    )

    def responsaveis_coletivas_elegiveis(self):
        """Usuários que podem ser o responsável pelas Emendas Coletivas (LOA-CRUD-072).

        Ativos, com as permissões do Operador da LOA, diretas, por grupo ou como
        superusuário, e sem vínculo de operador de autor: a coletiva não é de um
        autor e não vira proposição (LOA-FASE-070).
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()
        qs = User.objects.filter(is_active=True)
        for perm in self.PERMISSOES_RESPONSAVEL_COLETIVAS:
            app_label, codename = perm.split(".")
            com_perm = User.objects.filter(
                Q(
                    user_permissions__content_type__app_label=app_label,
                    user_permissions__codename=codename,
                )
                | Q(
                    groups__permissions__content_type__app_label=app_label,
                    groups__permissions__codename=codename,
                )
            )
            qs = qs.filter(Q(is_superuser=True) | Q(pk__in=com_perm.values("pk")))
        return qs.exclude(operadorautor_set__isnull=False).distinct()

    def pode_ser_responsavel_coletivas(self, user):
        """Mesmo critério de ``responsaveis_coletivas_elegiveis``, para um usuário."""
        return bool(
            user
            and user.is_active
            and user.has_perms(self.PERMISSOES_RESPONSAVEL_COLETIVAS)
            and not user.operadorautor_set.exists()
        )

    def responsavel_coletivas(self, loa):
        """Dono das Emendas Coletivas geradas na LOA (LOA-FASE-071).

        Levanta ``ValueError`` com a mensagem para a tela quando a LOA não tem
        responsável ou quando ele deixou de atender a LOA-CRUD-072.
        """
        user = loa.responsavel_coletivas
        if user is None:
            raise ValueError(
                "A LOA não tem responsável pelas Emendas Coletivas. Defina-o no "
                "cadastro da LOA para gerar as Emendas Coletivas."
            )
        if not self.pode_ser_responsavel_coletivas(user):
            raise ValueError(
                f"O responsável pelas Emendas Coletivas da LOA ({user}) não tem as "
                "permissões do Operador da LOA ou é operador de autor. Altere-o no "
                "cadastro da LOA para gerar as Emendas Coletivas."
            )
        return user

    def tem_norma(self, loa):
        """A matéria da LOA já virou norma. Fica guardado na instância, para
        ser consultado uma vez só por acesso (LOA-CRUD-071)."""
        if not hasattr(loa, "_tem_norma"):
            loa._tem_norma = bool(loa.materia and loa.materia.normajuridica())
        return loa._tem_norma

    def resumo_parlamentares(self, loa):
        """Resumo por parlamentar do detalhe da LOA (LOA-CRUD-040 a 049).

        Devolve ``linhas`` (uma por parlamentar vinculado, com as colunas de
        cada tipo de emenda), ``totais`` por tipo, ``existe_pcl`` e
        ``tem_norma``. LOA-CRUD-071: as somas são agrupadas por parlamentar e
        tipo, em duas consultas para a LOA inteira.
        """
        from cmj.loa.models import (
            EmendaLoa,
            EmendaLoaParlamentar,
            RegistroAjusteLoa,
            RegistroAjusteLoaParlamentar,
        )
        from cmj.loa.models.m_prestacaoconta import PrestacaoContaRegistro

        zero = Decimal("0.00")
        tipos = EmendaLoa.TIPOEMENDALOA_CHOICE[:2]
        ids_tipos = [k for k, v in tipos]

        # LOA-CRUD-067: ativo é quem tem mandato na legislatura do ano da LOA
        com_mandato = self.parlamentares_com_mandato(loa)
        tem_norma = self.tem_norma(loa)

        # D: destinações do parlamentar na LOA e no tipo, incluídas as que estão
        # em impedimento técnico. I: as das emendas impedidas. LOA-CRUD-043:
        # impedida é a emenda na fase de impedimento técnico ou com registro de
        # ajuste, a mesma regra da prestação de contas (LOA-PCC-010).
        # LOA-CRUD-065: a junção não passa pelo manager de EmendaLoa, então a
        # fase -10 (transformada em coletiva) sai aqui
        impedida = Q(emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO) | Exists(
            RegistroAjusteLoa.objects.filter(emendaloa=OuterRef("emendaloa_id"))
        )
        emendas = {
            (r["parlamentar_id"], r["emendaloa__tipo"]): r
            for r in EmendaLoaParlamentar.objects.filter(
                emendaloa__loa=loa,
                emendaloa__tipo__in=ids_tipos,
                emendaloa__fase__gt=0,
            )
            .order_by()
            .values("parlamentar_id", "emendaloa__tipo")
            .annotate(
                destinado=Sum("valor"),
                impedido=Sum("valor", filter=impedida),
            )
        }

        # Ac: ajustes em registro com emenda do mesmo tipo. As: em registro sem
        # emenda. Aimp: em registro na fase de ajuste impedido (LOA-CRUD-049).
        # O valor do ajuste não é negativo (LOA-CRUD-066). O registro liga-se a
        # várias emendas: a condição vai em subconsulta, porque a junção
        # repetiria o valor do ajuste a cada emenda
        emendas_do_registro = RegistroAjusteLoa.emendaloa.through.objects.filter(
            registroajusteloa=OuterRef("registro_id")
        )
        ajustes = {
            (r["parlamentar_id"], r["registro__tipo"]): r
            for r in RegistroAjusteLoaParlamentar.objects.filter(
                registro__oficio_ajuste_loa__loa=loa,
                registro__tipo__in=ids_tipos,
            )
            .order_by()
            .values("parlamentar_id", "registro__tipo")
            .annotate(
                com_emenda=Sum(
                    "valor",
                    filter=Exists(
                        emendas_do_registro.filter(
                            emendaloa__tipo=OuterRef("registro__tipo")
                        )
                    ),
                ),
                sem_emenda=Sum("valor", filter=~Exists(emendas_do_registro)),
                impedido=Sum(
                    "valor", filter=Q(registro__fase=RegistroAjusteLoa.AJUSTE_IMPEDIDO)
                ),
            )
        }

        # LOA-CRUD-054: os totais existem mesmo sem parlamentar vinculado
        totais = {
            k: dict(ja_destinado=zero, impedimento_tecnico=zero, sem_destinacao=zero)
            for k in ids_tipos
        }
        linhas = []
        for lp in loa.loaparlamentar_set.select_related("parlamentar").order_by(
            "parlamentar__nome_parlamentar"
        ):
            linha = {
                "loaparlamentar": lp,
                "com_mandato": lp.parlamentar_id in com_mandato,
            }
            for k, nome in tipos:
                disp = lp.disp_saude if k == EmendaLoa.SAUDE else lp.disp_diversos
                emenda = emendas.get((lp.parlamentar_id, k), {})
                ajuste = ajustes.get((lp.parlamentar_id, k), {})
                destinado = emenda.get("destinado") or zero
                impedido = emenda.get("impedido") or zero
                com_emenda = ajuste.get("com_emenda") or zero
                sem_emenda = ajuste.get("sem_emenda") or zero
                ajuste_impedido = ajuste.get("impedido") or zero

                # LOA-CRUD-045
                remanescente = disp - destinado
                ja_destinado = destinado - impedido + com_emenda + sem_emenda
                sem_destinacao = remanescente + impedido - com_emenda - sem_emenda
                impedimento_tecnico = impedido - com_emenda

                # LOA-CRUD-046: com mandato e LOA com norma, o remanescente
                # entra no impedimento, para mostrar o impacto total no valor
                # disponível para destinação
                if linha["com_mandato"] and tem_norma:
                    impedimento_tecnico += remanescente - sem_emenda

                # LOA-CRUD-049: o ajuste impedido fica no impedimento técnico, e
                # não no já destinado, haja ou não prestação de contas
                ja_destinado -= ajuste_impedido
                impedimento_tecnico += ajuste_impedido
                sem_destinacao += ajuste_impedido

                linha[k] = {
                    "name": nome,
                    "sem_destinacao": sem_destinacao,
                    "impedimento_tecnico": impedimento_tecnico,
                    "ja_destinado": ja_destinado,
                }
                # LOA-CRUD-048
                for coluna in totais[k]:
                    totais[k][coluna] += linha[k][coluna]
            linhas.append(linha)

        # LOA-CRUD-040: primeiro os que têm mandato, cada grupo em ordem de nome
        linhas.sort(key=lambda x: not x["com_mandato"])

        return dict(
            linhas=linhas,
            totais=totais,
            tem_norma=tem_norma,
            existe_pcl=PrestacaoContaRegistro.objects.filter(
                prestacao_conta__loa=loa
            ).exists(),
        )

    @staticmethod
    def _partes_por_parlamentar(loa, *campos, ordem):
        """Soma das participações de cada parlamentar nas emendas impositivas
        da LOA, agrupada pelos campos informados (LOA-CRUD-056)."""
        from cmj.loa.models import EmendaLoa

        parlamentar = "emendaloaparlamentar_set__parlamentar"
        for el in (
            EmendaLoa.objects.filter(loa=loa, tipo__gt=0)
            .values(*campos, f"{parlamentar}__id", f"{parlamentar}__nome_parlamentar")
            .order_by(*ordem, f"{parlamentar}__nome_parlamentar")
            .annotate(valor_parte_parlamentar=Sum("emendaloaparlamentar_set__valor"))
        ):
            # LOA-CRUD-058: emenda sem participação de parlamentar soma zero
            el["valor_parte_parlamentar"] = el["valor_parte_parlamentar"] or Decimal(
                "0.00"
            )
            el["parlamentar_id"] = el[f"{parlamentar}__id"]
            el["nome_parlamentar"] = el[f"{parlamentar}__nome_parlamentar"]
            yield el

    def resumo_unidades(self, loa):
        """Resumo por unidade orçamentária do detalhe da LOA (LOA-CRUD-056 a
        058): ``unidades``, por ``(id, especificação)``, e ``soma_geral``."""
        soma_geral = Decimal("0.00")
        unidades = {}
        for el in self._partes_por_parlamentar(
            loa,
            "unidade__especificacao",
            "unidade__id",
            ordem=("unidade__especificacao",),
        ):
            unidade = unidades.setdefault(
                (el["unidade__id"], el["unidade__especificacao"]),
                {"parlamentares": [], "soma_unidade": Decimal("0.00")},
            )
            unidade["soma_unidade"] += el["valor_parte_parlamentar"]
            unidade["parlamentares"].append(
                {
                    "id": el["parlamentar_id"] or "",
                    "nome_parlamentar": el["nome_parlamentar"] or "",
                    "soma_valor": el["valor_parte_parlamentar"],
                }
            )
            soma_geral += el["valor_parte_parlamentar"]
        return dict(unidades=unidades, soma_geral=soma_geral)

    def resumo_entidades(self, loa):
        """Resumo por entidade do detalhe da LOA (LOA-CRUD-060 e 061):
        ``entidades``, por ``(id, nome)``, e ``soma_geral``. Emenda sem
        entidade fica fora."""
        soma_geral = Decimal("0.00")
        entidades = {}
        for el in self._partes_por_parlamentar(
            loa,
            "tipo",
            "entidade__nome_fantasia",
            "entidade__id",
            "unidade__especificacao",
            ordem=("tipo", "entidade__nome_fantasia"),
        ):
            if not el["entidade__nome_fantasia"]:
                continue
            entidade = entidades.setdefault(
                (el["entidade__id"], el["entidade__nome_fantasia"].upper()),
                {
                    "tipo": el["tipo"],
                    "parlamentares": [],
                    "soma_entidade": Decimal("0.00"),
                },
            )
            entidade["soma_entidade"] += el["valor_parte_parlamentar"]
            # LOA-CRUD-061: a consulta separa por tipo e unidade; cada
            # parlamentar entra uma vez só na entidade, com a soma das partes
            parte = next(
                (
                    p
                    for p in entidade["parlamentares"]
                    if p["id"] == el["parlamentar_id"]
                ),
                None,
            )
            if parte:
                parte["soma_valor"] += el["valor_parte_parlamentar"]
            else:
                entidade["parlamentares"].append(
                    {
                        "id": el["parlamentar_id"] or "",
                        "nome_parlamentar": el["nome_parlamentar"] or "",
                        "soma_valor": el["valor_parte_parlamentar"],
                    }
                )
            soma_geral += el["valor_parte_parlamentar"]

        for entidade in entidades.values():
            entidade["parlamentares"].sort(key=lambda p: p["nome_parlamentar"] or "")
        return dict(entidades=entidades, soma_geral=soma_geral)

    def update_disponibilidades(self, loa):
        """Grava em cada ``LoaParlamentar`` a disponibilidade calculada por
        ``disponibilidades``."""
        if not loa:
            raise ValueError("LoaService requires a Loa instance")

        valores = self.disponibilidades(loa)
        for lp in loa.loaparlamentar_set.all():
            if lp.parlamentar_id not in valores:
                continue
            lp.disp_saude, lp.disp_diversos = valores[lp.parlamentar_id]
            lp.disp_total = lp.disp_saude + lp.disp_diversos
            lp.save()
        return loa
