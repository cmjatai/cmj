from decimal import ROUND_DOWN, Decimal

from django.db.models.aggregates import Sum

from cmj.utils import quantize
from sapl.parlamentares.models import Legislatura, Parlamentar


class LoaService:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LoaService, cls).__new__(cls)
        return cls._instance

    def update_disponibilidades(self, loa):
        from cmj.loa.models import EmendaLoa

        if not loa:
            raise ValueError("LoaService requires a Loa instance")

        def set_values_for_lp(lp, disp_total, disp_saude, disp_diversos, count_lps):
            idsp = quantize(disp_saude / Decimal(count_lps), rounding=ROUND_DOWN)
            iddp = quantize(disp_diversos / Decimal(count_lps), rounding=ROUND_DOWN)
            # if iddp + idsp != idtp:
            #    iddp = idtp - idsp
            lp.disp_total = idsp + iddp
            lp.disp_saude = idsp
            lp.disp_diversos = iddp

        legislatura_atual = Legislatura.cache_legislatura_atual()

        materia_in_legislatura_atual = True
        loa_in_legislatura_atual = True

        if loa.materia:
            materia_in_legislatura_atual = (
                legislatura_atual["data_inicio"]
                <= loa.materia.data_apresentacao
                <= legislatura_atual["data_fim"]
            )
            loa_in_legislatura_atual = (
                legislatura_atual["data_inicio"].year
                <= loa.ano
                <= legislatura_atual["data_fim"].year
            )

        lps = loa.loaparlamentar_set.all()
        count_lps = lps.count()

        if (loa_in_legislatura_atual and materia_in_legislatura_atual) or (
            not loa_in_legislatura_atual and not materia_in_legislatura_atual
        ):
            count_lps = lps.count()
            if count_lps:
                for lp in lps:
                    set_values_for_lp(
                        lp,
                        loa.disp_total,
                        loa.disp_saude,
                        loa.disp_diversos,
                        count_lps,
                    )
                    lp.save()
            return loa

        parlamentares_ativos = {
            p: list(p.emendaloaparlamentar_set.filter(emendaloa__loa=loa))
            for p in Parlamentar.objects.filter(ativo=True)
        }
        parlamentares_ativos_com_emendas = {
            p: emendas for p, emendas in parlamentares_ativos.items() if emendas
        }
        parlamentares_ativos_sem_emendas = {
            p: emendas for p, emendas in parlamentares_ativos.items() if not emendas
        }

        parlamentares_inativos_com_emendas = {
            p: list(p.emendaloaparlamentar_set.filter(emendaloa__loa=loa))
            for p in Parlamentar.objects.filter(
                ativo=False, emendaloaparlamentar_set__emendaloa__loa=loa
            ).distinct()
        }

        count_parlamentares_ativos = Decimal(len(parlamentares_ativos))
        count_parlamentares_ativos_com_emendas = Decimal(
            len(parlamentares_ativos_com_emendas)
        )
        count_parlamentares_ativos_sem_emendas = Decimal(
            len(parlamentares_ativos_sem_emendas)
        )

        count_parlamentares_inativos_com_emendas = Decimal(
            len(parlamentares_inativos_com_emendas)
        )

        count_parlamentares_com_emendas = Decimal(
            count_parlamentares_ativos_com_emendas
            + count_parlamentares_inativos_com_emendas
        )

        disp_previa_total = quantize(
            loa.rcl_previa * loa.perc_disp_total / Decimal(100),
            rounding=ROUND_DOWN,
        )
        disp_previa_saude = quantize(
            loa.rcl_previa * loa.perc_disp_saude / Decimal(100),
            rounding=ROUND_DOWN,
        )
        disp_previa_diversos = quantize(
            loa.rcl_previa * loa.perc_disp_diversos / Decimal(100),
            rounding=ROUND_DOWN,
        )

        disp_previa_total = (
            quantize(
                disp_previa_total / count_parlamentares_ativos, rounding=ROUND_DOWN
            )
            * count_parlamentares_ativos
        )
        disp_previa_saude = (
            quantize(
                disp_previa_saude / count_parlamentares_ativos, rounding=ROUND_DOWN
            )
            * count_parlamentares_ativos
        )
        disp_previa_diversos = (
            quantize(
                disp_previa_diversos / count_parlamentares_ativos, rounding=ROUND_DOWN
            )
            * count_parlamentares_ativos
        )

        imp_inativos_saude = Decimal("0.00")
        imp_inativos_diversos = Decimal("0.00")
        for lp in lps:
            if lp.parlamentar in parlamentares_inativos_com_emendas.keys():
                soma_imp_saude = lp.parlamentar.emendaloaparlamentar_set.filter(
                    emendaloa__loa=loa,
                    emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO,
                    emendaloa__tipo=EmendaLoa.SAUDE,
                ).aggregate(Sum("valor"))
                soma_imp_diversos = lp.parlamentar.emendaloaparlamentar_set.filter(
                    emendaloa__loa=loa,
                    emendaloa__fase=EmendaLoa.IMPEDIMENTO_TECNICO,
                    emendaloa__tipo=EmendaLoa.DIVERSOS,
                ).aggregate(Sum("valor"))

                soma_imp_saude = soma_imp_saude["valor__sum"] or Decimal("0.00")
                soma_imp_diversos = soma_imp_diversos["valor__sum"] or Decimal("0.00")
                dps = disp_previa_saude
                dpd = disp_previa_diversos
                set_values_for_lp(
                    lp, dps + dpd, dps, dpd, count_parlamentares_com_emendas
                )
                lp.disp_total -= soma_imp_saude + soma_imp_diversos
                lp.disp_saude -= soma_imp_saude
                lp.disp_diversos -= soma_imp_diversos
                lp.save()
                imp_inativos_saude += soma_imp_saude
                imp_inativos_diversos += soma_imp_diversos

        for lp in lps:
            if lp.parlamentar in parlamentares_ativos_com_emendas.keys():
                set_values_for_lp(
                    lp,
                    loa.disp_total + imp_inativos_saude + imp_inativos_diversos,
                    loa.disp_saude + imp_inativos_saude,
                    loa.disp_diversos + imp_inativos_diversos,
                    count_parlamentares_ativos,
                )
            elif lp.parlamentar in parlamentares_ativos_sem_emendas.keys():
                set_values_for_lp(
                    lp,
                    loa.disp_total
                    - disp_previa_total
                    + imp_inativos_saude
                    + imp_inativos_diversos,
                    loa.disp_saude - disp_previa_saude + imp_inativos_saude,
                    loa.disp_diversos - disp_previa_diversos + imp_inativos_diversos,
                    count_parlamentares_ativos,
                )
            lp.save()
