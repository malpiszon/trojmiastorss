#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
import dateparser

rssLink = 'https://rss.malpiszon.net/trojmiasto.pl/'
url = 'https://www.trojmiasto.pl/wiadomosci/'
skippedCategories = ['sport', 'deluxe']
arts = []

response = requests.get(url)
soup = BeautifulSoup(response.text, 'lxml')

for art in soup.find_all('li', class_='arch-item'):
    category = art.find('div', class_='category').find('a').text.strip()
    if category.lower() not in skippedCategories:
        url = art.find('a').get('href')
        item = Item(
            title = art.find('a', class_='color04').text.strip(),
            link = url,
            description = art.find('div', class_='lead').text.strip(),
            author = 'Trojmiasto.pl (' + category + ')',
            creator = 'by Trojmiasto.pl (' + category + ')',
            comments = url + '#opinions-wrap',
            categories = [ category ],
            guid = Guid(art.find('a').get('href')),
            pubDate = dateparser.parse(art.find('span', class_='op-list').text.strip().splitlines()[0].strip(), languages=['pl'])
        )
        arts.append(item)

feed = Feed(
    title = 'Trójmiasto.pl',
    link = rssLink,
    description = 'Kanał RSS dla Trójmiasto.pl',
    language = 'pl-PL',
    lastBuildDate = datetime.datetime.now(),
    items = arts
)

print(feed.rss())

