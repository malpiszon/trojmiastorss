#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
import dateparser

url='https://www.trojmiasto.pl/wiadomosci/'

response = requests.get(url)
soup = BeautifulSoup(response.text, "lxml")

arts = []

for art in soup.find_all("li", class_="arch-item"):
    item = Item(
        title = art.find("a", class_="color04").text.strip(),
        link = art.find("a").get("href"),
        description = art.find("div", class_="lead").text.strip(),
        author = "Trojmiasto.pl",
        guid = Guid(art.find("a").get("href")),
        pubDate = dateparser.parse(art.find("span", class_="op-list").text.strip().splitlines()[0].strip(), languages=['pl'])
    )
    arts.append(item)

feed = Feed(
    title = "Trójmiasto.pl",
    link = "tyrion.kw/rss",
    description = "RSS z Trójmiasto.pl",
    language = "pl-PL",
    lastBuildDate = datetime.datetime.now(),
    items = arts
)

print(feed.rss())

