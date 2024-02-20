#!/usr/bin/env python

from twitter.search import Search
from twitter.scraper import Scraper
from twitter.util import find_key

from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

from downloader import Downloader, read_cookie

# configs
cookie_file = "cookie.json"
username = "XDevelopers"
download_path = "download/"
# How many days of posts do you want to query every step?
# increase: faster iteration
# decrease: may not be able to get every post (could be a nonexistant problem)
step = 30


Path(download_path).mkdir(parents=True, exist_ok=True)

cookie = read_cookie(cookie_file)
search = Search(cookies=cookie)
scraper = Scraper(cookies=cookie)
downloader = Downloader(cookies=cookie)

today = datetime.now()
date_since = today - timedelta(days=step)
date_until = today

while True:
    date_since = date_since - timedelta(days=step)
    date_until = date_until - timedelta(days=step)
    date_since_str = date_since.strftime("%Y-%m-%d")
    date_until_str = date_until.strftime("%Y-%m-%d")
    query_str = f"from:{username} since:{date_since_str} until:{date_until_str}"

    print(f"Processing {date_since_str} - {date_until_str}")

    search_result = search.run(queries=[{"category": "Photos", "query": query_str}])[0]
    posts = find_key(search_result, "tweet_results")
    post_ids = filter(None, [post["result"].get("rest_id") for post in posts])

    downloader.download(post_ids, download_path)

    sleep(60)
