import logging
import time

import pymupdf
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cmj.utils import clean_text
from cmj.utils.genia import IAGenaiBase

logger = logging.getLogger(__name__)


class IAAnaliseSimilaridadeService(IAGenaiBase):
    """
    Classe para análise de similaridade
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_mime_type = "text/plain"

    def make_prompt(self, original, analisado, o_epigrafe, a_epigrafe):

        prompt_lite = f"""
Atue como um analista de textos legislativos de uma Câmara Municipal.
Responda de forma educada, formal e direta. Use o termo "similaridade" para se referir à cópia ou semelhança entre textos.

Sua tarefa é comparar dois requerimentos ("{o_epigrafe}" e "{a_epigrafe}").
Para avaliar a similaridade, foque APENAS nestes 3 elementos (A Tríade):
- O QUÊ: Qual é o benefício ou ação solicitada?
- ONDE: Qual é a localidade exata (bairro, rua, região)?
- PARA QUEM: Quem é o beneficiário?

REGRAS DE ANÁLISE:
1. Oculte a Tríade da resposta.
2. Ignore quem são os vereadores/autores.
3. Os textos são sobre um município em específico, a análise de Localidade esperada, portanto, é de bairros, ruas, regiões ou localidades dentro do município. Se os textos mencionarem apenas o nome do município, sem uma localidade específica, o foco da análise deve direcionar totalmente para o beneficiário e o benefício solicitado, ou seja, o QUÊ e PARA QUEM.
4. Atribua similaridade máxima apenas se os 3 elementos da Tríade coincidirem exatamente. Mesmo pequenas diferenças de semântica devem reduzir a similaridade
5. Se houver diferença na localidade ou na solicitação, a similaridade deve cair consideravelmente.
6. Caso identifique diferenças, mas que trata-se de um texto estar contido no outro, ou seja, um texto ser uma versão mais detalhada do outro, aumente uma similaridade chegando inclusive afirmar, por estar contido, que é semelhante e, se possível, explique a razão.

Você DEVE retornar a resposta exatamente no formato Markdown abaixo. Não adicione saudações ou textos extras.

Markdown:
### **Análise de Similaridade Legislativa**

**Parecer Técnico:**
[Escreva um parágrafo curto e cordial comparando detalhadamente O QUÊ, ONDE e PARA QUEM nos dois textos. Explique se eles coincidem ou onde divergem.]

**Os textos pedem o mesmo benefício para a mesma localidade?** **[Sim / Não]**

**Similaridade:** [[ XX% ]]

---
TEXTOS PARA ANÁLISE:

<ORIGINAL>
{original}
</ORIGINAL>

<ANALISADO>
{analisado}
</ANALISADO>
"""

        prompt__para_versoes_pro = f"""Você é um especialista em redação de textos legislativos de uma Câmara Municipal brasileira.
Sua comunicação deve ter um tom oficial e cordial, porém leve, direto e extremamente conciso.

Sua tarefa é comparar dois requerimentos legislativos ("{o_epigrafe}" e "{a_epigrafe}") e avaliar se eles solicitam o mesmo benefício para a mesma localidade e beneficiário.

REGRAS DE ANÁLISE (Siga rigorosamente):
1. IGNORE os autores dos textos.
2. Foco exclusivo na tríade: O QUÊ (ação/benefício), ONDE (localidade específica) e PARA QUEM (beneficiário).
3. Penalize o percentual de similaridade se houver qualquer diferença na localidade ou na solicitação. Atribua similaridade máxima apenas se a tríade for idêntica.
4. Jamais utilize a palavra "plágio". Refira-se apenas como "similaridade".
5. Não inclua saudações, conclusões genéricas ou metalinguagem (ex: "Aqui está a análise...").

FORMATO DE SAÍDA OBRIGATÓRIO:
Retorne a resposta estritamente no formato Markdown abaixo, preenchendo as informações solicitadas sem adicionar novos tópicos:

### Análise de Similaridade Legislativa

**Os textos pedem o mesmo benefício para a mesma localidade?** **[Responda apenas Sim ou Não]**

**Similaridade:** [[ XX% ]]

**Parecer Técnico:**
[Escreva um único parágrafo, de forma cordial e clara, justificando o percentual com base exclusivamente na comparação entre o benefício, a localidade e o beneficiário dos documentos "{o_epigrafe}" e "{a_epigrafe}".]

---
TEXTOS PARA ANÁLISE:

<ORIGINAL>
{original}
</ORIGINAL>

<ANALISADO>
{analisado}
</ANALISADO>
"""

        prompt2 = f"""
Assuma a personalidade de um especialista em produção de textos legislativos em uma câmara municipal brasileira com experiência em redação de documentos oficiais.
Sua tarefa é avaliar a similaridade de dois textos e identificar se eles tratam do mesmo assunto e pedem o mesmo benefício para a mesma localidade específica.
Os textos tratam de requerimentos legislativos, que são pedidos formais feitos por vereadores de uma mesma cidade para atender demandas da população ou seja, localidades específicas dentro do município.

Para tal tarefa, compare o conteúdo de <ORIGINAL></ORIGINAL> com o conteúdo de <ANALISADO></ANALISADO>.
Para citar estes dois conteúdos, nomeie eles respectivamente da seguinte maneira: "{o_epigrafe}" e "{a_epigrafe}".

Remova de sua análise os autores pois são irrelevantes para a comparação requerida.
O importante é o que está sendo pedido, quem será o beneficiário do pedido e para qual localidade dentro no município está sendo feito tal pedido.

Escreva de forma dissertativa explicativa utilizando o mínimo de palavras ou frases destas instruções, sem considerações adicionais ou mesmo conclusões extras. Neste contexto responda:
- Os textos estão pedindo o mesmo benefício para a mesma localidade? Responda objetivamente com "Sim" ou "Não" dastacando em negrito está pergunta e resposta.

- Evite ao máximo utilizar palavras ou frases destas instruções.
- Calcule a semelhança percentual entre os documentos desconsiderando autores, focando na solicitação, no problema apontado, no beneficiário e na localidade, qual semelhança percentual entre <ORIGINAL></ORIGINAL> e <ANALISADO></ANALISADO>? Coloque o resultado em percentual com uma marcação de colchetes, exemplo: "[[ 100% ]]".
- Eleve a similaridade a um valor máximo se os textos estiverem pedindo exatamente mesmo benefício para exatamente a mesma localidade e beneficiário. reduza a similaridade se houver diferenças, mesmo que sutis, entre os textos.
- Não utilize a palavra "plágio" em sua resposta, se necessário expressar tal sentido, utilize a palavra "similaridade".

Utilizando linguagem dissertativa explicativa com os títulos e subtítulos necessários para facilitar a leitura, utilizando negrito e itálico quando necessário, formate a resposta em markdown conforme abaixo:

### **Análise de Similaridade Legislativa**
**Os textos pedem o mesmo benefício para a mesma localidade?** **[Sim / Não]**

Similaridade: [[ XX% ]]

**Detalhamento da Análise:**

* **Benefício Solicitado**: [Descreva o benefício ou ação solicitada em cada texto. Compare se ambos os textos estão solicitando exatamente a mesma ação ou benefício, ou se há diferenças, mesmo que sutis, na natureza do pedido.]
* **Localidade**: [Identifique a localidade específica mencionada em cada texto (bairro, rua, região). Compare se ambos os textos estão focando na mesma localidade ou se há divergências geográficas que possam impactar a similaridade.]
* **Beneficiários**: [Determine quem é o beneficiário do pedido em cada texto. Compare se ambos os textos estão direcionando o benefício para o mesmo grupo ou indivíduo, ou se há diferenças no público-alvo que possam reduzir a similaridade.]
* **Justificativa**: [Analise a justificativa ou motivo apresentado em cada texto para a solicitação. Compare se ambos os textos apresentam razões semelhantes ou se há diferenças que possam influenciar a avaliação da similaridade.]

---<ORIGINAL>{original}</ORIGINAL>

---<ANALISADO>{analisado}</ANALISADO>
"""

        return prompt2

        prompt1 = f"""
Assuma a personalidade de um especialista em produção de textos legislativos em uma câmara municipal brasileira com experiência em redação de documentos oficiais.
Sua tarefa é avaliar a similaridade de dois textos e identificar se eles tratam do mesmo assunto e pedem o mesmo benefício para a mesma localidade específica.
Os textos tratam de requerimentos legislativos, que são pedidos formais feitos por vereadores de uma mesma cidade para atender demandas da população ou seja, localidades específicas dentro do município.

Para tal tarefa, compare o conteúdo de <ORIGINAL></ORIGINAL> com o conteúdo de <ANALISADO></ANALISADO>.
Para citar estes dois conteúdos, nomeie eles respectivamente da seguinte maneira: "{o_epigrafe}" e "{a_epigrafe}".

Remova de sua análise os autores pois são irrelevantes para a comparação requerida.
O importante é o que está sendo pedido, quem será o beneficiário do pedido e para qual localidade dentro no município está sendo feito tal pedido.

Escreva de forma dissertativa explicativa utilizando o mínimo de palavras ou frases destas instruções, sem considerações adicionais ou mesmo conclusões extras. Neste contexto responda:
- Os textos estão pedindo o mesmo benefício para a mesma localidade? Responda objetivamente com "Sim" ou "Não" dastacando em negrito está pergunta e resposta.

- Evite ao máximo utilizar palavras ou frases destas instruções.
- Calcule a semelhança percentual entre os documentos desconsiderando autores, focando na solicitação, no problema apontado, no beneficiário e na localidade, qual semelhança percentual entre <ORIGINAL></ORIGINAL> e <ANALISADO></ANALISADO>? Coloque o resultado em percentual com uma marcação de colchetes, exemplo: "[[ 100% ]]".
- Eleve a similaridade a um valor máximo se os textos estiverem pedindo exatamente mesmo benefício para exatamente a mesma localidade e beneficiário. reduza a similaridade se houver diferenças, mesmo que sutis, entre os textos.
- Não utilize a palavra "plágio" em sua resposta, se necessário expressar tal sentido, utilize a palavra "similaridade".

Utilizando linguagem dissertativa explicativa com os títulos e subtítulos necessários para facilitar a leitura, utilizando negrito e itálico quando necessário, formate a resposta em markdown conforme abaixo:

### **Análise de Similaridade Legislativa**
**Os textos pedem o mesmo benefício para a mesma localidade?** **[Sim / Não]**

Similaridade: [[ XX% ]]

**Detalhamento da Análise:**

[Escreva detalhadamente "O QUÊ", "ONDE" e "PARA QUEM", "POR QUE" nos dois textos. Explique se eles coincidem ou onde divergem.]

---<ORIGINAL>{original}</ORIGINAL>

---<ANALISADO>{analisado}</ANALISADO>
"""

        return prompt1

    def extract_text_from_similaridade(self, similaridade):
        mat1 = similaridade.materia_1
        mat2 = similaridade.materia_2

        doc1 = pymupdf.open(mat1.texto_original.original_path)
        text1 = self._extract_pdf_text(doc1)
        text1 = clean_text(text1)

        doc2 = pymupdf.open(mat2.texto_original.original_path)
        text2 = self._extract_pdf_text(doc2)
        text2 = clean_text(text2)

        return text1, text2

    def run(self, similaridade, *args, **kwargs):
        # não presuma semelhança com run da classe acima
        _logger = kwargs.get("logger", logger)
        _save = kwargs.get("save", True)

        text1, text2 = self.extract_text_from_similaridade(similaridade)
        mat1 = similaridade.materia_1
        mat2 = similaridade.materia_2

        prompt = self.make_prompt(
            text1, text2, mat1.epigrafe_short, mat2.epigrafe_short
        )

        answer = self.generate_content(prompt, ascending=False)

        similaridade.analise = answer.text
        similaridade.ia_name = self.ia_model_name
        similaridade.data_analise = timezone.localtime()

        try:
            similaridade_value = similaridade.analise.split("[[ ")[1].split("%")[0]
            similaridade.similaridade = int(similaridade_value)
        except Exception as e:
            _logger.error(e)
            similaridade.similaridade = 0
        if _save:
            similaridade.save()
        return similaridade

    def batch_run(self, analises, logger=logger):

        quota = self.retrieve_quota_if_available(ascending=False)

        get_threads = quota.get_threads
        batch_size = quota.batch_size

        execs = []
        for i in range(get_threads):
            execs.append(
                {
                    "inline_analises": [],
                    "inline_requests": [],
                    "analises": [],
                    "display_name": f"batch_analise_similaridade_entre_materias_thread_{i}_{int(time.time())}",
                    "job_name": None,
                    "finished": False,
                    "state_job": None,
                    "inline_responses": [],
                }
            )

        analises = list(
            analises[0 : batch_size * get_threads]
        )  # limita para evitar excesso de requisições

        # distribui as análises entre os threads
        for i, analise in enumerate(analises):
            execs[i % get_threads]["analises"].append(analise)

        for exec in execs:
            analises = exec["analises"]

            for analise in analises:
                inline_analises = exec["inline_analises"]
                inline_requests = exec["inline_requests"]

                text1, text2 = self.extract_text_from_similaridade(analise)
                mat1 = analise.materia_1
                mat2 = analise.materia_2

                prompt = self.make_prompt(
                    text1, text2, mat1.epigrafe_short, mat2.epigrafe_short
                )
                inline_analises.append(analise)
                inline_requests.append(
                    {
                        "config": dict(
                            # temperature=self.temperature,
                            # top_p=self.top_p,
                            # top_k=self.top_k,
                            response_mime_type=self.response_mime_type,
                        ),
                        "contents": [{"parts": [{"text": prompt}], "role": "user"}],
                    }
                )

            display_name = exec["display_name"]
            inline_analises = exec["inline_analises"]
            inline_requests = exec["inline_requests"]

            inline_batch_job = self.client.batches.create(
                model=self.ia_model_name,
                src=inline_requests,
                config={"display_name": display_name},
            )
            exec["job_name"] = inline_batch_job.name

        def process_exec(exec):
            job_name = exec["job_name"]
            inline_analises = exec["inline_analises"]

            if exec["state_job"] != "JOB_STATE_SUCCEEDED":
                logger.error(
                    f"Batch job {job_name} did not succeed. State: {exec['state_job']}"
                )
                return

            for i, text in enumerate(exec["inline_responses"]):

                if not text:
                    continue

                quota.create_log()

                similaridade = inline_analises[i]
                similaridade.analise = text
                similaridade.ia_name = self.ia_model_name
                similaridade.data_analise = timezone.localtime()

                try:
                    similaridade_value = (
                        similaridade.analise.split("[[")[1].split("%")[0].strip()
                    )
                    similaridade.similaridade = int(similaridade_value)
                except Exception as e:
                    logger.error(e)
                    similaridade.similaridade = 0
                similaridade.save()

        while True:
            all_finished = True
            for exec in execs:
                if exec["finished"]:
                    continue
                job_name = exec["job_name"]
                batch_job_inline = self.client.batches.get(name=job_name)
                if batch_job_inline.state.name not in (
                    "JOB_STATE_SUCCEEDED",
                    "JOB_STATE_FAILED",
                    "JOB_STATE_CANCELLED",
                    "JOB_STATE_EXPIRED",
                ):
                    all_finished = False
                    logger.info(
                        f"Batch job {job_name}. Current state: {batch_job_inline.state.name}"
                    )
                else:
                    exec["finished"] = True
                    exec["state_job"] = batch_job_inline.state.name
                    if batch_job_inline.state.name == "JOB_STATE_SUCCEEDED":
                        exec["inline_responses"] = [
                            resp.response.text
                            for resp in batch_job_inline.dest.inlined_responses
                            if resp.response
                        ]

                    process_exec(exec)

            if all_finished:
                break
            # print(f"Some jobs not finished. Waiting 30 seconds...")
            time.sleep(60)
            # print(f"Job not finished. Current state: {batch_job_inline.state.name}. Waiting 30 seconds...")
