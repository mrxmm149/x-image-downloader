#!/usr/bin/env python

from os.path import basename

from downloader import Downloader, read_cookie

# configs
list_file = "list.txt"
cookie_file = "cookie.json"
download_path = "download/"


def get_id(line: str) -> int:
    split_line = basename(line).split("_")
    if len(split_line) > 3:
        return int(split_line[3])
    else:
        return int(line)


# Option 1: Simple post id list
with open(list_file, "r") as f:
    post_ids = f.read().splitlines()

# Option 2: parse filename into post id
# with open(list_file, "r") as f:
#     post_ids = {get_id(x) for x in f.read().splitlines()}

Downloader(read_cookie(cookie_file)).download(post_ids, download_path)
