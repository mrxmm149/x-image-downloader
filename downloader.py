#!/usr/bin/env python

from datetime import datetime
from json import JSONDecodeError, loads
from os.path import isfile, join
from pathlib import Path
from urllib.request import urlretrieve

from dateutil import tz
from twitter.scraper import Scraper
from twitter.util import find_key

from threading import Thread, Lock

# config
ITERATION_SIZE = 32  # download in parallel
LOCALTIME = True


class Downloader:
    __downloaded_urls = set()
    __lock = Lock()
    __threads = []

    def __init__(self, cookies):
        self.scraper = Scraper(cookies=cookies)

    def download(self, post_ids: list[int] | set[int], path: str) -> None:
        sorted_ids = sorted(set(post_ids))
        for ii in range(0, len(sorted_ids), ITERATION_SIZE):
            tweets = self.scraper.tweets_by_ids(sorted_ids[ii : ii + ITERATION_SIZE])
            self.__download_chunk(tweets, path)

    def __download_chunk(self, tweets, path: str) -> None:
        results = find_key(tweets, "result")
        for result in results:
            t = Thread(target=self.__download_post, args=(result, path))
            t.start()
            self.__threads.append(t)

        for t in self.__threads:
            t.join()

        self.__threads = []

    def __download_post(self, result, download_path: str) -> None:
        typename = result.get("__typename", "")
        if typename == "Tweet":
            post = result
        elif typename == "TweetWithVisibilityResults":
            post = result["tweet"]
        else:
            return

        post_id = post.get("rest_id")
        if post_id is None:
            print("[error] Failed to get post id")
            return

        try:
            self.__download_media(post, download_path)
        except Exception as e:
            print(f"[error] Failed to download media in post {post_id}: {e}")
            with open("failed.txt", "a") as f:
                f.write(f"{post_id}\n")

    def __download_media(self, post, path: str) -> None:
        urls = find_key(find_key(post, "variants"), "url")  # video urls
        if len(urls) == 0:
            urls = find_key(post["legacy"], "media_url_https")  # photo urls
            # urls = [url for url in urls if "_video_thumb" not in url]
        urls = self.__dedup_list(urls)

        author_name = find_key(post["core"], "screen_name")[0]
        path = join(path, author_name)
        Path(path).mkdir(parents=True, exist_ok=True)

        created_at = self.__get_creation_time(post)
        post_id = post.get("rest_id")

        for ii, url in enumerate(urls, start=1):
            ext = Path(url).suffix
            full_path = join(path, f"{created_at}_twt_{post_id}_{ii:02}{ext}")
            self.__download_url(url, full_path)

        print(f"Downloaded {len(urls)} files from post {post_id}")

    def __dedup_list(self, li: list) -> list:
        return list(dict.fromkeys(li))  # use dict to preserve order

    def __get_creation_time(self, post) -> str:
        in_fmt = "%a %b %d %H:%M:%S %z %Y"
        out_fmt = "%Y%m%d_%H%M%S"

        t = datetime.strptime(find_key(post["legacy"], "created_at")[0], in_fmt)
        if LOCALTIME:
            t = t.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
        return t.strftime(out_fmt)

    def __download_url(self, url: str, full_path: str) -> None:
        with self.__lock:
            if url in self.__downloaded_urls:
                return
            self.__downloaded_urls.add(url)
        isfile(full_path) or urlretrieve(url, full_path)


def read_cookie(cookie_file: str) -> None:
    try:
        with open(cookie_file) as f:
            return loads(f.read())
    except OSError as e:
        print(f"[error] Failed to open file {cookie_file}: {e}")
        raise e

    except JSONDecodeError as e:
        print(f"[error] cookie is not in a valid json format: {e}")
        raise e

    except Exception as e:
        print(f"[error] unknown error: {e}")
        raise e
