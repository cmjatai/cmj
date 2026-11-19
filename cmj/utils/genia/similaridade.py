import logging
import time

from django.utils import timezone

from cmj.core.models import IAQuota
from cmj.utils.genia import prompts_similaridade
from cmj.utils.genia.base import IAGenaiBase
from cmj.utils.genia.extracao import extract_clean_text_from_path

logger = logging.getLogger(__name__)

BATCH_FINAL_STATES = (
    "JOB_STATE_SUCCEEDED",
    "JOB_STATE_FAILED",
    "JOB_STATE_CANCELLED",
    "JOB_STATE_EXPIRED",
)


class IAAnaliseSimilaridadeService(IAGenaiBase):
    """
    Análise de similaridade entre os textos originais de duas matérias.

    Spec: docs/specs/genia/similaridade.md
    """

    quota_service_name = IAQuota.ServicosAutorizados.IA_ANALISE_SIMILARIDADE_SERVICE
    response_mime_type = "text/plain"

    prompt_template = prompts_similaridade.PROMPT_V2

    BATCH_POLL_INTERVAL = 60  # segundos entre consultas ao estado dos jobs

    def make_prompt(self, original, analisado, o_epigrafe, a_epigrafe):
        return self.prompt_template.format(
            original=original,
            analisado=analisado,
            o_epigrafe=o_epigrafe,
            a_epigrafe=a_epigrafe,
        )

    def make_prompt_from_similaridade(self, similaridade):
        text1, text2 = self.extract_text_from_similaridade(similaridade)
        return self.make_prompt(
            text1,
            text2,
            similaridade.materia_1.epigrafe_short,
            similaridade.materia_2.epigrafe_short,
        )

    def extract_text_from_similaridade(self, similaridade):
        return (
            extract_clean_text_from_path(
                similaridade.materia_1.texto_original.original_path
            ),
            extract_clean_text_from_path(
                similaridade.materia_2.texto_original.original_path
            ),
        )

    def apply_answer(self, similaridade, text, logger=logger):
        """Preenche a análise com a resposta do modelo, sem salvar."""
        similaridade.analise = text
        similaridade.ia_name = self.ia_model_name
        similaridade.data_analise = timezone.localtime()

        try:
            # A resposta traz o percentual no formato "[[ 85% ]]"
            similaridade.similaridade = int(text.split("[[")[1].split("%")[0].strip())
        except Exception as e:
            logger.error(e)
            similaridade.similaridade = 0
        return similaridade

    def run(self, similaridade, *args, **kwargs):
        """Analisa um par de matérias de forma síncrona."""
        _logger = kwargs.get("logger", logger)
        _save = kwargs.get("save", True)

        prompt = self.make_prompt_from_similaridade(similaridade)
        answer = self.generate_content(prompt, ascending=False)

        self.apply_answer(similaridade, answer.text, logger=_logger)
        if _save:
            similaridade.save()
        return similaridade

    def batch_run(self, analises, logger=logger):
        """
        Analisa vários pares pela API de batch e bloqueia até todos os jobs
        terminarem. A IAQuota define quantos jobs (`get_threads`) e quantas
        análises por job (`batch_size`).
        """
        quota = self.retrieve_quota_if_available(ascending=False)

        get_threads = quota.get_threads
        batch_size = quota.batch_size

        stamp = int(time.time())
        execs = [
            {
                "analises": [],
                "display_name": f"batch_analise_similaridade_entre_materias_thread_{i}_{stamp}",
                "job_name": None,
                "finished": False,
            }
            for i in range(get_threads)
        ]

        # limita para evitar excesso de requisições e distribui entre os jobs
        analises = list(analises[0 : batch_size * get_threads])
        for i, analise in enumerate(analises):
            execs[i % get_threads]["analises"].append(analise)

        for exec_ in execs:
            inline_requests = [
                {
                    "config": dict(response_mime_type=self.response_mime_type),
                    "contents": [
                        {
                            "parts": [
                                {"text": self.make_prompt_from_similaridade(analise)}
                            ],
                            "role": "user",
                        }
                    ],
                }
                for analise in exec_["analises"]
            ]

            batch_job = self.client.batches.create(
                model=self.ia_model_name,
                src=inline_requests,
                config={"display_name": exec_["display_name"]},
            )
            exec_["job_name"] = batch_job.name

        def process_exec(exec_, batch_job):
            state = batch_job.state.name
            if state != "JOB_STATE_SUCCEEDED":
                logger.error(
                    f"Batch job {exec_['job_name']} did not succeed. State: {state}"
                )
                return

            responses = [
                resp.response.text
                for resp in batch_job.dest.inlined_responses
                if resp.response
            ]
            for i, text in enumerate(responses):
                if not text:
                    continue

                quota.create_log()

                similaridade = exec_["analises"][i]
                self.apply_answer(similaridade, text, logger=logger)
                similaridade.save()

        while True:
            all_finished = True
            for exec_ in execs:
                if exec_["finished"]:
                    continue
                job_name = exec_["job_name"]
                batch_job = self.client.batches.get(name=job_name)
                if batch_job.state.name not in BATCH_FINAL_STATES:
                    all_finished = False
                    logger.info(
                        f"Batch job {job_name}. Current state: {batch_job.state.name}"
                    )
                else:
                    exec_["finished"] = True
                    process_exec(exec_, batch_job)

            if all_finished:
                break
            time.sleep(self.BATCH_POLL_INTERVAL)
