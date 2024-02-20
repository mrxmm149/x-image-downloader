#!/usr/bin/env python

from twitter.account import Account
from twitter.util import find_key

from downloader import Downloader, read_cookie

# configs
cookie_file = "cookie.json"
download_path = "download/"

cookie = read_cookie(cookie_file)
account = Account(cookies=cookie)
results = find_key(account.bookmarks(), "tweet_results")
tweets = [r["result"].get("tweet") or r["result"] for r in results]
Downloader(cookie).download([tweet["rest_id"] for tweet in tweets], download_path)
