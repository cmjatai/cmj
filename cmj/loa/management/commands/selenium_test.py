import datetime
import logging
from time import sleep

from django.core.management.base import BaseCommand
from django.db.models import Q
from jupyterlab_server import slugify
from selenium import webdriver
from selenium.webdriver.common.by import By

from cmj.settings.medias import MEDIA_PROTECTED_ROOT
from cmj.sigad.models import Classe
from cmj.utils import Manutencao
from sapl.materia.models import MateriaLegislativa


class Command(BaseCommand):

    logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        m = Manutencao()
        # m.desativa_auto_now()
        m.desativa_signals()

        screenshots = MEDIA_PROTECTED_ROOT.child("screenshots")

        # cria subpasta em screenshots com o nome da data atual em formato 2026-06-12

        screenshot_folder = screenshots.child(
            datetime.datetime.now().strftime("%Y-%m-%d")
        )

        try:
            screenshot_folder.mkdir()
        except Exception as e:
            print("pasta de screenshots já existe")

        options = webdriver.ChromeOptions()
        options.page_load_strategy = "normal"  # eager, normal, none
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1280,2275")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            },
        )
        driver.implicitly_wait(30)

        url_domain = "https://www.jatai.go.leg.br"
        # driver.maximize_window()

        execs = {
            "classes": True,
            "materias": True,
        }

        urls = []
        classes_publicas_pntp = Classe.objects.qs_pntp()
        for classe in classes_publicas_pntp:
            if not execs["classes"]:
                continue

            if not classe.url_redirect:
                urls.append(f"{url_domain}/{classe.absolute_slug}")
                continue

            if classe.url_redirect == "__":
                continue

            if classe.url_redirect.startswith("http"):
                urls.append(classe.url_redirect)
            else:
                urls.append(f"{url_domain}{classe.url_redirect}")

        for materia in MateriaLegislativa.objects.filter(
            Q(em_tramitacao=True)
            | Q(
                data_apresentacao__gte=datetime.datetime.now()
                - datetime.timedelta(days=60)
            ),
        ).order_by("-data_apresentacao"):
            if not execs["materias"]:
                continue

            url = f"{url_domain}/materia/{materia.id}"
            urls.append(url)

        urls = list(set(urls))
        urls.sort(reverse=True)

        popups_dispensados = False

        for url in urls:

            filename = slugify(url)

            try:
                print(f"acessando {url}")
                driver.get(url)
                sleep(5 if "www.jatai.go.leg.br" in url else 10)
            except Exception as e:
                print(f"erro ao acessar {url}: {e}")
                continue

            if "www.jatai.go.leg.br" in url and not popups_dispensados:
                try:
                    element = driver.find_element(By.ID, "btn-lgpd-ciente")
                    element.click()
                    sleep(1)
                except Exception as e:
                    print("popup de LGPD não encontrado")

                # procura .container-popup .btn-close e se encontrar clica para fechar o popup
                try:
                    element = driver.find_element(
                        By.CSS_SELECTOR, ".container-popup .btn-close"
                    )
                    element.click()
                    sleep(1)
                except Exception as e:
                    print("popup não encontrado")

                popups_dispensados = True

            try:
                driver.save_screenshot(screenshot_folder.child(f"{filename}.png"))
            except Exception as e:
                print(f"erro ao salvar screenshot de {url}: {e}")

        sleep(2)
        driver.quit()

        print("fim")
