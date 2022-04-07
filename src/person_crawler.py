import threading
from time import sleep
from typing import List
from bot import ProxyManager, Bot
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from urllib.parse import quote


class CampingBotThreadpool:
    def __init__(
        self,
        num_threads=4,
        crawler_options: dict = {},
    ):
        ## Chrome driver options
        self.crawler_options = crawler_options

        ## Threading parameters
        self.threads = []
        self.num_threads = num_threads

    def run(self):
        for i in range(0, self.num_threads):
            thread = CampingBotThread(self, self.crawler_options, i)
            thread.start()
            self.threads.append(thread)

        for i in range(0, self.num_threads):
            self.threads[i].join()


class CampingBotThread(threading.Thread):
    def __init__(self, parent: CampingBotThreadpool, crawler_options: dict, index: int):
        self.bot = CampingBot(**crawler_options, index=index)
        self.parent = parent
        threading.Thread.__init__(self)

    def run(self):
        self.bot.stall()
        self.bot.book_site()

        self.bot.driver.close()


class CampingBot(Bot):
    def __init__(self, headless=True, show_images=False, index=0):
        self.__headless = headless
        self.__show_images = show_images
        self.proxy_manager = ProxyManager()
        self.index = index
        self.rotate_proxy()

    def rotate_proxy(self):
        if hasattr(self, "driver"):
            super().__del__()
        super().__init__(
            self.proxy_manager.proxy, self.__headless, self.__show_images, self.index
        )

    def stall(self):
        self.driver.get("https://camping.bcparks.ca/")
        sleep(200)

    def book_site(self):
        pass
