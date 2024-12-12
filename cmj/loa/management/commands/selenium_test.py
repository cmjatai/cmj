
from time import sleep
import logging

from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from cmj.utils import Manutencao


class Command(BaseCommand):

    logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        #parser.add_argument('--deep', action='store_true', default=False)
        #parser.add_argument('--onlychilds', action='store_true', default=False)
        #parser.add_argument('--outfile', action='store_true', default=False)
        ##parser.add_argument('--force', action='store_true', default=False)
        #parser.add_argument('--timeexec', type=int, default=80000)
        pass

    def handle(self, *args, **options):
        m = Manutencao()
        # m.desativa_auto_now()
        m.desativa_signals()

        options = webdriver.ChromeOptions()
        options.page_load_strategy = 'eager'

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(30)

        driver.get("https://www.jatai.go.leg.br/online/")
        driver.maximize_window()
        element = driver.find_element(By.ID, 'btn-lgpd-ciente')
        element.click()
        sleep(1)

        element = driver.find_element(
            By.CLASS_NAME, 'sessao-plenaria-item-list')
        element.click()
        sleep(1)

        element = driver.find_element(By.XPATH,
                                      "//a[contains(@class, 'link-file-21239') and not(contains(@class,'d-none'))]")

        element.click()
        sleep(1)

        sleep(30)
        driver.quit()

        print('fim')
