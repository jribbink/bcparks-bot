import threading
from time import sleep
from typing import List
from bot import ProxyManager, Bot
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
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

        ## Proxy manager
        self.proxy_manager = ProxyManager()

    def run(self):
        for i in range(0, self.num_threads):
            thread = CampingBotThread(self, self.crawler_options, i)
            thread.start()
            self.threads.append(thread)

        for i in range(0, self.num_threads):
            self.threads[i].join()


class CampingBotThread(threading.Thread):
    def __init__(self, parent: CampingBotThreadpool, crawler_options: dict, index: int):
        self.bot = CampingBot(parent.proxy_manager, **crawler_options, index=index)
        self.parent = parent
        threading.Thread.__init__(self)

    def run(self):
        self.bot.stall()
        self.bot.book_site()

        self.bot.driver.close()


class CampingBot(Bot):
    def __init__(self, proxy_manager, headless=True, show_images=False, index=0):
        self.__headless = headless
        self.__show_images = show_images
        self.proxy_manager = proxy_manager
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
        self.wait_for_document()

    def book_site(self):
        campground_name = "Wells Gray Provincial Park"
        arrival_date = "Jun 6"
        number_of_nights = "1"
        equiptment_name = "3 Tents"
        intermediate_link_text = "Clearwater Lake"
        site_number = "C32"

        park_select = self.driver.find_elements_by_css_selector("#park-autocomplete")
        if not park_select:
            sleep(5)
            self.book_site()
        self.click_element(park_select[0])

        desired_select = self.wait_for_element(
            lambda: self.exec_script("js/findText.js", campground_name)
        )
        self.click_element(desired_select)

        def pick_date(date: str):
            date = date.strip()
            month = date.split(" ")[0].upper()
            day = date.split(" ")[1]

            month_dropdown_picker = self.wait_for_element(
                lambda: self.driver.find_elements_by_css_selector(
                    "#monthDropdownPicker > span.mat-button-wrapper"
                )
            )[0]
            self.click_element(month_dropdown_picker)

            month_button = self.wait_for_element(
                lambda: self.exec_script("js/findText.js", month)
            )
            self.click_element(month_button)

            day_button = self.wait_for_element(
                lambda: self.exec_script(
                    "js/findText.js",
                    day,
                    self.driver.find_element_by_css_selector(
                        "#mat-datepicker-0 > div > mat-month-view > table > tbody"
                    ),
                )
            )
            self.click_element(day_button)

        arrive_button = self.driver.find_element_by_xpath(
            '//*[@id="mat-tab-content-0-0"]/div/div/fieldset/div[2]/mat-form-field[1]/div/div[1]'
        )
        self.click_element(arrive_button)

        pick_date(arrival_date)

        nights_field = self.driver.find_element_by_xpath('//*[@id="mat-input-3"]')
        nights_field.send_keys(Keys.BACKSPACE)
        nights_field.send_keys(number_of_nights)

        equiptment_field = self.driver.find_element_by_xpath(
            '//*[@id="mat-select-value-1"]/span'
        )
        self.click_element(equiptment_field)

        equiptment_button = self.wait_for_element(
            lambda: self.exec_script("js/findText.js", equiptment_name)
        )
        self.click_element(equiptment_button)

        search_button = self.driver.find_element_by_css_selector(
            "#actionSearch > span.mat-button-wrapper > div.button-contents.ng-star-inserted"
        )
        self.click_element(search_button)

        self.wait_for_document()

        if intermediate_link_text:
            intermediate_link = self.exec_script(
                "js/getIntermediateLink.js",
                self.wait_for_element(
                    lambda: self.exec_script("js/findText.js", intermediate_link_text)
                ),
            )
            self.click_element(intermediate_link)

        self.wait_for_document()

        site_button = self.exec_script(
            "js/getSiteButton.js",
            self.wait_for_element(
                lambda: self.exec_script(
                    "js/findText.js",
                    site_number,
                    self.wait_for_element(
                        lambda: self.driver.find_elements_by_css_selector(
                            "#map > div.leaflet-pane.leaflet-map-pane > div.leaflet-pane.leaflet-marker-pane.leaflet-zoom-hide"
                        )
                    )[0],
                )
            ),
        )
        self.click_element(site_button)

        reserve_button = self.wait_for_element(
            lambda: self.driver.find_elements_by_css_selector(
                "#addToStay > span.mat-button-wrapper"
            )
        )[0]
        self.click_element(reserve_button)

        ## HANDLE WHAT HAPPENS IF WE TOO EARLY?

        WebDriverWait(self.driver, 20).until(
            lambda driver: self.exec_script(
                "js/isTextPresent.js", "This is part of a Double Site"
            )
            or self.exec_script("js/isTextPresent.js", "Review Reservation Details")
        )

        if self.exec_script("js/isTextPresent.js", "This is part of a Double Site"):
            confirm_button = self.wait_for_element(
                lambda: self.driver.find_elements_by_css_selector(
                    "#confirmButton > span.mat-button-wrapper"
                )
            )[0]
            self.click_element(confirm_button)

        self.wait_for_document()

        sleep(200)
