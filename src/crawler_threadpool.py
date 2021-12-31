import os
import pickle
from shutil import copyfile
import threading
from typing import List
from crawler import VideoCrawler
from util.util import dump_videos

from video import Video

class AtomicInteger():
    def __init__(self, value=0):
        self._value = int(value)
        self._lock = threading.Lock()
        
    def inc(self, d=1):
        with self._lock:
            self._value += int(d)
            return self._value

    def dec(self, d=1):
        return self.inc(-d)    

    @property
    def value(self):
        with self._lock:
            return self._value

    @value.setter
    def value(self, v):
        with self._lock:
            self._value = int(v)
            return self._value

class CrawlerThreadpool():
    def __init__(self, videos: List[Video], num_threads = 4, start_index = 0, end_index = 0, crawler_options: dict = {}, output_file = "dump.file"):
        self.crawler_options = crawler_options

        self.threads = []
        self.count = AtomicInteger(start_index)
        self.completed_count = AtomicInteger(0)  ##temp
        self.end_index = end_index

        self.videos = videos
        self.completed_videos = []
        self.missing_videos = []

        self.num_threads = num_threads
        self.file_save_lock = threading.Lock()

        self.output_file = output_file

    def run(self):
        for i in range(0, self.num_threads):
            thread = CrawlerThread(self, self.crawler_options)
            thread.start()
            self.threads.append(thread)

        for i in range(0, self.num_threads):
            self.threads[i].join()

class CrawlerThread(threading.Thread):
    def __init__(self, parent: CrawlerThreadpool, crawler_options: dict):
        self.crawler = VideoCrawler(**crawler_options)
        self.parent = parent
        threading.Thread.__init__(self)

    def get_existing_info(self, query_video):
        info = None
        for video in self.parent.videos:
            ## Check if videos have same base query and video has info
            if(video.query.title.strip() == query_video.query.title.strip()):
                if(hasattr(video, "info")):
                    info = video.info
                    break
        
        return info
    
    def run(self):
        while(self.parent.completed_count.value < 200):
            i = self.parent.count.inc() - 1
            print(i)

            if hasattr(self.parent.videos[i], "info"):
                continue

            try:
                video = self.parent.videos[i]

                ## Check if video has already been queried
                info = self.get_existing_info(video)
                if(info is None): ## otherwise query through crawler
                    info = self.crawler.get_video(video, index = i)
                    self.parent.completed_count.inc()
                video.info = info

                print(video.info)

                self.parent.completed_videos.append(video)
                print(video.query.title)

                with self.parent.file_save_lock:
                    dump_videos(self.parent.videos, self.parent.output_file)
                #print("{}\n    Name:\t\t{}\n    Description:\t{}".format(videos[i].title, entity["result"]["name"], entity["result"]["description"]))
                #except VideoNotFoundException as ex:
            except Exception as ex:
                if("Message: no such element: Unable to locate element: {\"method\":\"name\",\"selector\":\"q\"}" in str(ex)):
                    print(self.crawler.proxy_manager.proxy)
                print(ex)
                print("Failed {} (index: {})".format(self.parent.videos[i].title, i))
                self.parent.missing_videos.append(self.parent.videos[i])