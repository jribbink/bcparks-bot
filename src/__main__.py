import os
from person_crawler import CampingBotThreadpool

from util.io import request_input, request_int


def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    print("----------------------------------")
    print("|      BC Parks Booking Bot      |")
    print("| Created by Jordan Ribbink 2022 |")
    print("----------------------------------\n")


print_banner()

num_threads = request_int("How many threads would you like to launch? ")

threadpool = CampingBotThreadpool(
    num_threads=num_threads, crawler_options={"headless": False, "show_images": True}
)
threadpool.run()
