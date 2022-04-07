from random import random, randrange
import re
import os
import threading
from time import sleep
from seleniumwire import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.remote.webelement import WebElement


class ProxyManager:
    class MeasuredProxy:
        def __init__(self, addr):
            self.addr = addr
            self.count = 0

    def __init__(self, file="config/proxies.txt"):
        self.count_lock = threading.Lock()

        def get_proxies(file):
            f = open(file, "r")
            regex = r"(.+:\d+):(.+):(.+)"
            proxies = []
            for line in f:
                if line.startswith("//"):
                    continue
                result = re.search(regex, line).groups()
                proxies.append(
                    "{user}:{password}@{addr}".format(
                        user=result[1], password=result[2], addr=result[0]
                    )
                )
            return proxies

        self.proxies = [
            ProxyManager.MeasuredProxy(proxy) for proxy in get_proxies(file)
        ]

    @property
    def proxy(self):
        with self.count_lock:
            p = min(self.proxies, key=lambda x: x.count)
            p.count += 1

        return p.addr


class Bot:
    def __init__(self, proxy, headless=True, show_images=False, index=0):
        seleniumwire_options = {
            "proxy": {
                "http": "http://{}".format(proxy),
                "https": "https://{}".format(proxy),
            }
        }

        os.environ["DBUS_SESSION_BUS_ADDRESS"] = "/dev/null"

        chrome_options = Options()
        chrome_profile = os.path.join(
            os.path.abspath(os.getcwd()), "chrome-dirs/p{}".format(index)
        )

        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_argument("user-data-dir=" + chrome_profile)
        chrome_options.add_argument("profile-directory=Profile 1")
        chrome_options.add_argument("--window-size=1920x1080")
        if headless:
            chrome_options.add_argument("--headless")

        if not show_images:
            chrome_prefs = {}
            chrome_options.experimental_options["prefs"] = chrome_prefs
            chrome_prefs["profile.default_content_settings"] = {"images": 2}
            chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}

        self.driver = webdriver.Chrome(
            options=chrome_options,
            seleniumwire_options=seleniumwire_options,
            service_args=[
                "--verbose",
                "--log-path=" + os.path.abspath(os.path.join(os.getcwd(), "log.log")),
            ],
        )
        self.wait_for_document()

    def __del__(self):
        self.driver.close()

    def exec_script(self, file, *args):
        f = open(file, "r")
        return self.driver.execute_script(f.read(), *args)

    def wait_for_document(self):
        WebDriverWait(self.driver, 20).until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )

    def click_element(self, element, attempts=5):
        sleep(0.15 + random() * 0.05)
        count = 0
        while count < attempts:
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda driver: expected_conditions.element_to_be_clickable(element)
                )
                element.click()
                sleep(0.15 + random() * 0.05)
                return
            except WebDriverException as e:
                if "is not clickable at point" in str(e) and count + 1 < attempts:
                    print("Retrying clicking button...")
                    count += 1
                else:
                    raise e

            sleep(1)

    def wait_for_element(self, element_lambda) -> WebElement:
        WebDriverWait(self.driver, 20).until(
            lambda driver: element_lambda()
            and expected_conditions.element_to_be_clickable(element_lambda())
        )
        return element_lambda()
