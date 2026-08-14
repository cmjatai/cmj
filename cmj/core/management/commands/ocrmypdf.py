import fcntl
import logging
import os
import shutil
import stat
import sys
import time
from datetime import datetime, timedelta
from pwd import getpwuid
from time import sleep

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save
from django.utils import timezone

from cmj.core.models import OcrMyPDF
from cmj.diarios.models import DiarioOficial
from cmj.utils import ProcessoExterno
from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import (
    DocumentoAcessorioAdministrativo,
    DocumentoAdministrativo,
)
from sapl.sessao.models import SessaoPlenaria


def _get_registration_key(model):
    return "%s_%s" % (model._meta.app_label, model._meta.model_name)


class _TempoLimiteAtingido(Exception):
    """Corte de tempo por execução: para de varrer, mas ainda reindexa."""


class _SessaoAbertaInterrompeu(Exception):
    """Sessão plenária abriu durante o processamento: aborta sem reindexar."""


class Command(BaseCommand):

    # janela considerada execução noturna: [22h, 6h)
    HORA_FIM_NOTURNO = 6
    HORA_INICIO_NOTURNO = 22

    JOBS_NOTURNO = 12
    JOBS_DIURNO = 4

    TIMEOUT_OCR_SECONDS = 300
    TEMPO_MAX_EXECUCAO = timedelta(minutes=2)
    SLEEP_ENTRE_ITENS = 2

    # retenção de histórico de OcrMyPDF, aplicada só na execução noturna
    RETENCAO_OCR_DIAS = 360
    RETENCAO_OCR_FALHA_DIAS = 90

    TMP_IDLE_SECONDS = 86400  # 1 dia sem uso para ser elegível à limpeza
    MTIME_FOLGA_SECONDS = 86400  # folga de 1 dia ao comparar mtime x último ocr

    # (usuário dono do arquivo, prefixo do nome) elegíveis à limpeza em /tmp
    TMP_CLEAR_RULES = [
        ("djangoapps", "pymp"),
        ("djangoapps", "com.github.ocrmypdf"),
        ("djangoapps", "yarn--"),
        # ('solr', 'upload_'),
        ("djangoapps", "br.leg.go.jatai.portalcmj."),
    ]

    LOCK_PATH = "/tmp/cmj_ocrmypdf.lock"

    max_paginas_noturno = 100  # avaliar tempo de execução para números maiores
    max_paginas_diurno = 50

    # só usa os limites de tamanho de arquivo se não houver número de páginas
    # ao alterar aqui, analisar tb a indexação no solr
    max_size_noturno = 40 * 1024 * 1024
    max_size_diurno = 10 * 1024 * 1024

    execucao_noturna = False

    models = [
        {
            "model": DocumentoAdministrativo,
            "file_field": ("texto_integral",),
            "count": 0,
            "count_base": 9,
            "order_by": "-data",
            "years_priority": 1,
        },
        {
            "model": MateriaLegislativa,
            "file_field": ("texto_original",),
            "count": 0,
            "count_base": 2,
            "order_by": "-data_apresentacao",
            "years_priority": 1,
        },
        {
            "model": NormaJuridica,
            "file_field": ("texto_integral",),
            "count": 0,
            "count_base": 2,
            "order_by": "-data",
            "years_priority": 1,
        },
        {
            "model": DocumentoAcessorioAdministrativo,
            "file_field": ("arquivo",),
            "count": 0,
            "count_base": 2,
            "order_by": "-data",
            "years_priority": 1,
        },
        {
            "model": DocumentoAcessorio,
            "file_field": ("arquivo",),
            "count": 0,
            "count_base": 2,
            "order_by": "-data",
            "years_priority": 1,
        },
        {
            "model": SessaoPlenaria,
            "file_field": ("upload_pauta", "upload_ata", "upload_anexo"),
            "count": 0,
            "count_base": 2,
            "order_by": "-data_inicio",
            "years_priority": 1,
        },
        {
            "model": DiarioOficial,
            "file_field": ("arquivo",),
            "count": 0,
            "count_base": 1,
            "order_by": "-data",
            "years_priority": 0,
        },
    ]

    def delete_itens_tmp_folder(self):
        entries = os.scandir("/tmp/")

        now = time.time()
        for entry in entries:
            age = now - os.stat(entry.path)[stat.ST_MTIME]

            if age <= self.TMP_IDLE_SECONDS:
                continue

            for user, start_name in self.TMP_CLEAR_RULES:
                if not entry.name.startswith(start_name):
                    continue
                if getpwuid(os.stat(entry.path).st_uid).pw_name != user:
                    continue

                try:
                    shutil.rmtree(entry.path, ignore_errors=True)
                    if os.path.exists(entry.path):
                        os.remove(entry.path)
                except Exception:
                    self.logger.exception("Falha ao limpar %s", entry.path)
                break

    def _adquirir_lock(self):
        # lock exclusivo via flock: liberado automaticamente pelo SO mesmo
        # se o processo morrer, ao contrário do parsing de `ps` anterior
        self._lock_file = open(self.LOCK_PATH, "w")
        try:
            fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._lock_file.close()
            self._lock_file = None
            return False
        return True

    def _liberar_lock(self):
        if getattr(self, "_lock_file", None):
            fcntl.flock(self._lock_file, fcntl.LOCK_UN)
            self._lock_file.close()
            self._lock_file = None

    def tem_sessaoplenaria_aberta(self):
        return SessaoPlenaria.objects.filter(
            data_inicio=timezone.localdate(), iniciada=True, finalizada=False
        ).exists()

    def handle(self, *args, **options):

        if self.tem_sessaoplenaria_aberta():
            return

        self.logger = logging.getLogger(__name__)

        init = timezone.localtime()
        if not settings.DEBUG and not self._adquirir_lock():
            print(init, "Command OcrMyPdf já está sendo executado por outro processo")
            return

        try:
            self._executar(init)
        finally:
            if not settings.DEBUG:
                self._liberar_lock()

    def _executar(self, init):
        post_save.disconnect(dispatch_uid="timerefresh_post_signal")
        post_save.disconnect(dispatch_uid="signal_post_syncrefresh")

        self.delete_itens_tmp_folder()

        self.execucao_noturna = (
            init.hour < self.HORA_FIM_NOTURNO or init.hour >= self.HORA_INICIO_NOTURNO
        )

        # só faz limpeza de histórico em execução noturna
        if self.execucao_noturna:
            self._run_manutencao_noturna(init)

        years_updated = set()
        try:
            while self.models:
                for model in self.models:
                    model["count"] = 0

                for model in self.models:
                    self._processar_model(model, init, years_updated)

                self.models = list(filter(lambda x: x["count"] != 0, self.models))
        except _TempoLimiteAtingido:
            pass
        except _SessaoAbertaInterrompeu:
            return

        self._reindexar_anos(years_updated)

    def _run_manutencao_noturna(self, init):
        # refaz tudo que foi feito há mais de RETENCAO_OCR_DIAS
        OcrMyPDF.objects.filter(
            created__lt=init - timedelta(days=self.RETENCAO_OCR_DIAS)
        ).delete()

        # refaz tudo que foi feito há mais de RETENCAO_OCR_FALHA_DIAS e falhou
        OcrMyPDF.objects.filter(
            created__lt=init - timedelta(days=self.RETENCAO_OCR_FALHA_DIAS),
            sucesso=False,
        ).delete()

    def _processar_model(self, model, init, years_updated):
        ct = ContentType.objects.get_for_model(model["model"])
        count = 0

        data_field = model["order_by"][1 if model["order_by"].startswith("-") else 0 :]

        items = model["model"].objects.order_by(model["order_by"])

        for item in items:

            if self.tem_sessaoplenaria_aberta():
                raise _SessaoAbertaInterrompeu()

            paginas = 0
            if hasattr(item, "_paginas"):
                # tenta capturar o número de páginas
                try:
                    paginas = item.paginas
                except Exception:
                    paginas = 0

                # se não conseguiu num de páginas, só passa ao teste de
                # tamanho de arquivo se a execução é noturna
                if not paginas and not self.execucao_noturna:
                    continue

                # mesmo a execução sendo noturna não faz arquivos com mais
                # de max_paginas_noturno
                if paginas > self.max_paginas_noturno:
                    continue

                # se diurno não faz ocr em arquivos com páginas superiores
                # a max_paginas_diurno
                if paginas > self.max_paginas_diurno and not self.execucao_noturna:
                    continue

            if count >= model["count_base"] and not self.execucao_noturna:
                break

            for ff in model["file_field"]:
                tentou, continuar = self._processar_campo(
                    item, ff, model, ct, data_field, paginas, init, years_updated
                )
                if tentou:
                    count += 1
                if not continuar:
                    break

    def _processar_campo(
        self, item, ff, model, ct, data_field, paginas, init, years_updated
    ):
        """Retorna (tentou_processar, continuar_proximos_campos)."""

        # se documento foi homologado não executa ocr
        if hasattr(item, "metadata"):
            md = item.metadata
            if md and "signs" in md and ff in md["signs"]:
                signs_field = md["signs"][ff]
                if ("hom" in signs_field and signs_field["hom"]) or (
                    "signs" in signs_field and signs_field["signs"]
                ):
                    return False, True

        file = getattr(item, ff)

        if file and not file.name.endswith(".pdf"):
            return False, True

        if not paginas:
            if file and file.name and file.size > self.max_size_noturno:
                return False, True

            if (
                file
                and file.name
                and file.size > self.max_size_diurno
                and not self.execucao_noturna
            ):
                return False, True

        ocr = OcrMyPDF.objects.filter(
            content_type=ct, object_id=item.id, field=ff
        ).first()

        if ocr and file and file.name:
            # possui meta ocr anterior, testa se o arq é mais recente que
            # o último ocr feito
            try:
                t = os.path.getmtime(file.path) - self.MTIME_FOLGA_SECONDS
                date_file = datetime.fromtimestamp(t, timezone.utc)

                if date_file <= ocr.created:
                    return False, True
            except Exception:
                self.logger.exception("Falha ao checar mtime de %s", file.path)
                if settings.DEBUG:
                    return False, True

            # se arq é mais novo, apaga o meta ocr p fazer novamente
            ocr.delete()
            ocr = None

        elif ocr and not file or ocr and file and not file.name:
            # se existe um meta ocr mas não existe mais o arquivo
            ocr.delete()
            return False, True

        if ocr or not file or not file.name:
            return False, True

        # existe arquivo mas não existe meta ocr por nunca ter feito ou por
        # alguma regra de remoção acima
        self.logger.info(str(item.id) + " " + str(model["model"]))
        model["count"] += 1
        print(item.id, model["model"])

        o = OcrMyPDF()
        o.content_object = item
        o.field = ff
        o.sucesso = False
        o.save()

        try:
            init_item = timezone.localtime()
            result = self.run(item, ff)
            if result is None:
                return True, False

            o.sucesso = result
            o.save()

            if result and hasattr(item, data_field):
                item_data = getattr(item, data_field)
                if item_data and hasattr(item_data, "year"):
                    years_updated.add((item_data.year, model["model"]))

            now = timezone.localtime()

            if hasattr(item, "_paginas"):
                print(
                    item.id,
                    item._paginas,
                    model["model"]._meta.label,
                    str(now - init_item),
                )

            self.logger.info(
                str(now - init_item) + " " + str(item.id) + " " + str(model["model"])
            )

            if now - init > self.TEMPO_MAX_EXECUCAO:
                raise _TempoLimiteAtingido()

        except _TempoLimiteAtingido:
            raise
        except Exception:
            self.logger.exception(
                "Falha ao processar OCR do item %s (%s)", item.id, model["model"]
            )

        self.logger.info("Aguardando...")
        print("Aguardando...")
        sleep(self.SLEEP_ENTRE_ITENS)
        print("Seguindo...")
        self.logger.info("Seguindo...")

        return True, True

    def _reindexar_anos(self, years_updated):
        for y, m in years_updated:
            try:
                self.logger.info(f"Ano Executado: {y} chamando update_index...")
                management.call_command(
                    "update_index",
                    f"{m._meta.app_label}.{m._meta.object_name}",
                    f"--start={y}-01-01T00:00:00'",
                    f"--end='{y}-12-31T23:59:59'",
                    "--verbosity=3",
                    "--batch-size=100",
                    "--using=default",
                )
            except Exception:
                self.logger.exception("Falha ao reindexar ano %s do model %s", y, m)

    def run(self, item, fstr):

        file = getattr(item, fstr)
        # não usar --force-ocr pois invalida as assinaturas digitais em
        # arquivos digitais
        # force-ocr só pode ser usado se outro teste verificar antes que um
        # documento não possui assinatura digital

        in_path = file.path.replace("media/sapl/", "media/original__sapl/")
        in_path = in_path.replace("media/cmj/", "media/original__cmj/")

        out_path = file.path
        if out_path.endswith("jpeg"):
            out_path = out_path + ".pdf"

        jobs = self.JOBS_NOTURNO if self.execucao_noturna else self.JOBS_DIURNO

        cmd = [
            "{}/ocrmypdf".format("/".join(sys.executable.split("/")[:-1])),
            "--redo-ocr",
            "-l por",
            "-q",
            "-j {}".format(jobs),
            "--output-type pdfa-2",
            in_path,
            out_path,
        ]

        try:
            p = ProcessoExterno(" ".join(cmd), self.logger)
            r = p.run(timeout=self.TIMEOUT_OCR_SECONDS)

            if r is None:
                return None
            if r[0] in (0, 2, 6):
                return True
            return None
        except Exception:
            self.logger.exception("Falha ao executar ocrmypdf para o item %s", item.id)
            return False
