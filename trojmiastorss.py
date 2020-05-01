#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
import dateparser

rssLink = 'tyrion.kw/rss'
urls=['https://www.trojmiasto.pl/wiadomosci/', 'https://dom.trojmiasto.pl/archiwum/aktualnosci/']
arts = []

for url in urls:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    for art in soup.find_all('li', class_='arch-item'):
        item = Item(
            title = art.find('a', class_='color04').text.strip(),
            link = art.find('a').get('href'),
            description = art.find('div', class_='lead').text.strip(),
            author = 'Trojmiasto.pl',
            guid = Guid(art.find('a').get('href')),
            pubDate = dateparser.parse(art.find('span', class_='op-list').text.strip().splitlines()[0].strip(), languages=['pl'])
        )
        arts.append(item)

feed = Feed(
    title = 'Trójmiasto.pl',
    link = rssLink,
    description = 'Wiadomości Trójmiasto.pl',
    language = 'pl-PL',
    lastBuildDate = datetime.datetime.now(),
    items = arts
)

print(feed.rss())

