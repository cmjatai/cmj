import datetime
import logging
import re

import requests
from asn1crypto import cms
from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.signals import post_save, pre_save
from django.utils import timezone
from django.utils.text import slugify

from cmj.celery import app
from cmj.sigad.models import Documento
from cmj.utils import DisableSignals
from cmj.videos.models import VideoParte
from sapl.materia.models import MateriaLegislativa

logger = (
    get_task_logger(__name__) if not settings.DEBUG else logging.getLogger(__name__)
)

socials_connects = {
    "telegram": dict(
        TOKEN=settings.TELEGRAM_CMJATAI_BOT_KEY,
        API_ID=settings.TELEGRAM_API_ID,
        API_HASH=settings.TELEGRAM_API_HASH,
        CHAT_ID=(
            settings.TELEGRAM_CHAT_ID
            if not settings.DEBUG
            else settings.TELEGRAM_CHAT_DEV_ID
        ),
        url_base=f"https://api.telegram.org/bot{settings.TELEGRAM_CMJATAI_BOT_KEY}/{{endpoint}}",
    )
}


@app.task(queue="cq_core", bind=True)
def task_send_rede_social(self, rede, app_label, model_name, pk):
    # print(args)
    # print(kwargs)
    # return

    if "www" not in settings.SITE_URL:
        return

    send_func = f"send_{rede}_{app_label}_{model_name}"

    # print(f'print, task_send_rede_social iniciou execução: {send_func}')
    logger.info(f"logger task_send_rede_social iniciou execução: {send_func}")

    gf = globals()
    if send_func in gf:
        return gf[send_func](pk)


def send_telegram_sigad_documento(pk):
    # print('send documento iniciou execução')
    logger.info("send documento iniciou execução")

    instance = Documento.objects.filter(pk=pk).first()
    if not instance:
        return

    if "banco-de-imagens" in instance.slug:
        return

    md = instance.metadata

    if not md:
        md = {}

    if "send" not in md:
        md["send"] = {}

    md["send"]["telegram"] = timezone.localtime()
    instance.metadata = md
    instance.save()

    descricao = instance.descricao or ""
    if descricao and descricao != instance.titulo:
        descricao = f"{chr(10)}{chr(10)}<i>{descricao}</i>"
    else:
        descricao = ""

    texto = instance.texto or ""
    tt = ""
    for t in texto.split(" "):
        if len(tt) < 200:
            tt += t + " "
        else:
            texto = tt.strip() + "..."
            break
    if texto:
        texto = f"""{chr(10)}{chr(10)}<pre>{texto}</pre>"""

    ct = ContentType.objects.get_by_natural_key("sigad", "documento")
    vp = VideoParte.objects.filter(content_type=ct, object_id=instance.id).first()
    live = ""
    if vp and "video" in instance.slug:
        link = f"{chr(10)}{chr(10)}https://youtu.be/{vp.video.vid}"
        if vp.video.json["snippet"]["liveBroadcastContent"] == "live":
            live = f"#AoVivo"
    else:
        link = f'{chr(10)}{chr(10)}<a href="{settings.SITE_URL}/{instance.slug}">Leia mais!</a>'

    text = f"""#{instance.classe.titulo} {live}
<b>{instance.titulo}</b>{descricao}{texto}{link}"""

    # <tg-spoiler>spoiler</tg-spoiler>
    # if settings.DEBUG:
    # print(text)
    logger.info(text)
    #    return

    url_base = socials_connects["telegram"]["url_base"]
    CHAT_ID = socials_connects["telegram"]["CHAT_ID"]

    try:
        r = requests.post(
            url_base.format(endpoint="sendMessage"),
            data={
                "parse_mode": "html",
                "chat_id": CHAT_ID,
                "text": text,
            },
        )
    except Exception as e:
        logger.error(e)


def send_telegram_materia_materialegislativa(pk):
    # print('send matéria iniciou execução')
    logger.info("send matéria iniciou execução")

    instance = MateriaLegislativa.objects.get(pk=pk)
    md = instance.metadata

    if not md:
        md = {}

    if "send" not in md:
        md["send"] = {}

    md["send"]["telegram"] = timezone.localtime()
    instance.metadata = md
    instance.save()

    autores_hash_tag = " ".join(
        map(
            lambda a: "#{}".format("".join(str(a.nome).split(" "))),
            instance.autores.all(),
        )
    )

    autores = "\n".join(map(lambda a: "<i>{}</i>".format(a), instance.autores.all()))

    text = f"""#{instance.tipo.sigla} #MatériaLegislativa
<b>{str(instance).upper()}</b>

<pre>{instance.ementa}</pre>

Autoria:
{autores}

{autores_hash_tag}
<a href="{settings.SITE_URL}/materia/{instance.id}">Acompanhe o Processo Legislativo desta Matéria clicando aqui.</a>
    """

    # <tg-spoiler>spoiler</tg-spoiler>
    # if settings.DEBUG:
    # print(text)
    logger.info(text)
    #    return

    url_base = socials_connects["telegram"]["url_base"]
    CHAT_ID = socials_connects["telegram"]["CHAT_ID"]

    try:
        r = requests.post(
            url_base.format(endpoint="sendMessage"),
            data={
                "parse_mode": "html",
                "chat_id": CHAT_ID,
                "text": text,
            },
        )
        with open(instance.texto_original.path, mode="rb") as fp:

            def custom_filename(item):
                arcname = "{}-{:03d}-{}-{}.{}".format(
                    item.ano,
                    item.numero,
                    slugify(item.tipo.sigla),
                    slugify(item.tipo.descricao),
                    item.texto_original.path.split(".")[-1],
                )
                return arcname

            r = requests.post(
                url_base.format(endpoint="sendDocument"),
                data={
                    "chat_id": CHAT_ID,
                    "caption": "Uma cópia na integra do original para você conferir!",
                },
                files={
                    "document": (
                        custom_filename(instance),
                        fp.read(),
                        "application/pdf",
                    )
                },
            )

    except Exception as e:
        logger.error(e)


@app.task(queue="cq_core", bind=True)
def signed_files_extraction(self, app_label, model_name, pk):

    if settings.DEBUG:
        logger.debug(
            f"START signed_files_extraction_post_save_signal {timezone.localtime()}"
        )

    task_signed_files_extraction_function(app_label, model_name, pk)
    if settings.DEBUG:
        logger.debug(
            f"END signed_files_extraction_post_save_signal {timezone.localtime()}"
        )


def task_signed_files_extraction_function(app_label, model_name, pk):
    def get_pdf_dictionary_bounds(pdfdata, position):
        """
        Encontra os limites << e >> do dicionário PDF que contém a posição informada.
        Lida com dicionários aninhados usando um contador de profundidade.
        """
        # 1. Busca para trás o início do dicionário (<<)
        start_pos = position
        depth = 1
        while start_pos > 0:
            start_pos = pdfdata.rfind(b"<<", 0, start_pos)
            if start_pos == -1:
                break
            # Como estamos indo de trás para frente, se acharmos >> primeiro,
            # significa que entramos em um sub-dicionário, ignoramos
            close_tags = pdfdata.count(b">>", start_pos, position)
            open_tags = pdfdata.count(b"<<", start_pos, position)
            if open_tags > close_tags:
                break

        # 2. Busca para frente o fim do dicionário (>>)
        end_pos = position
        depth = 1
        while end_pos < len(pdfdata):
            end_pos = pdfdata.find(b">>", end_pos + 1)
            if end_pos == -1:
                end_pos = len(pdfdata)
                break

            close_tags = pdfdata.count(b">>", position, end_pos + 2)
            open_tags = pdfdata.count(b"<<", position, end_pos + 2)
            if close_tags > open_tags:
                end_pos += 2  # Inclui os caracteres >>
                break

        return max(0, start_pos), min(len(pdfdata), end_pos)

    def run_signed_name_and_date_extract(file_obj):
        signs = {}

        if hasattr(file_obj, "read"):
            file_obj.seek(0)
            pdfdata = file_obj.read()
        else:
            with open(file_obj, "rb") as f:
                pdfdata = f.read()

        n = -1
        while True:
            n = pdfdata.find(b"/ByteRange", n + 1)
            if n == -1:
                break

            start = pdfdata.find(b"[", n)
            stop = pdfdata.find(b"]", start)
            if start == -1 or stop == -1:
                continue

            try:
                br = [int(i, 10) for i in pdfdata[start + 1 : stop].split()]
                if len(br) != 4:
                    continue
            except ValueError:
                continue

            hex_start = br[0] + br[1]
            hex_end = br[2]

            contents_area = pdfdata[hex_start:hex_end]
            c_start = contents_area.find(b"<")
            c_end = contents_area.rfind(b">")

            if c_start == -1 or c_end == -1:
                continue

            hex_str = contents_area[c_start + 1 : c_end]
            try:
                bcontents = bytes.fromhex(hex_str.decode("ascii", errors="ignore"))
            except ValueError:
                continue

            nome = "Nome do assinante não localizado."
            oname = ""
            fd = None

            try:
                info = cms.ContentInfo.load(bcontents)
                signed_data = info["content"]

                oun_old = []
                for cert in signed_data["certificates"]:
                    subject = cert.native["tbs_certificate"]["subject"]
                    issuer = cert.native["tbs_certificate"]["issuer"]
                    oname = issuer.get("organization_name", "")

                    if oname in ("Gov-Br", "1Doc"):
                        nome = subject["common_name"].split(":")[0]
                        continue

                    oun = subject.get("organizational_unit_name")

                    if isinstance(oun, str):
                        continue

                    if oun and len(oun) > len(oun_old):
                        oun_old = oun
                        nome = subject.get("common_name", "").split(":")[0]

                    if oun and isinstance(oun, list) and len(oun) == 4:
                        oname += " - " + oun[3]
                        break
            except Exception:
                pass

            # =================================================================
            # NOVO: ISOLAMENTO PERFEITO DO DICIONÁRIO DA ASSINATURA
            # =================================================================
            dict_start, dict_end = get_pdf_dictionary_bounds(pdfdata, n)
            signature_dict = pdfdata[dict_start:dict_end]

            # Fallback do Nome restrito apenas a este dicionário exato
            if nome == "Nome do assinante não localizado.":
                name_match = re.search(rb"/Name\s*\((.*?)\)", signature_dict)
                if name_match:
                    try:
                        raw_name = name_match.group(1)
                        if raw_name.startswith(b"\xfe\xff"):
                            nome = raw_name.decode("utf-16-be", errors="ignore")
                        else:
                            nome = raw_name.decode("utf-8", errors="ignore")
                    except Exception:
                        pass

            # Resgate da Data restrito apenas a este dicionário exato
            date_match = re.search(rb"/M\s*\((D:[0-9+Z\'-]+)\)", signature_dict)
            if date_match:
                try:
                    data_str = date_match.group(1).decode("ascii", errors="ignore")
                    if "D:" in data_str:
                        if not data_str.endswith("Z"):
                            data_str = data_str.replace("Z", "+")
                        data_str = data_str.replace("'", "")
                        fd = datetime.datetime.strptime(data_str[2:], "%Y%m%d%H%M%S%z")
                except Exception:
                    pass

            if nome and nome not in signs:
                signs[nome] = [fd, oname]

        return list(signs.items())

    def signed_name_and_date_extract(file, isola_hom=True):

        try:
            signs = run_signed_name_and_date_extract(file)
        except Exception as e:
            return {}

        data_min = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

        try:
            signs = sorted(
                signs, key=lambda sign: (sign[0], sign[1][1], sign[1][0] or data_min)
            )
        except Exception as e:
            pass

        signs.reverse()

        signs_dict = {}

        for s in signs:
            if (
                s[0] not in signs_dict
                or "ICP" in s[1][1]
                and "ICP" not in signs_dict[s[0]][1]
            ):
                signs_dict[s[0]] = s[1]

        signs = sorted(
            signs_dict.items(), key=lambda sign: (sign[0], sign[1][1], sign[1][0])
        )

        sr = []

        for s in signs:
            tt = s[0].title().split(" ")
            for idx, t in enumerate(tt):
                if t in ("Dos", "De", "Da", "Do", "Das", "E"):
                    tt[idx] = t.lower()
            sr.append((" ".join(tt), s[1]))

        signs = sr

        meta_signs = {"signs": [], "hom": []}

        for s in signs:
            cn = settings.CERT_PRIVATE_KEY_NAME
            meta_signs["hom" if s[0] == cn and isola_hom else "signs"].append(s)
        return meta_signs

    model = apps.get_model(app_label, model_name)

    try:
        instance = model.objects.get(pk=pk)
    except:
        return

    isola_hom = model_name in (
        "MateriaLegislativa",
        "DocumentoAcessorio",
    )

    if not hasattr(instance, "FIELDFILE_NAME") or not hasattr(instance, "metadata"):
        return

    metadata = instance.metadata
    for fn in instance.FIELDFILE_NAME:  # fn -> field_name
        ff = getattr(instance, fn)  # ff -> file_field

        try:
            running_extraction = metadata["signs"][fn]["running_extraction"]
        except:
            continue
        else:
            if not running_extraction:
                continue

        if (
            metadata
            and "signs" in metadata
            and fn in metadata["signs"]
            and metadata["signs"][fn]
        ):
            metadata["signs"][fn] = {}

        if not ff:
            continue

        try:
            file = ff.file.file
            meta_signs = {}
            if not isinstance(ff.file, InMemoryUploadedFile):
                original_absolute_path = ff.original_path
                with open(original_absolute_path, "rb") as file:
                    meta_signs = signed_name_and_date_extract(file, isola_hom=isola_hom)
                    file.close()

                absolute_path = ff.path
                with open(absolute_path, "rb") as file:
                    sign_hom = signed_name_and_date_extract(file, isola_hom=isola_hom)
                    file.close()
                    meta_signs["hom"] = sign_hom["hom"]

            else:
                file.seek(0)
                meta_signs = signed_name_and_date_extract(file, isola_hom=isola_hom)

            if not meta_signs:
                continue

            if not metadata:
                metadata = {"signs": {}}

            if "signs" not in metadata:
                metadata["signs"] = {}

            metadata["signs"][fn] = meta_signs
        except Exception as e:
            metadata["signs"][fn] = {}
            logger.error(
                f"Erro ao extrair assinaturas de {instance._meta.concrete_model}: {instance.pk} - {instance}"
            )

    with DisableSignals([pre_save, post_save]):
        try:
            instance.metadata = metadata
            instance.save(update_fields=["metadata"])
        except:
            logger.error(f"Erro ao salvar {instance.pk} - {instance}")
