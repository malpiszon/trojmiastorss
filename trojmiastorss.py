#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
import dateparser

rssLink = 'https://rss.malpiszon.net/trojmiasto.pl/'
url = 'https://www.trojmiasto.pl/wiadomosci/'
skippedCategories = ['sport']
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
            author = 'Trojmiasto.pl',
            comments = url + '#opinions-wrap',
            categories = category,
            guid = Guid(art.find('a').get('href')),
            pubDate = dateparser.parse(art.find('span', class_='op-list').text.strip().splitlines()[0].strip(), languages=['pl'])
        )
        arts.append(item)

favicon = Image(
    url = 'https://static1.s-trojmiasto.pl/_img/favicon/favicon.ico',
    title = 'Trojmiasto.pl favicon',
    link = 'https://trojmiasto.pl'
)
feed = Feed(
    title = 'Trójmiasto.pl',
    link = rssLink,
    description = 'Wiadomości Trójmiasto.pl',
    language = 'pl-PL',
    image = favicon,
    lastBuildDate = datetime.datetime.now(),
    items = arts
)

print(feed.rss())

